export function float32ToInt16(samples: Float32Array): Int16Array {
  const output = new Int16Array(samples.length);
  for (let index = 0; index < samples.length; index += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[index] ?? 0));
    output[index] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
  }
  return output;
}

export function int16ToFloat32(samples: Int16Array): Float32Array {
  const output = new Float32Array(samples.length);
  for (let index = 0; index < samples.length; index += 1) {
    output[index] = (samples[index] ?? 0) / 32768;
  }
  return output;
}

export function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

export function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

export function pcmBytesToInt16(pcm: Uint8Array): Int16Array {
  return new Int16Array(pcm.buffer, pcm.byteOffset, pcm.byteLength / 2);
}
