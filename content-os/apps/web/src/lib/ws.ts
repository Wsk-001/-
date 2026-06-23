import { TaskEvent } from "./types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function subscribeToTask(
  taskId: string,
  onEvent: (event: TaskEvent) => void
): () => void {
  const ws = new WebSocket(`${WS_BASE}/api/ws/tasks/${taskId}`);

  ws.onmessage = (event) => {
    try {
      const data: TaskEvent = JSON.parse(event.data);
      onEvent(data);
    } catch (err) {
      console.error("Failed to parse WebSocket message:", err);
    }
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  ws.onclose = () => {
    console.log(`WebSocket closed for task ${taskId}`);
  };

  return () => {
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close();
    }
  };
}
