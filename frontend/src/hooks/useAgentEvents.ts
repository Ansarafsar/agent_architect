import { useEffect, useState, useRef } from 'react';

interface AgentMessage {
    agent: string;
    message: string;
    event_type: string;
    timestamp: string;
}

export function useAgentEvents(threadId: string | null) {
    const [messages, setMessages] = useState<AgentMessage[]>([]);
    const [isComplete, setIsComplete] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);

    useEffect(() => {
        if (!threadId) {
            return;
        }

        // Close existing connection
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        // Open new SSE connection
        const eventSource = new EventSource(`/api/events/${threadId}`);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.event === 'complete') {
                    setIsComplete(true);
                    eventSource.close();
                } else if (data.error) {
                    console.error('SSE Error:', data.error);
                    eventSource.close();
                } else {
                    setMessages((prev) => [...prev, data]);
                }
            } catch (e) {
                console.error('Failed to parse SSE message:', e);
            }
        };

        eventSource.onerror = () => {
            console.error('SSE connection error');
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [threadId]);

    return { messages, isComplete };
}
