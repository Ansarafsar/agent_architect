"""
Pydantic models for Cerina Protocol Foundry state management.
Implements the blackboard state pattern for multi-agent collaboration.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SafetyFlag(BaseModel):
    """Represents a safety concern in a protocol draft."""
    segment: str = Field(..., description="The specific text segment flagged")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Severity of the risk")
    suggestion: str = Field(..., description="Recommended improvement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment": "Try exposing yourself to heights immediately",
                "risk_level": "high",
                "suggestion": "Use gradual exposure hierarchy starting with safe visualization"
            }
        }


class ProtocolStep(BaseModel):
    """Individual step in a CBT protocol."""
    step_number: int
    title: str
    description: str
    exposure_level: Literal["low", "medium", "high"]
    duration: Optional[str] = None
    notes: Optional[str] = None


class ProtocolDraft(BaseModel):
    """Structured CBT protocol draft."""
    title: str
    description: str
    steps: list[ProtocolStep] = Field(default_factory=list)
    risk_notes: str = ""
    contraindications: list[str] = Field(default_factory=list)
    clinical_notes: str = ""


class BlackboardState(BaseModel):
    """
    Shared state across all agents in the workflow.
    This implements the blackboard pattern for multi-agent coordination.
    """
    # Schema versioning
    schema_version: int = Field(default=1, description="State schema version")
    
    # Thread management
    thread_id: str = Field(..., description="Unique thread identifier")
    
    # User input
    user_intent: str = Field(..., description="The original user request")
    
    # Draft management
    draft_versions: list[str] = Field(
        default_factory=list,
        description="JSON strings of historical drafts"
    )
    active_draft: str = Field(
        default="",
        description="Current draft as JSON string"
    )
    
    # Safety tracking
    safety_flags: list[SafetyFlag] = Field(
        default_factory=list,
        description="List of safety concerns identified"
    )
    safety_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall safety score (0=unsafe, 1=safe)"
    )
    
    # Quality metrics
    empathy_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Empathy and tone score (0=poor, 1=excellent)"
    )
    
    # Iteration tracking
    iterations: int = Field(
        default=0,
        description="Number of revision cycles completed"
    )
    
    # Workflow status
    status: Literal["running", "halted", "approved", "final"] = Field(
        default="running",
        description="Current workflow state"
    )
    
    # Metadata
    metadata: dict = Field(
        default_factory=dict,
        description="Additional context and tracking data"
    )
    
    # Agent messages
    agent_messages: list[dict] = Field(
        default_factory=list,
        description="Log of agent activities for UI display"
    )
    
    # Human review
    human_feedback: Optional[str] = Field(
        default=None,
        description="Feedback from human reviewer"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": 1,
                "thread_id": "thread_abc123",
                "user_intent": "Create a protocol for social anxiety in public speaking",
                "draft_versions": [],
                "active_draft": "",
                "safety_flags": [],
                "safety_score": 1.0,
                "empathy_score": 0.5,
                "iterations": 0,
                "status": "running",
                "metadata": {},
                "agent_messages": []
            }
        }
    
    def add_agent_message(self, agent: str, message: str, event_type: str = "info"):
        """Add a message from an agent to the log."""
        self.agent_messages.append({
            "agent": agent,
            "message": message,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def increment_iteration(self):
        """Increment the iteration counter."""
        self.iterations += 1
        self.updated_at = datetime.utcnow()


class WorkflowInput(BaseModel):
    """Input for starting a new workflow."""
    user_intent: str = Field(..., description="User's request for a CBT protocol")
    thread_id: Optional[str] = Field(None, description="Optional thread ID for resuming")


class WorkflowOutput(BaseModel):
    """Output from the workflow."""
    thread_id: str
    status: Literal["running", "halted", "approved", "final"]
    final_draft: Optional[ProtocolDraft] = None
    safety_score: float
    empathy_score: float
    iterations: int
    requires_human_review: bool = False
    message: str = ""
