"""
Supervisor Agent - Orchestrates workflow and makes routing decisions.
"""
import os
from typing import Literal
from .base import BaseAgent
from backend.state.models import BlackboardState


# Configuration from environment
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
SAFETY_THRESHOLD = float(os.getenv("SAFETY_THRESHOLD", "0.5"))
EMPATHY_THRESHOLD = float(os.getenv("EMPATHY_THRESHOLD", "0.8"))


class SupervisorAgent(BaseAgent):
    """Agent responsible for workflow orchestration and routing."""
    
    def __init__(self):
        super().__init__(name="Supervisor")
        self.max_iterations = MAX_ITERATIONS
        self.safety_threshold = SAFETY_THRESHOLD
        self.empathy_threshold = EMPATHY_THRESHOLD
    
    def decide_next_step(self, state: BlackboardState) -> Literal[
        "safety", "critic", "revision", "human_review", "finalize", "halt"
    ]:
        """
        Determine the next step in the workflow based on current state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node to execute
        """
        self.log("Making routing decision...")
        
        # Check for critical safety issues first
        if state.safety_score < self.safety_threshold:
            high_risk_flags = sum(1 for f in state.safety_flags if f.risk_level == "high")
            
            if high_risk_flags > 0:
                self.log(f"🚨 CRITICAL SAFETY: Score={state.safety_score:.2f}, High-risk flags={high_risk_flags}")
                state.add_agent_message(
                    agent=self.name,
                    message=f"🚨 Halting for human review: Critical safety concerns detected",
                    event_type="warning"
                )
                return "human_review"
            else:
                self.log(f"⚠️ Safety below threshold, sending to revision")
                state.add_agent_message(
                    agent=self.name,
                    message=f"Safety score {state.safety_score:.2f} below threshold, routing to revision",
                    event_type="info"
                )
                return "revision"
        
        # Check iteration limit
        if state.iterations >= self.max_iterations:
            self.log(f"⏱️ Max iterations ({self.max_iterations}) reached")
            state.add_agent_message(
                agent=self.name,
                message=f"Maximum iterations ({self.max_iterations}) reached, requesting human review",
                event_type="warning"
            )
            return "human_review"
        
        # Check empathy/quality score
        if state.empathy_score < self.empathy_threshold:
            if state.iterations > 0:
                # Already tried revising, might need human input
                self.log(f"📊 Empathy still low after {state.iterations} iterations")
                state.add_agent_message(
                    agent=self.name,
                    message=f"Quality remains below threshold after {state.iterations} revisions",
                    event_type="info"
                )
                return "human_review"
            else:
                self.log(f"📊 Empathy score {state.empathy_score:.2f} below threshold, sending to revision")
                state.add_agent_message(
                    agent=self.name,
                    message=f"Empathy score {state.empathy_score:.2f} below threshold, routing to revision",
                    event_type="info"
                )
                return "revision"
        
        # All checks passed!
        self.log(f"✅ All checks passed! Safety={state.safety_score:.2f}, Empathy={state.empathy_score:.2f}")
        state.add_agent_message(
            agent=self.name,
            message=f"✅ Protocol meets all quality standards - Finalizing",
            event_type="success"
        )
        return "finalize"
    
    async def run(self, state: BlackboardState) -> tuple[BlackboardState, str]:
        """
        Evaluate state and decide next action.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state and next node name
        """
        self.log("Evaluating workflow state...")
        
        state.add_agent_message(
            agent=self.name,
            message=f"📋 Evaluation - Safety: {state.safety_score:.2f}, Empathy: {state.empathy_score:.2f}, Iterations: {state.iterations}/{self.max_iterations}",
            event_type="info"
        )
        
        # Make routing decision
        next_step = self.decide_next_step(state)
        
        # Update state metadata
        state.metadata["supervisor_decision"] = {
            "next_step": next_step,
            "safety_score": state.safety_score,
            "empathy_score": state.empathy_score,
            "iterations": state.iterations,
            "reasoning": self._get_decision_reasoning(state, next_step)
        }
        
        return state, next_step
    
    def _get_decision_reasoning(self, state: BlackboardState, decision: str) -> str:
        """Get human-readable reasoning for the decision."""
        if decision == "human_review":
            if state.safety_score < self.safety_threshold:
                return f"Safety score {state.safety_score:.2f} below threshold {self.safety_threshold}"
            elif state.iterations >= self.max_iterations:
                return f"Maximum iterations {self.max_iterations} reached"
            else:
                return "Quality improvements not sufficient after multiple revisions"
        elif decision == "revision":
            if state.safety_score < self.safety_threshold:
                return f"Safety concerns need addressing (score: {state.safety_score:.2f})"
            else:
                return f"Empathy score {state.empathy_score:.2f} below threshold {self.empathy_threshold}"
        elif decision == "finalize":
            return "All quality criteria met"
        else:
            return f"Routing to {decision}"
