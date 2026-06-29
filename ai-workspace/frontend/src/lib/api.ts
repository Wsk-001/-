/**
 * API 客户端 - 与后端 FastAPI 通信
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * 发送聊天消息并获取流式响应
 * 使用 fetch + ReadableStream 解析 SSE
 */
export async function streamChat(
  message: string,
  sessionId: string,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<AbortController> {
  const controller = new AbortController();

  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      onError(`HTTP ${response.status}: ${text}`);
      return controller;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError("No response body");
      return controller;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 解析 SSE 数据行
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // 保留最后一个可能不完整的行

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data: ")) continue;

        const jsonStr = trimmed.slice(6); // 去掉 "data: "
        try {
          const data = JSON.parse(jsonStr);

          if (data.error) {
            onError(data.error);
          } else if (data.done) {
            onDone();
          } else if (data.token) {
            onToken(data.token);
          }
        } catch {
          // 解析失败的行跳过
        }
      }
    }

    onDone();
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return controller;
    }
    onError(err instanceof Error ? err.message : "Unknown error");
  }

  return controller;
}
