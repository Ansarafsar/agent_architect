"""
LangGraph workflow for Cerina Protocol Foundry.
Orchestrates multi-agent CBT protocol generation with safety checks.
"""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from backend.state.models import BlackboardState
from backend.state.checkpointer import get_checkpointer
from backend.agents import (
    DraftingAgent,
    SafetyGuardianAgent,
    ClinicalCriticAgent,
    RevisionAgent,
    SupervisorAgent
)
import logging

logger = logging.getLogger(__name__)


# Node names
class NodeNames:
    """Constants for node names in the graph."""
    DRAFT = "draft"
    SAFETY = "safety"
    CRITIC = "critic"
    REVISE = "revise"
    SUPERVISOR = "supervisor"
    HUMAN_REVIEW = "human_review"
    FINALIZE = "finalize"


def create_workflow_graph(checkpointer: PostgresSaver) -> StateGraph:
    """
    Create the LangGraph workflow for protocol generation.
    
    Args:
        checkpointer: PostgresSaver instance for state persistence
        
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building workflow graph...")
    
    # Initialize agents
    drafting_agent = DraftingAgent()
    safety_agent = SafetyGuardianAgent()
    critic_agent = ClinicalCriticAgent()
    revision_agent = RevisionAgent()
    supervisor_agent = SupervisorAgent()
    
    # Create graph
    workflow = StateGraph(BlackboardState)
    
    # ========================================
    # Define Node Functions
    # ========================================
    
    async def draft_node(state: BlackboardState) -> BlackboardState:
        """Create initial draft."""
        logger.info(f"[{NodeNames.DRAFT}] Creating initial draft...")
        return await drafting_agent.run(state)
    
    async def safety_node(state: BlackboardState) -> BlackboardState:
        """Run safety analysis."""
        logger.info(f"[{NodeNames.SAFETY}] Running safety analysis...")
        return await safety_agent.run(state)
    
    async def critic_node(state: BlackboardState) -> BlackboardState:
        """Run clinical quality review."""
        logger.info(f"[{NodeNames.CRITIC}] Running quality review...")
        return await critic_agent.run(state)
    
    async def revision_node(state: BlackboardState) -> BlackboardState:
        """Revise draft based on feedback."""
        logger.info(f"[{NodeNames.REVISE}] Revising draft...")
        return await revision_agent.run(state)
    
    async def supervisor_node(state: BlackboardState) -> BlackboardState:
        """Make routing decision."""
        logger.info(f"[{NodeNames.SUPERVISOR}] Making routing decision...")
        updated_state, next_step = await supervisor_agent.run(state)
        # Store next step in metadata for conditional routing
        updated_state.metadata["next_step"] = next_step
        return updated_state
    
    async def human_review_node(state: BlackboardState) -> BlackboardState:
        """Pause for human review."""
        logger.info(f"[{NodeNames.HUMAN_REVIEW}] Pausing for human review...")
        state.status = "halted"
        state.add_agent_message(
            agent="System",
            message="⏸️ Workflow paused for human review. Please review and approve/edit the draft.",
            event_type="halt"
        )
        return state
    
    async def finalize_node(state: BlackboardState) -> BlackboardState:
        """Finalize the protocol."""
        logger.info(f"[{NodeNames.FINALIZE}] Finalizing protocol...")
        state.status = "final"
        state.add_agent_message(
            agent="System",
            message="🎉 Protocol generation complete and approved!",
            event_type="success"
        )
        return state
    
    # ========================================
    # Add Nodes to Graph
    # ========================================
    
    workflow.add_node(NodeNames.DRAFT, draft_node)
    workflow.add_node(NodeNames.SAFETY, safety_node)
    workflow.add_node(NodeNames.CRITIC, critic_node)
    workflow.add_node(NodeNames.REVISE, revision_node)
    workflow.add_node(NodeNames.SUPERVISOR, supervisor_node)
    workflow.add_node(NodeNames.HUMAN_REVIEW, human_review_node)
    workflow.add_node(NodeNames.FINALIZE, finalize_node)
    
    # ========================================
    # Define Edges and Routing
    # ========================================
    
    # Set entry point
    workflow.set_entry_point(NodeNames.DRAFT)
    
    # Draft -> Safety (always)
    workflow.add_edge(NodeNames.DRAFT, NodeNames.SAFETY)
    
    # Safety -> Critic (always)
    workflow.add_edge(NodeNames.SAFETY, NodeNames.CRITIC)
    
    # Critic -> Supervisor (always)
    workflow.add_edge(NodeNames.CRITIC, NodeNames.SUPERVISOR)
    
    # Revision -> Safety (re-check after revision)
    workflow.add_edge(NodeNames.REVISE, NodeNames.SAFETY)
    
    # Supervisor -> Conditional routing based on decision
    def supervisor_router(state: BlackboardState) -> str:
        """Route based on supervisor's decision."""
        next_step = state.metadata.get("next_step", "finalize")
        logger.info(f"[ROUTER] Supervisor decided: {next_step}")
        
        if next_step == "revision":
            return NodeNames.REVISE
        elif next_step == "human_review":
            return NodeNames.HUMAN_REVIEW
        elif next_step == "finalize":
            return NodeNames.FINALIZE
        else:
            # Default to finalize
            return NodeNames.FINALIZE
    
    workflow.add_conditional_edges(
        NodeNames.SUPERVISOR,
        supervisor_router,
        {
            NodeNames.REVISE: NodeNames.REVISE,
            NodeNames.HUMAN_REVIEW: NodeNames.HUMAN_REVIEW,
            NodeNames.FINALIZE: NodeNames.FINALIZE
        }
    )
    
    # Human Review -> Finalize (after approval)
    workflow.add_edge(NodeNames.HUMAN_REVIEW, NodeNames.FINALIZE)
    
    # Finalize -> END
    workflow.add_edge(NodeNames.FINALIZE, END)
    
    # ========================================
    # Compile Graph
    # ========================================
    
    logger.info("Compiling workflow graph with checkpointer...")
    compiled = workflow.compile(checkpointer=checkpointer)
    
    logger.info("✅ Workflow graph compiled successfully!")
    
    return compiled


def get_workflow():
    """
    Get the compiled workflow graph with checkpointing enabled.
    
    Returns:
        Compiled workflow graph
    """
    checkpointer = get_checkpointer()
    saver = checkpointer.get_saver()
    return create_workflow_graph(saver)
