"""
MCP Server for Cerina Protocol Foundry.
Exposes protocol generation as a tool for AI assistants like Claude.
"""
import asyncio
import json
import logging
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
import uuid

from backend.state.models import BlackboardState
from backend.graph import get_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
mcp_server = Server("cerina-foundry")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="cerina.generate_protocol",
            description=(
                "Generate a safe, evidence-based Cognitive Behavioral Therapy (CBT) protocol. "
                "This tool uses a multi-agent system with safety checks, clinical review, and "
                "iterative refinement to create therapeutic protocols. "
                "Use this when you need structured CBT interventions for anxiety, phobias, "
                "depression, or other mental health conditions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Description of the therapeutic protocol needed (e.g., 'protocol for social anxiety in workplace settings')"
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum revision iterations (default: 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    if name != "cerina.generate_protocol":
        raise ValueError(f"Unknown tool: {name}")
    
    query = arguments.get("query")
    if not query:
        raise ValueError("query parameter is required")
    
    logger.info(f"Generating protocol for: {query}")
    
    try:
        # Generate unique thread ID
        thread_id = f"mcp_{uuid.uuid4().hex[:12]}"
        
        # Create initial state
        initial_state = BlackboardState(
            thread_id=thread_id,
            user_intent=query
        )
        
        # Get workflow (without human-in-the-loop for MCP)
        workflow = get_workflow()
        
        # Run workflow with configuration
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        logger.info("Executing workflow...")
        final_state = await workflow.ainvoke(
            initial_state.model_dump(),
            config=config
        )
        
        # Convert result
        result_state = BlackboardState(**final_state)
        
        # Parse the final draft
        if result_state.active_draft:
            draft_data = json.loads(result_state.active_draft)
            
            # Format output
            output = {
                "status": "success",
                "protocol": draft_data,
                "metadata": {
                    "safety_score": result_state.safety_score,
                    "empathy_score": result_state.empathy_score,
                    "iterations": result_state.iterations,
                    "status": result_state.status,
                    "safety_flags": len(result_state.safety_flags)
                }
            }
            
            # Format as readable text
            formatted_text = f"""# {draft_data['title']}

{draft_data['description']}

## Protocol Steps

"""
            for step in draft_data.get('steps', []):
                formatted_text += f"""### Step {step['step_number']}: {step['title']}
**Exposure Level:** {step['exposure_level']}
{step.get('duration', 'Duration not specified')}

{step['description']}

"""
                if step.get('notes'):
                    formatted_text += f"*Note: {step['notes']}*\n\n"
            
            if draft_data.get('risk_notes'):
                formatted_text += f"\n## ⚠️ Safety Considerations\n\n{draft_data['risk_notes']}\n\n"
            
            if draft_data.get('contraindications'):
                formatted_text += "\n## Contraindications\n\n"
                for ci in draft_data['contraindications']:
                    formatted_text += f"- {ci}\n"
            
            if draft_data.get('clinical_notes'):
                formatted_text += f"\n## Clinical Notes\n\n{draft_data['clinical_notes']}\n\n"
            
            formatted_text += f"\n---\n\n**Quality Metrics:**\n"
            formatted_text += f"- Safety Score: {result_state.safety_score:.2%}\n"
            formatted_text += f"- Empathy Score: {result_state.empathy_score:.2%}\n"
            formatted_text += f"- Revisions: {result_state.iterations}\n"
            
            if result_state.safety_flags:
                formatted_text += f"\n**Safety Flags:** {len(result_state.safety_flags)} concerns addressed during generation\n"
            
            return [
                TextContent(
                    type="text",
                    text=formatted_text
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to generate protocol. Status: {result_state.status}"
                )
            ]
    
    except Exception as e:
        logger.error(f"Error generating protocol: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info("🚀 Starting Cerina Foundry MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
