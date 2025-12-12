"""
Clinical Critic Agent - Evaluates empathy, tone, and clinical quality.
"""
import json
from .base import BaseAgent
from backend.state.models import BlackboardState, ProtocolDraft


CRITIC_PROMPT = """You are a Clinical Quality Critic specializing in therapeutic communication and patient-centered care.

Evaluate this CBT protocol for clinical quality, empathy, and patient-centeredness:

Protocol Title: {title}
Description: {description}

Protocol Steps:
{steps}

Clinical Notes: {clinical_notes}

Evaluate on these dimensions:

1. **EMPATHY & TONE**:
   - Is the language compassionate and non-judgmental?
   - Does it validate the patient's experience?
   - Is it hopeful without being dismissive?

2. **CLARITY**:
   - Are instructions clear and actionable?
   - Would a patient understand what to do?
   - Is medical/technical jargon minimized?

3. **PATIENT-CENTEREDNESS**:
   - Does it respect patient autonomy?
   - Are adaptations mentioned for different needs?
   - Is it culturally sensitive?

4. **CLINICAL APPROPRIATENESS**:
   - Is the progression logical?
   - Are techniques evidence-based?
   - Is professional support adequately emphasized?

5. **ENGAGEMENT**:
   - Would a patient feel motivated to follow this?
   - Is it overwhelming or too sparse?

Respond ONLY with valid JSON:
{{
  "empathy_score": 0.0-1.0,
  "strengths": ["strength1", "strength2"],
  "improvements": [
    {{
      "area": "specific area",
      "issue": "what's wrong",
      "suggestion": "how to fix it"
    }}
  ],
  "overall_feedback": "Brief summary"
}}

Score 0.8+ means excellent empathy and quality.
Score below 0.7 needs revision."""


class ClinicalCriticAgent(BaseAgent):
    """Agent responsible for evaluating clinical quality and empathy."""
    
    def __init__(self):
        super().__init__(name="ClinicalCritic")
    
    async def run(self, state: BlackboardState) -> BlackboardState:
        """
        Evaluate protocol for clinical quality and empathy.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with quality assessment
        """
        self.log("Evaluating clinical quality and empathy...")
        
        state.add_agent_message(
            agent=self.name,
            message="💙 Starting clinical quality review...",
            event_type="start"
        )
        
        try:
            # Parse current draft
            if not state.active_draft:
                state.add_agent_message(
                    agent=self.name,
                    message="⚠️ No draft to review",
                    event_type="warning"
                )
                return state
            
            draft = ProtocolDraft.model_validate_json(state.active_draft)
            
            # Format steps for analysis
            steps_text = "\n".join([
                f"{i+1}. {step.title}\n   {step.description}\n   Duration: {step.duration or 'Not specified'}\n   Notes: {step.notes or 'None'}"
                for i, step in enumerate(draft.steps)
            ])
            
            # Prepare prompt
            prompt = CRITIC_PROMPT.format(
                title=draft.title,
                description=draft.description,
                steps=steps_text,
                clinical_notes=draft.clinical_notes or "None provided"
            )
            
            # Call LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a clinical quality evaluator. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.llm.chat_json(
                messages=messages,
                temperature=0.4,
                max_tokens=3000
            )
            
            # Update state
            state.empathy_score = float(response.get("empathy_score", 0.5))
            
            improvement_count = len(response.get("improvements", []))
            
            if state.empathy_score >= 0.8:
                self.log(f"✅ Excellent quality: Score={state.empathy_score:.2f}")
                state.add_agent_message(
                    agent=self.name,
                    message=f"✅ Excellent clinical quality (Score: {state.empathy_score:.2f})",
                    event_type="success"
                )
            elif state.empathy_score >= 0.7:
                self.log(f"👍 Good quality, minor improvements possible: Score={state.empathy_score:.2f}")
                state.add_agent_message(
                    agent=self.name,
                    message=f"👍 Good quality with {improvement_count} suggested improvements (Score: {state.empathy_score:.2f})",
                    event_type="info"
                )
            else:
                self.log(f"⚠️ Quality needs improvement: Score={state.empathy_score:.2f}")
                state.add_agent_message(
                    agent=self.name,
                    message=f"⚠️ Quality needs improvement (Score: {state.empathy_score:.2f}, {improvement_count} issues found)",
                    event_type="warning"
                )
            
            # Store detailed feedback in metadata
            state.metadata["last_critique"] = {
                "empathy_score": state.empathy_score,
                "strengths": response.get("strengths", []),
                "improvements": response.get("improvements", []),
                "feedback": response.get("overall_feedback", "")
            }
            
            return state
            
        except Exception as e:
            self.log(f"Error in clinical review: {e}", level="error")
            state.add_agent_message(
                agent=self.name,
                message=f"❌ Error during quality review: {str(e)}",
                event_type="error"
            )
            # Default to needs improvement
            state.empathy_score = 0.5
            return state
