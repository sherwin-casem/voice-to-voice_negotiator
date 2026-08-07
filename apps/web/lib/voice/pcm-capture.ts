import { CAPTURE_BUFFER_SIZE, VOICE_SAMPLE_RATE } from "@/lib/voice/constants";
import { bytesToBase64, float32ToInt16 } from "@/lib/voice/pcm";

export type PcmChunkHandler = (chunk: {
  dataBase64: string;
  timestampMs: number;
}) => void;

/**
 * AudioWorklet processor source. Buffers input frames and posts fixed-size
 * Float32 chunks to the main thread. Registered from a Blob URL so no static
 * worklet asset needs to be served.
 */
const CAPTURE_WORKLET_SOURCE = `
class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.chunkSize = (options.processorOptions && options.processorOptions.chunkSize) || 4096;
    this.buffer = new Float32Array(this.chunkSize);
    this.offset = 0;
  }

  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (!channel) {
      return true;
    }
    let read = 0;
    while (read < channel.length) {
      const take = Math.min(this.chunkSize - this.offset, channel.length - read);
      this.buffer.set(channel.subarray(read, read + take), this.offset);
      this.offset += take;
      read += take;
      if (this.offset === this.chunkSize) {
        this.port.postMessage(this.buffer.slice(0));
        this.offset = 0;
      }
    }
    return true;
  }
}
registerProcessor("pcm-capture", PcmCaptureProcessor);
`;

export class PcmCapture {
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private workletNode: AudioWorkletNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private silentSink: GainNode | null = null;
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
    this.source.connect(this.analyser);

    if (this.context.audioWorklet) {
      await this.startWorkletPath();
    } else {
      this.startScriptProcessorPath();
    }

    this.startLevelMonitor();
  }

  private async startWorkletPath(): Promise<void> {
    if (!this.context || !this.analyser) {
      return;
    }
    const blob = new Blob([CAPTURE_WORKLET_SOURCE], { type: "application/javascript" });
    const moduleUrl = URL.createObjectURL(blob);
    try {
      await this.context.audioWorklet.addModule(moduleUrl);
    } finally {
      URL.revokeObjectURL(moduleUrl);
    }

    this.workletNode = new AudioWorkletNode(this.context, "pcm-capture", {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      processorOptions: { chunkSize: CAPTURE_BUFFER_SIZE },
    });
    this.workletNode.port.onmessage = (event: MessageEvent<Float32Array>) => {
      this.emitChunk(event.data);
    };

    // Route through a zero-gain sink: the graph must reach the destination
    // for processing to run, but mic input must never be audible (echo).
    this.silentSink = this.context.createGain();
    this.silentSink.gain.value = 0;
    this.analyser.connect(this.workletNode);
    this.workletNode.connect(this.silentSink);
    this.silentSink.connect(this.context.destination);
  }

  /** Fallback for browsers without AudioWorklet support. */
  private startScriptProcessorPath(): void {
    if (!this.context || !this.analyser) {
      return;
    }
    this.scriptProcessor = this.context.createScriptProcessor(CAPTURE_BUFFER_SIZE, 1, 1);
    this.scriptProcessor.onaudioprocess = (event) => {
      this.emitChunk(event.inputBuffer.getChannelData(0));
    };

    this.silentSink = this.context.createGain();
    this.silentSink.gain.value = 0;
    this.analyser.connect(this.scriptProcessor);
    this.scriptProcessor.connect(this.silentSink);
    this.silentSink.connect(this.context.destination);
  }

  private emitChunk(samples: Float32Array): void {
    if (!this.streaming || !this.chunkHandler) {
      return;
    }
    const pcm = float32ToInt16(samples);
    this.chunkHandler({
      dataBase64: bytesToBase64(new Uint8Array(pcm.buffer)),
      timestampMs: Date.now(),
    });
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
    if (this.workletNode) {
      this.workletNode.port.onmessage = null;
      this.workletNode.disconnect();
    }
    this.scriptProcessor?.disconnect();
    this.silentSink?.disconnect();
    this.analyser?.disconnect();
    this.source?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    void this.context?.close();

    this.workletNode = null;
    this.scriptProcessor = null;
    this.silentSink = null;
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
