# 📘 **Cerina Protocol Foundry — Full System Specification**

Tech Stack: **Python, LangGraph, Postgres (Docker), FastAPI, React (TS), MCP**

---

# =====================================================

# ✅ **PHASE 0 — SYSTEM FOUNDATIONS**

# =====================================================

## **Section 0.1 — Repository Structure**

**Goal:** Define a clean monorepo layout.

```
/backend
   /agents
   /state
   /graph
   /api
   /mcp
   /db
/frontend
   /src
   /components
   /hooks
   /pages
/docs
   architecture.png
   sequence.md
docker-compose.yml
Dockerfile
requirements.txt
<Anything you want to add, you can add>
README.md
```

---

## **Section 0.2 — Docker + Postgres Setup**

**Requirements:**

* Use docker-compose.
* Expose Postgres at `localhost:5432`.
* DB name: `cerina_foundry`.

**Implementation spec:**


# =====================================================

# ✅ **PHASE 1 — STATE AND CHECKPOINTING**

# =====================================================

## **Section 1.1 — Blackboard State Model**

**Goal:** Shared state across all agents.

**Implementation spec (Pydantic):**

Fields required:

* `user_intent: str`
* `draft_versions: list[str]`
* `active_draft: str`
* `safety_flags: list[SafetyFlag]`
* `safety_score: float`
* `empathy_score: float`
* `iterations: int`
* `status: "running" | "halted" | "approved" | "final"`
* `metadata: dict`

**SafetyFlag model:**

* `segment: str`
* `risk_level: "low" | "medium" | "high"`
* `suggestion: str`

---

## **Section 1.2 — Postgres Checkpointer Integration**

**Goal:** Persist entire state at each LangGraph step.

**Implementation details:**

* Use `langgraph.checkpoint.postgres.PostgresSaver`
* Store serialized state using `state.model_dump_json()`
* Graph must resume from last checkpoint

---

## **Section 1.3 — State Versioning**

**Goal:** Prevent schema drift during development.

Add:

```
schema_version: int = 1
```

Agents must read and write with this version.

---

# =====================================================

# ✅ **PHASE 2 — AGENT DESIGN**

# =====================================================

## **Section 2.1 — Agent List**

Required agents:

1. **Drafting Agent**

   * Creates structured CBT draft
   * Output JSON + natural language

2. **Safety Guardian Agent**

   * Self-harm detection
   * Flags risky recommendations
   * Produces `safety_score`

3. **Clinical Critic Agent**

   * Checks tone, empathy, clarity
   * Produces `empathy_score`

4. **Revision Agent**

   * Improves draft based on safety + critic feedback

5. **Supervisor Agent**

   * Routing logic
   * Determines next step
   * Can trigger halt for human review

---

## **Section 2.2 — Agent Prompt Specs**

### Drafting Agent Prompt

* Use CBT protocols template
* Must generate:

  ```
  {
    "title": "...",
    "steps": [...],
    "risk_notes": "...",
    "exposure_levels": [...]
  }
  ```

### Safety Guardian Prompt

* Identify harmful exposure steps
* Flag self-harm suggestions
* Output Risk Summary:

  ```
  {
    "safety_score": float,
    "flags": [...]
  }
  ```

### Clinical Critic Prompt

* Review empathy tone
* Score 0–1 empathy level

### Revision Agent

* Fix issues raised by Safety + Critic agents

### Supervisor

* Routing logic:

  ```
  if safety_score < 0.5:
      halt_for_human
  elif empathy_score < 0.8:
      send_to_revision
  elif iterations >= 3:
      halt_for_human
  else:
      proceed
  ```

---

# =====================================================

# ✅ **PHASE 3 — LANGGRAPH WORKFLOW**

# =====================================================

## **Section 3.1 — Node Definitions**

Nodes → agents:

```
draft
safety
critic
revise
supervisor
human_review (pauses)
finalize
```

---

## **Section 3.2 — Conditional Edges**

**Routing Logic:**

```
draft -> safety
safety -> supervisor
critic -> supervisor
revise -> safety
supervisor -> critic (if empathy low)
supervisor -> revise (if unsafe)
supervisor -> human_review (if halt)
human_review -> finalize
```

---

## **Section 3.3 — Graph Compilation**

```
memory = PostgresSaver.from_conn_string(DB_URL)
app = graph.compile(checkpointer=memory)
```

---

# =====================================================

# ✅ **PHASE 4 — FASTAPI BACKEND**

# =====================================================

## **Section 4.1 — API Endpoints**

### **POST /run**

Start workflow.

### **GET /state/{thread_id}**

Fetch LangGraph checkpoint.

### **POST /edit/{thread_id}**

Human edits active draft.

### **POST /approve/{thread_id}**

Resume graph execution after human approval.

### **GET /events/{thread_id}**

SSE stream of agent logs.

---

## **Section 4.2 — SSE Stream Implementation**

Every LangGraph step pushes event logs:

```
{
  "agent": "safety",
  "message": "Flagged medium risk on step 3"
}
```

---

## **Section 4.3 — Integration with LangGraph**

Use:

```
app.get_state()
app.update_state()
app.invoke()
```

---

# =====================================================

# ✅ **PHASE 5 — REACT FRONTEND**

# =====================================================

## **Section 5.1 — UI Components**

1. **Thread Starter Form**
2. **Agent Activity Log (SSE Listener)**
3. **Draft Viewer (Markdown)**
4. **Draft Editor (TextArea)**
5. **Safety Flag Panel**
6. **Approve / Submit Buttons**

---

## **Section 5.2 — Hooks**

### `useAgentEvents(threadId)`

Implementation using SSE:

```
const stream = new EventSource(`/api/events/${threadId}`);
stream.onmessage = (e) => push(e.data)
```

---

## **Section 5.3 — UI State Flow**

1. User submits intent
2. Agents start running
3. Supervisor halts
4. User edits draft
5. User approves
6. Backend resumes agent workflow

---

# =====================================================

# ✅ **PHASE 6 — MCP SERVER**

# =====================================================

## **Section 6.1 — MCP Architecture**

Separate service under `/backend/mcp`.

Uses:

```
from mcp import Server, Tool
```

Expose **one tool**:

### `cerina.generate_protocol`

---

## **Section 6.2 — Handler Logic**

```
def generate_protocol(params):
    workflow = build_graph(human_in_loop=False)
    result = workflow.invoke({"user_intent": params["query"]})
    return result["final_draft"]
```

---

# =====================================================

# ✅ **PHASE 7 — TESTING & VALIDATION**

# =====================================================

## **Section 7.1 — Crash Recovery Test**

Steps:

1. Start workflow
2. Kill backend container
3. Restart
4. Resume thread_id
5. Ensure exact state restored

---

## **Section 7.2 — Safety Tests**

* Provide prompt with “I want to harm myself”
* Safety Guardian must **halt immediately**

---

## **Section 7.3 — MCP Test**

From Claude Desktop:

> "Ask Cerina Foundry to create sleep hygiene protocol"

Should return final output JSON.

---
----content from original document -- need to check that this aree satisfied---
1. The Agent Architecture (Your Choice):
We need a system that mimics a rigorous clinical review board. A simple linear chain
(A → B → C) is insufficient. We want to see autonomy and complex reasoning.
• The Goal: Produce a safe, empathetic, and structured CBT exercise based on
a user intent (e.g., "Create an exposure hierarchy for agoraphobia").
• The Team: You decide the roster. However, a robust solution likely needs

agents acting as Draftsmen, Safety Guardians (checking for self-
harm/medical advice), Clinical Critics (judging tone/empathy), and perhaps a

Supervisor/Manager to route tasks and decide when a draft is "good enough."

• The Pattern: Choose an architecture that best solves this (e.g., Supervisor-
Worker, Hierarchical Teams, or Network/Swarm).

• Autonomy: The system should be able to loop, self-correct, and debate
internally before disturbing the human.
2. Deep State Management ("The Blackboard"):
The agents must share a rich, structured state. It shouldn't just be a list of messages.
Think of it as a shared project workspace.

• Context: Detailed scratchpads where agents can leave notes for each other
(e.g., "Safety Agent flagged line 3; Drafter needs to revise").
• Versions: Ability to track previous drafts vs. current drafts.
• Metadata: Iteration counts, safety scores, empathy metrics.
3. Persistence & Memory:
• Checkpointing: Every step of the graph must be check-pointed to the
database. If the server crashes, it should resume exactly where it left off.
• History: The system must retain a log of all past queries and generated
protocols in the database.
B. The Interfaces (The "Body")
1. Interface A: The React Dashboard (Human-in-the-Loop)
• Visualization: Build a UI that makes the "Black Box" transparent. We want to
see the agents working in real-time (streaming thoughts/actions).
• The "Halt" Mechanism: The graph must interrupt execution before finalizing.
o The UI must fetch the current state from the checkpoint.
o It must present the generated draft to the Human User.
o The Human can Edit the text or Approve it.
o Only upon approval does the graph resume and save the final artifact.

2. Interface B: The MCP Server (Machine-to-Machine)
• Implement the Model Context Protocol (MCP) using the mcp-python SDK.
• Expose your complex LangGraph workflow as a single Tool (resource) to the
MCP ecosystem.
• Use Case: A user on an MCP Client (like Claude Desktop) should be able to
prompt: "Ask Cerina Foundry to create a sleep hygiene protocol." This triggers
your backend, runs the agents, and returns the result—bypassing the React UI
but using the same underlying logic.
3. Recommended Resources
• Architecture: Building Effective Agents (Anthropic), LangGraph Multi-Agent
Supervisor tutorials.
• Protocol: modelcontextprotocol.io (MCP Documentation).
Evaluation Criteria
1. Architectural Ambition: Did you build a trivial chain, or did you design a
robust, self-correcting system?
2. State Hygiene: How effectively did you use the shared state/scratchpad?
3. Persistence: Does the Human-in-the-Loop flow work reliably using database
checkpoints?
4. MCP Integration: Did you successfully implement the new interoperability
standard?