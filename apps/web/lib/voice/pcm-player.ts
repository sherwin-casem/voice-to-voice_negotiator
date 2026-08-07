import { base64ToBytes, int16ToFloat32, pcmBytesToInt16 } from "@/lib/voice/pcm";

export class PcmStreamPlayer {
  private context: AudioContext | null = null;
  private nextStartTime = 0;
  private activeSources = new Set<AudioBufferSourceNode>();
  private drainCallback: (() => void) | null = null;
  private finalChunkReceived = false;

  async resume(): Promise<void> {
    if (!this.context) {
      this.context = new AudioContext();
    }
    if (this.context.state === "suspended") {
      await this.context.resume();
    }
  }

  /** Called once all buffered audio after a final chunk has finished playing. */
  onDrained(callback: (() => void) | null): void {
    this.drainCallback = callback;
  }

  /**
   * Signal that the final chunk of the current utterance has been enqueued.
   * The drain callback fires when the scheduled buffers actually finish
   * playing, not when the final chunk merely arrives over the wire.
   */
  markFinalChunkReceived(): void {
    this.finalChunkReceived = true;
    this.checkDrained();
  }

  enqueueBase64Chunk(dataBase64: string, sampleRate: number): void {
    if (!this.context) {
      this.context = new AudioContext({ sampleRate });
    }

    const pcmBytes = base64ToBytes(dataBase64);
    const int16 = pcmBytesToInt16(pcmBytes);
    const float32 = int16ToFloat32(int16);
    const buffer = this.context.createBuffer(1, float32.length, sampleRate);
    buffer.copyToChannel(new Float32Array(float32), 0);

    const source = this.context.createBufferSource();
    source.buffer = buffer;
    source.connect(this.context.destination);
    this.activeSources.add(source);
    source.onended = () => {
      this.activeSources.delete(source);
      this.checkDrained();
    };

    const startAt = Math.max(this.context.currentTime, this.nextStartTime);
    source.start(startAt);
    this.nextStartTime = startAt + buffer.duration;
  }

  stop(): void {
    for (const source of this.activeSources) {
      try {
        source.stop();
      } catch {
        // Source may already be stopped.
      }
    }
    this.activeSources.clear();
    this.finalChunkReceived = false;
    this.nextStartTime = 0;
  }

  private checkDrained(): void {
    if (this.finalChunkReceived && this.activeSources.size === 0) {
      this.finalChunkReceived = false;
      this.drainCallback?.();
    }
  }

  dispose(): void {
    this.stop();
    void this.context?.close();
    this.context = null;
  }

  get isPlaying(): boolean {
    return this.activeSources.size > 0;
  }
}
