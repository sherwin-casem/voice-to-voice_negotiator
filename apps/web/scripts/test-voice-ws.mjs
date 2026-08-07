/**
 * Local voice WebSocket integration smoke test.
 *
 * Usage (API must be running on localhost:8000):
 *   node scripts/test-voice-ws.mjs
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USER_ID = process.env.TEST_USER_ID ?? "00000000-0000-4000-8000-000000000001";

function wsUrl(sessionId) {
  const base = new URL(API_URL);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  return `${base.origin}/api/v1/ws/interview/${sessionId}?user_id=${USER_ID}`;
}

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": USER_ID,
      ...(options.headers ?? {}),
    },
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    throw new Error(body.error?.message ?? `HTTP ${response.status}: ${JSON.stringify(body)}`);
  }
  return body.data;
}

function send(socket, type, payload) {
  socket.send(JSON.stringify({ type, payload }));
}

function waitForEvent(socket, type, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error(`Timed out waiting for ${type}`));
    }, timeoutMs);

    const onMessage = (event) => {
      const envelope = JSON.parse(event.data);
      if (envelope.type === type) {
        cleanup();
        resolve(envelope);
      }
    };

    const cleanup = () => {
      clearTimeout(timer);
      socket.removeEventListener("message", onMessage);
    };

    socket.addEventListener("message", onMessage);
  });
}

function fakePcmBase64(durationMs = 200) {
  const sampleCount = Math.floor((16000 * durationMs) / 1000);
  const bytes = Buffer.alloc(sampleCount * 2);
  for (let index = 0; index < sampleCount; index += 1) {
    const sample = Math.floor(Math.sin(index / 10) * 8000);
    bytes.writeInt16LE(sample, index * 2);
  }
  return bytes.toString("base64");
}

async function main() {
  console.log("Creating session...");
  const session = await api("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify({ title: "WS smoke test" }),
  });

  console.log("Configuring session...");
  await api(`/api/v1/sessions/${session.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      interview_type: "behavioral",
      difficulty: "mid",
      target_role: "Software Engineer",
      max_questions: 2,
    }),
  });

  console.log("Connecting WebSocket...");
  const socket = new WebSocket(wsUrl(session.id));

  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });

  const ready = await waitForEvent(socket, "session.ready");
  console.log("session.ready:", ready.payload.status);

  send(socket, "session.start", {
    session_id: session.id,
    audio_format: { sample_rate: 16000, encoding: "pcm_s16le", channels: 1 },
  });

  const firstQuestion = await waitForEvent(socket, "interviewer.response");
  console.log("interviewer.response:", firstQuestion.payload.text);

  await waitForEvent(socket, "audio.output");
  console.log("audio.output received");

  send(socket, "audio.input", {
    seq: 0,
    data: fakePcmBase64(300),
    timestamp_ms: Date.now(),
  });
  send(socket, "speech.end", { timestamp_ms: Date.now() });

  const partial = await waitForEvent(socket, "transcript.partial");
  console.log("transcript.partial:", partial.payload.text);

  const finalTranscript = await waitForEvent(socket, "transcript.final");
  console.log("transcript.final:", finalTranscript.payload.text);

  await waitForEvent(socket, "interviewer.thinking");
  console.log("interviewer.thinking received");

  send(socket, "session.end", { reason: "user_ended" });
  const ended = await waitForEvent(socket, "session.ended");
  console.log("session.ended:", ended.payload.status);

  socket.close();
  console.log("Voice WebSocket smoke test passed.");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
