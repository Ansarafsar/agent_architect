"""
Revision Agent - Improves drafts based on safety and critic feedback.
"""
import json
from .base import BaseAgent
from backend.state.models import BlackboardState, ProtocolDraft, SafetyFlag


REVISION_PROMPT = """You are a Senior Clinical Protocol Editor specializing in CBT interventions.

Your task is to REVISE and IMPROVE this protocol based on feedback from safety and quality reviews.

ORIGINAL PROTOCOL:
{original_draft}

SAFETY FEEDBACK (Score: {safety_score}/1.0):
{safety_feedback}

QUALITY FEEDBACK (Empathy Score: {empathy_score}/1.0):
{quality_feedback}

Your revision MUST:
1. Address ALL safety concerns with specific fixes
2. Implement ALL suggested quality improvements
3. Maintain the core therapeutic approach
4. Enhance empathy and patient-centeredness
5. Keep the same structure (title, steps, etc.)

If there are HIGH-RISK safety flags:
- Rewrite those sections completely
- Add safety warnings
- Include crisis resources
- Emphasize professional supervision

If empathy score is low:
- Use more compassionate language
- Add validation statements
- Make instructions clearer and gentler
- Reduce jargon

Respond ONLY with valid JSON in the EXACT same format as the original:
{{
  "title": "Revised title if needed",
  "description": "Enhanced description",
  "steps": [
    {{
      "step_number": 1,
      "title": "Step title",
      "description": "IMPROVED description addressing feedback",
      "exposure_level": "low|medium|high",
      "duration": "Duration",
      "notes": "Enhanced notes with safety considerations"
    }}
  ],
  "risk_notes": "ENHANCED safety notes addressing all concerns",
  "contraindications": ["Comprehensive", "list"],
  "clinical_notes": "IMPROVED professional guidance"
}}"""


class RevisionAgent(BaseAgent):
    """Agent responsible for revising drafts based on feedback."""
    
    def __init__(self):
        super().__init__(name="RevisionAgent")
    
    async def run(self, state: BlackboardState) -> BlackboardState:
        """
        Revise protocol based on safety and critic feedback.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with revised draft
        """
        self.log("Revising protocol based on feedback...")
        
        state.add_agent_message(
            agent=self.name,
            message="✏️ Starting protocol revision...",
            event_type="start"
        )
        
        try:
            # Check if we have a draft to revise
            if not state.active_draft:
                state.add_agent_message(
                    agent=self.name,
                    message="⚠️ No draft to revise",
                    event_type="warning"
                )
                return state
            
            # Parse current draft
            current_draft = ProtocolDraft.model_validate_json(state.active_draft)
            
            # Format safety feedback
            safety_feedback = "No major safety concerns."
            if state.safety_flags:
                safety_items = []
                for flag in state.safety_flags:
                    safety_items.append(
                        f"- [{flag.risk_level.upper()}] \"{flag.segment}\"\n"
                        f"  Fix: {flag.suggestion}"
                    )
                safety_feedback = "\n".join(safety_items)
            
            # Format quality feedback
            quality_feedback = "No major quality concerns."
            if "last_critique" in state.metadata:
                critique = state.metadata["last_critique"]
                improvements = critique.get("improvements", [])
                if improvements:
                    quality_items = []
                    for imp in improvements:
                        quality_items.append(
                            f"- {imp.get('area', 'General')}: {imp.get('issue', '')}\n"
                            f"  Suggestion: {imp.get('suggestion', '')}"
                        )
                    quality_feedback = "\n".join(quality_items)
                    quality_feedback += f"\n\nOverall: {critique.get('feedback', '')}"
            
            # Prepare prompt
            prompt = REVISION_PROMPT.format(
                original_draft=state.active_draft,
                safety_score=state.safety_score,
                safety_feedback=safety_feedback,
                empathy_score=state.empathy_score,
                quality_feedback=quality_feedback
            )
            
            # Call LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a clinical protocol editor. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.llm.chat_json(
                messages=messages,
                temperature=0.6,
                max_tokens=2500
            )
            
            # Validate and update
            revised_draft = ProtocolDraft(**response)
            revised_json = revised_draft.model_dump_json()
            
            # Update state
            state.active_draft = revised_json
            state.draft_versions.append(revised_json)
            state.increment_iteration()
            
            self.log(f"Revision complete. Iteration #{state.iterations}")
            state.add_agent_message(
                agent=self.name,
                message=f"✅ Revision #{state.iterations} complete: '{revised_draft.title}'",
                event_type="success"
            )
            
            # Track revision in metadata
            state.metadata["last_revision"] = {
                "iteration": state.iterations,
                "safety_addressed": len(state.safety_flags),
                "quality_addressed": len(state.metadata.get("last_critique", {}).get("improvements", []))
            }
            
            return state
            
        except Exception as e:
            self.log(f"Error during revision: {e}", level="error")
            state.add_agent_message(
                agent=self.name,
                message=f"❌ Error during revision: {str(e)}",
                event_type="error"
            )
            state.status = "halted"
            return state
