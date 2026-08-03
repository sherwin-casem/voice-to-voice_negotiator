import { CAPTURE_BUFFER_SIZE, VOICE_SAMPLE_RATE } from "@/lib/voice/constants";
import { bytesToBase64, float32ToInt16 } from "@/lib/voice/pcm";

export type PcmChunkHandler = (chunk: {
  dataBase64: string;
  timestampMs: number;
}) => void;

export class PcmCapture {
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private analyser: AnalyserNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private animationFrame: number | null = null;
  private levelHandler: ((level: number) => void) | null = null;
  private chunkHandler: PcmChunkHandler | null = null;
  private streaming = false;

  get isStreaming(): boolean {
    return this.streaming;
  }

  async start(): Promise<void> {
    if (this.stream) {
      return;
    }

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    this.context = new AudioContext({ sampleRate: VOICE_SAMPLE_RATE });
    this.source = this.context.createMediaStreamSource(this.stream);
    this.analyser = this.context.createAnalyser();
    this.analyser.fftSize = 256;
    this.processor = this.context.createScriptProcessor(CAPTURE_BUFFER_SIZE, 1, 1);

    this.processor.onaudioprocess = (event) => {
      if (!this.streaming || !this.chunkHandler) {
        return;
      }

      const channel = event.inputBuffer.getChannelData(0);
      const pcm = float32ToInt16(channel);
      this.chunkHandler({
        dataBase64: bytesToBase64(new Uint8Array(pcm.buffer)),
        timestampMs: Date.now(),
      });
    };

    this.source.connect(this.analyser);
    this.analyser.connect(this.processor);
    this.processor.connect(this.context.destination);
    this.startLevelMonitor();
  }

  onChunk(handler: PcmChunkHandler | null): void {
    this.chunkHandler = handler;
  }

  onLevel(handler: ((level: number) => void) | null): void {
    this.levelHandler = handler;
  }

  beginStreaming(): void {
    this.streaming = true;
  }

  stopStreaming(): void {
    this.streaming = false;
  }

  stop(): void {
    this.stopStreaming();
    this.stopLevelMonitor();
    this.processor?.disconnect();
    this.analyser?.disconnect();
    this.source?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    void this.context?.close();

    this.processor = null;
    this.analyser = null;
    this.source = null;
    this.stream = null;
    this.context = null;
    this.chunkHandler = null;
    this.levelHandler = null;
  }

  private startLevelMonitor(): void {
    if (!this.analyser || !this.levelHandler) {
      return;
    }

    const data = new Uint8Array(this.analyser.frequencyBinCount);
    const tick = () => {
      if (!this.analyser || !this.levelHandler) {
        return;
      }
      this.analyser.getByteFrequencyData(data);
      const average = data.reduce((sum, value) => sum + value, 0) / data.length;
      this.levelHandler(Math.min(1, average / 128));
      this.animationFrame = requestAnimationFrame(tick);
    };
    tick();
  }

  private stopLevelMonitor(): void {
    if (this.animationFrame !== null) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    this.levelHandler?.(0);
  }
}
