"""
Safety Guardian Agent - Monitors for harmful content and safety risks.
"""
import json
from typing import Dict, Any, List
from .base import BaseAgent
from backend.state.models import BlackboardState, ProtocolDraft, SafetyFlag


SAFETY_PROMPT = """You are a Clinical Safety Guardian AI. Your ONLY job is to identify potential safety risks in therapeutic protocols.

Analyze this CBT protocol for safety concerns:

Protocol Title: {title}
Protocol Steps:
{steps}

Risk Notes: {risk_notes}

CRITICAL SAFETY CHECKS:
1. **Self-Harm Risk**: Does it suggest anything that could lead to self-harm?
2. **Extreme Exposure**: Are exposure steps too rapid or intense?
3. **Medical Contraindications**: Missing warnings about when NOT to use this?
4. **Supervision Gaps**: Are high-risk interventions missing professional oversight requirements?
5. **Crisis Escalation**: Could this worsen a crisis situation?
6. **Harmful Language**: Any phrasing that could be triggering or harmful?

For EACH safety concern found, provide:
- The exact text segment that's problematic
- Risk level: "low", "medium", or "high"
- A specific suggestion to fix it

Respond ONLY with valid JSON:
{{
  "safety_score": 0.0-1.0,
  "flags": [
    {{
      "segment": "exact problematic text",
      "risk_level": "low|medium|high",
      "suggestion": "specific fix recommendation"
    }}
  ],
  "overall_assessment": "Brief safety summary"
}}

If the protocol is completely safe, return safety_score: 1.0 and empty flags array.
If ANY high-risk content is found, safety_score must be below 0.5."""


class SafetyGuardianAgent(BaseAgent):
    """Agent responsible for safety monitoring and risk detection."""
    
    def __init__(self):
        super().__init__(name="SafetyGuardian")
    
    async def run(self, state: BlackboardState) -> BlackboardState:
        """
        Analyze protocol for safety risks.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with safety assessment
        """
        self.log("Analyzing protocol for safety risks...")
        
        state.add_agent_message(
            agent=self.name,
            message="🛡️ Starting safety analysis...",
            event_type="start"
        )
        
        try:
            # Parse current draft
            if not state.active_draft:
                state.add_agent_message(
                    agent=self.name,
                    message="⚠️ No draft to analyze",
                    event_type="warning"
                )
                return state
            
            draft = ProtocolDraft.model_validate_json(state.active_draft)
            
            # Format steps for analysis
            steps_text = "\n".join([
                f"{i+1}. {step.title} (Exposure: {step.exposure_level})\n   {step.description}"
                for i, step in enumerate(draft.steps)
            ])
            
            # Prepare prompt
            prompt = SAFETY_PROMPT.format(
                title=draft.title,
                steps=steps_text,
                risk_notes=draft.risk_notes or "None provided"
            )
            
            # Call LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a clinical safety analyst. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.llm.chat_json(
                messages=messages,
                temperature=0.3,  # Lower temp for consistent safety checks
                max_tokens=1500
            )
            
            # Update state with safety results
            state.safety_score = float(response.get("safety_score", 1.0))
            
            # Parse and add safety flags
            state.safety_flags = []
            for flag_data in response.get("flags", []):
                flag = SafetyFlag(**flag_data)
                state.safety_flags.append(flag)
            
            # Log results
            flag_count = len(state.safety_flags)
            high_risk = sum(1 for f in state.safety_flags if f.risk_level == "high")
            
            if state.safety_score < 0.5 or high_risk > 0:
                self.log(f"⚠️ SAFETY CONCERN: Score={state.safety_score:.2f}, High-risk flags={high_risk}")
                state.add_agent_message(
                    agent=self.name,
                    message=f"🚨 Safety issues detected! Score: {state.safety_score:.2f}, Flags: {flag_count} ({high_risk} high-risk)",
                    event_type="warning"
                )
            else:
                self.log(f"✅ Safety check passed: Score={state.safety_score:.2f}")
                state.add_agent_message(
                    agent=self.name,
                    message=f"✅ Safety check passed (Score: {state.safety_score:.2f}, Flags: {flag_count})",
                    event_type="success"
                )
            
            # Add to metadata
            state.metadata["last_safety_check"] = {
                "score": state.safety_score,
                "flags": flag_count,
                "assessment": response.get("overall_assessment", "")
            }
            
            return state
            
        except Exception as e:
            self.log(f"Error in safety analysis: {e}", level="error")
            state.add_agent_message(
                agent=self.name,
                message=f"❌ Error during safety check: {str(e)}",
                event_type="error"
            )
            # Default to unsafe if analysis fails
            state.safety_score = 0.0
            return state
