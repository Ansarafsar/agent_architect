import { useState } from 'react';
import './index.css';
import { useAgentEvents } from './hooks/useAgentEvents';

interface SafetyFlag {
  segment: string;
  risk_level: 'low' | 'medium' | 'high';
  suggestion: string;
}

interface WorkflowState {
  thread_id: string;
  status: 'running' | 'halted' | 'final';
  active_draft: string;
  safety_flags: SafetyFlag[];
  safety_score: number;
  empathy_score: number;
  iterations: number;
}

function App() {
  const [userIntent, setUserIntent] = useState('');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [state, setState] = useState<WorkflowState | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { messages } = useAgentEvents(threadId);

  const startWorkflow = async () => {
    if (!userIntent.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_intent: userIntent }),
      });

      const data = await response.json();
      setThreadId(data.thread_id);

      // Poll for state updates
      pollState(data.thread_id);
    } catch (error) {
      console.error('Failed to start workflow:', error);
      alert('Failed to start workflow. Make sure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const pollState = async (tid: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/state/${tid}`);
        const data = await response.json();
        setState(data);

        if (data.status === 'final' || data.status === 'halted') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Failed to fetch state:', error);
      }
    }, 2000);
  };

  const approveWorkflow = async () => {
    if (!threadId) return;

    try {
      await fetch(`/api/approve/${threadId}`, { method: 'POST' });
      pollState(threadId);
    } catch (error) {
      console.error('Failed to approve:', error);
    }
  };

  const parseDraft = () => {
    if (!state?.active_draft) return null;
    try {
      return JSON.parse(state.active_draft);
    } catch {
      return null;
    }
  };

  const draft = parseDraft();

  return (
    <div className="container">
      <header className="header">
        <h1>🧠 Cerina Protocol Foundry</h1>
        <p>Multi-Agent CBT Protocol Generation with Safety Checks</p>
      </header>

      <div className="thread-form">
        <h2>Create New Protocol</h2>
        <textarea
          value={userIntent}
          onChange={(e) => setUserIntent(e.target.value)}
          placeholder="Describe the CBT protocol you need... (e.g., 'Create a protocol for managing social anxiety in public speaking situations')"
          disabled={isLoading || !!threadId}
        />
        <button onClick={startWorkflow} disabled={isLoading || !!threadId || !userIntent.trim()}>
          {isLoading ? 'Starting...' : 'Generate Protocol'}
        </button>
      </div>

      {threadId && (
        <div className="workflow-container">
          {/* Left Column: Activity Log */}
          <div className="panel">
            <h2>
              Agent Activity
              {state && (
                <span className={`status-badge ${state.status}`}>
                  {state.status}
                </span>
              )}
            </h2>
            <div className="activity-log">
              {messages.length === 0 && <p style={{ color: '#71717a' }}>Waiting for agents...</p>}
              {messages.map((msg, idx) => (
                <div key={idx} className={`log-item ${msg.event_type}`}>
                  <div className="agent">{msg.agent}</div>
                  <div>{msg.message}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Draft & Safety */}
          <div className="panel">
            <h2>Protocol Draft</h2>

            {state && (
              <div className="metrics">
                <div className="metric">
                  <div className={`metric-value ${state.safety_score >= 0.7 ? 'good' : state.safety_score >= 0.5 ? 'medium' : 'bad'}`}>
                    {(state.safety_score * 100).toFixed(0)}%
                  </div>
                  <div className="metric-label">Safety</div>
                </div>
                <div className="metric">
                  <div className={`metric-value ${state.empathy_score >= 0.8 ? 'good' : state.empathy_score >= 0.6 ? 'medium' : 'bad'}`}>
                    {(state.empathy_score * 100).toFixed(0)}%
                  </div>
                  <div className="metric-label">Empathy</div>
                </div>
                <div className="metric">
                  <div className="metric-value">{state.iterations}</div>
                  <div className="metric-label">Iterations</div>
                </div>
              </div>
            )}

            {draft && (
              <div className="draft-viewer">
                <div className="draft-content">
                  <h3>{draft.title}</h3>
                  <p>{draft.description}</p>

                  <h3>Steps:</h3>
                  {draft.steps?.map((step: any, idx: number) => (
                    <div key={idx} style={{ marginBottom: '1rem' }}>
                      <strong>{step.step_number}. {step.title}</strong>
                      <br />
                      <em style={{ color: '#a1a1aa' }}>Exposure: {step.exposure_level}</em>
                      <br />
                      {step.description}
                      {step.notes && <><br /><small>Note: {step.notes}</small></>}
                    </div>
                  ))}

                  {draft.risk_notes && (
                    <>
                      <h3>⚠️ Risk Notes:</h3>
                      <p>{draft.risk_notes}</p>
                    </>
                  )}
                </div>
              </div>
            )}

            {state?.safety_flags && state.safety_flags.length > 0 && (
              <div className="safety-panel">
                <h3 style={{ marginBottom: '0.75rem' }}>🛡️ Safety Concerns</h3>
                {state.safety_flags.map((flag, idx) => (
                  <div key={idx} className={`safety-flag ${flag.risk_level}`}>
                    <div className="level">{flag.risk_level} Risk</div>
                    <div><strong>Issue:</strong> "{flag.segment}"</div>
                    <div style={{ marginTop: '0.5rem' }}><strong>Fix:</strong> {flag.suggestion}</div>
                  </div>
                ))}
              </div>
            )}

            {state?.status === 'halted' && (
              <div className="actions">
                <button className="btn-approve" onClick={approveWorkflow}>
                  ✓ Approve & Finalize
                </button>
              </div>
            )}

            {state?.status === 'final' && (
              <div style={{ marginTop: '1rem', padding: '1rem', background: '#10b98120', borderRadius: '6px', textAlign: 'center' }}>
                <strong style={{ color: '#10b981' }}>✓ Protocol Approved & Finalized!</strong>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
