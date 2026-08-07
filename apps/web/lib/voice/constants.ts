export const VOICE_SAMPLE_RATE = 16000;
export const VOICE_ENCODING = "pcm_s16le";
export const VOICE_CHANNELS = 1;
export const CAPTURE_BUFFER_SIZE = 4096;

export const WS_EVENTS = {
  client: {
    sessionStart: "session.start",
    audioInput: "audio.input",
    speechEnd: "speech.end",
    sessionEnd: "session.end",
    outputCancel: "output.cancel",
  },
  server: {
    sessionReady: "session.ready",
    transcriptPartial: "transcript.partial",
    transcriptFinal: "transcript.final",
    interviewerThinking: "interviewer.thinking",
    interviewerResponse: "interviewer.response",
    audioOutput: "audio.output",
    sessionError: "session.error",
    sessionEnded: "session.ended",
  },
} as const;
