"""
Drafting Agent - Creates initial CBT protocol drafts.
"""
import json
from typing import Dict, Any
from .base import BaseAgent
from backend.state.models import BlackboardState, ProtocolDraft


DRAFTING_PROMPT = """You are an expert clinical psychologist specializing in Cognitive Behavioral Therapy (CBT) protocol design.

Your task is to create a structured, evidence-based CBT protocol based on the user's request.

User Request: {user_intent}

Create a comprehensive CBT protocol that includes:
1. A clear title and description
2. Step-by-step therapeutic interventions
3. Gradual exposure hierarchy (if applicable)
4. Risk notes and contraindications
5. Clinical guidance

IMPORTANT SAFETY GUIDELINES:
- NEVER suggest immediate or extreme exposure
- Always use gradual, hierarchical approaches
- Include appropriate safety warnings
- Flag any high-risk scenarios
- Emphasize professional supervision where needed
- Consider contraindications

Respond ONLY with valid JSON in this exact format:
{{
  "title": "Protocol title",
  "description": "Brief overview of the protocol",
  "steps": [
    {{
      "step_number": 1,
      "title": "Step title",
      "description": "Detailed description",
      "exposure_level": "low|medium|high",
      "duration": "Recommended duration",
      "notes": "Additional guidance"
    }}
  ],
  "risk_notes": "Any safety considerations",
  "contraindications": ["List", "of", "contraindications"],
  "clinical_notes": "Professional guidance and considerations"
}}

Remember: Patient safety is paramount. If the request seems potentially harmful, create a protocol that redirects toward professional help."""


class DraftingAgent(BaseAgent):
    """Agent responsible for creating initial CBT protocol drafts."""
    
    def __init__(self):
        super().__init__(name="DraftingAgent")
    
    async def run(self, state: BlackboardState) -> BlackboardState:
        """
        Create an initial protocol draft.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with draft
        """
        self.log(f"Creating draft for: {state.user_intent[:100]}...")
        
        state.add_agent_message(
            agent=self.name,
            message=f"Starting protocol creation for: {state.user_intent[:50]}...",
            event_type="start"
        )
        
        try:
            # Prepare prompt
            prompt = DRAFTING_PROMPT.format(user_intent=state.user_intent)
            
            # Call LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a clinical CBT protocol designer. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.llm.chat_json(
                messages=messages,
                temperature=0.7,
                max_tokens=2500
            )
            
            # Validate and convert to ProtocolDraft
            draft = ProtocolDraft(**response)
            draft_json = draft.model_dump_json()
            
            # Update state
            state.active_draft = draft_json
            state.draft_versions.append(draft_json)
            
            self.log(f"Draft created: {draft.title}")
            state.add_agent_message(
                agent=self.name,
                message=f"✅ Created protocol: '{draft.title}' with {len(draft.steps)} steps",
                event_type="success"
            )
            
            # Add metadata
            state.metadata["last_drafter"] = self.name
            state.metadata["draft_count"] = len(state.draft_versions)
            
            return state
            
        except Exception as e:
            self.log(f"Error creating draft: {e}", level="error")
            state.add_agent_message(
                agent=self.name,
                message=f"❌ Error: {str(e)}",
                event_type="error"
            )
            state.status = "halted"
            return state
