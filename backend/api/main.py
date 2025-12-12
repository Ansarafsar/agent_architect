"""
FastAPI application for Cerina Protocol Foundry.
Provides REST API endpoints for the multi-agent workflow.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uuid
import json
import asyncio
import logging
from typing import Optional

from backend.state.models import BlackboardState, WorkflowInput, WorkflowOutput, ProtocolDraft
from backend.state.checkpointer import get_checkpointer, get_checkpointer_async, reset_checkpointer
from backend.graph import get_workflow
from backend.db import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🚀 Starting Cerina Protocol Foundry API...")
    
    # Initialize database
    await init_db()
    
    # Initialize checkpointer
    await get_checkpointer_async()
    
    # Initialize workflow graph (compile once and cache)
    logger.info("📊 Initializing workflow graph...")
    get_workflow()
    
    logger.info("✅ API ready!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    await close_db()
    await reset_checkpointer()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Cerina Protocol Foundry API",
    description="Multi-agent CBT protocol generation with safety checks and human-in-the-loop review",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# API Endpoints
# ========================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Cerina Protocol Foundry API",
        "version": "0.1.0"
    }


@app.post("/run", response_model=WorkflowOutput)
async def run_workflow(input_data: WorkflowInput):
    """
    Start a new protocol generation workflow.
    
    Args:
        input_data: User intent for protocol creation
        
    Returns:
        Workflow output with thread_id and status
    """
    logger.info(f"Starting new workflow: {input_data.user_intent[:100]}...")
    
    try:
        # Generate thread ID
        thread_id = input_data.thread_id or f"thread_{uuid.uuid4().hex[:12]}"
        
        # Create initial state
        initial_state = BlackboardState(
            thread_id=thread_id,
            user_intent=input_data.user_intent
        )
        
        # Get workflow
        workflow = get_workflow()
        
        # Run workflow
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the workflow
        final_state = await workflow.ainvoke(
            initial_state.model_dump(),
            config=config
        )
        
        # Convert back to BlackboardState
        result_state = BlackboardState(**final_state)
        
        # Parse final draft if available
        final_draft = None
        if result_state.active_draft:
            try:
                final_draft = ProtocolDraft.model_validate_json(result_state.active_draft)
            except:
                pass
        
        return WorkflowOutput(
            thread_id=thread_id,
            status=result_state.status,
            final_draft=final_draft,
            safety_score=result_state.safety_score,
            empathy_score=result_state.empathy_score,
            iterations=result_state.iterations,
            requires_human_review=(result_state.status == "halted"),
            message=f"Workflow completed with status: {result_state.status}"
        )
        
    except Exception as e:
        logger.error(f"Error running workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/{thread_id}")
async def get_state(thread_id: str):
    """
    Get the current state of a workflow thread.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        Current workflow state
    """
    logger.info(f"Fetching state for thread: {thread_id}")
    
    try:
        workflow = get_workflow()
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        state = await workflow.aget_state(config)
        
        if not state or not state.values:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        return state.values
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edit/{thread_id}")
async def edit_draft(thread_id: str, edited_draft: ProtocolDraft):
    """
    Edit the active draft in a workflow.
    
    Args:
        thread_id: Thread identifier
        edited_draft: Updated protocol draft
        
    Returns:
        Success message
    """
    logger.info(f"Editing draft for thread: {thread_id}")
    
    try:
        workflow = get_workflow()
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        state_snapshot = await workflow.aget_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # Update the active draft
        current_state = BlackboardState(**state_snapshot.values)
        current_state.active_draft = edited_draft.model_dump_json()
        current_state.add_agent_message(
            agent="Human",
            message="Draft manually edited by user",
            event_type="edit"
        )
        
        # Update state in checkpoint
        await workflow.aupdate_state(config, current_state.model_dump())
        
        return {"message": "Draft updated successfully", "thread_id": thread_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing draft: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve/{thread_id}")
async def approve_and_resume(thread_id: str, feedback: Optional[str] = None):
    """
    Approve the current draft and resume workflow.
    
    Args:
        thread_id: Thread identifier
        feedback: Optional human feedback
        
    Returns:
        Updated workflow status
    """
    logger.info(f"Approving and resuming thread: {thread_id}")
    
    try:
        workflow = get_workflow()
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        state_snapshot = await workflow.aget_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # Update state
        current_state = BlackboardState(**state_snapshot.values)
        
        if feedback:
            current_state.human_feedback = feedback
        
        current_state.status = "approved"
        current_state.add_agent_message(
            agent="Human",
            message=f"Draft approved{' with feedback: ' + feedback if feedback else ''}",
            event_type="approval"
        )
        
        # Update and resume
        await workflow.aupdate_state(config, current_state.model_dump())
        
        # Resume execution (run next step which should be finalize)
        result = await workflow.ainvoke(None, config=config)
        result_state = BlackboardState(**result)
        
        return {
            "message": "Workflow approved and finalized",
            "thread_id": thread_id,
            "status": result_state.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{thread_id}")
async def stream_events(thread_id: str):
    """
    Stream workflow events via Server-Sent Events (SSE).
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        SSE stream of agent messages
    """
    async def event_generator():
        """Generate SSE events from workflow state."""
        try:
            workflow = get_workflow()
            config = {"configurable": {"thread_id": thread_id}}
            
            last_message_count = 0
            
            # Poll for new messages (in production, use proper event system)
            for _ in range(60):  # Poll for max 60 seconds
                try:
                    state_snapshot = await workflow.aget_state(config)
                    
                    if state_snapshot and state_snapshot.values:
                        current_state = BlackboardState(**state_snapshot.values)
                        messages = current_state.agent_messages
                        
                        # Send new messages
                        if len(messages) > last_message_count:
                            new_messages = messages[last_message_count:]
                            for msg in new_messages:
                                yield f"data: {json.dumps(msg)}\n\n"
                            last_message_count = len(messages)
                        
                        # Stop if workflow is done
                        if current_state.status in ["final", "halted"]:
                            yield f"data: {json.dumps({'event': 'complete', 'status': current_state.status})}\n\n"
                            break
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in event stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break
                    
        except Exception as e:
            logger.error(f"Fatal error in event generator: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
