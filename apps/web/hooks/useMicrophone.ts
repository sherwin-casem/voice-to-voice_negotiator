"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface MicrophoneState {
  isEnabled: boolean;
  isRecording: boolean;
  permissionDenied: boolean;
  level: number;
  enable: () => Promise<void>;
  startRecording: () => void;
  stopRecording: () => void;
  disable: () => void;
}

export function useMicrophone(): MicrophoneState {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [level, setLevel] = useState(0);

  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);

  const stopAnalyser = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    setLevel(0);
  }, []);

  const startAnalyser = useCallback((stream: MediaStream) => {
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;

    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(data);
      const average = data.reduce((sum, value) => sum + value, 0) / data.length;
      setLevel(Math.min(1, average / 128));
      animationRef.current = requestAnimationFrame(tick);
    };
    tick();
  }, []);

  const disable = useCallback(() => {
    stopAnalyser();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void audioContextRef.current?.close();
    audioContextRef.current = null;
    analyserRef.current = null;
    setIsEnabled(false);
    setIsRecording(false);
  }, [stopAnalyser]);

  const enable = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      setPermissionDenied(false);
      setIsEnabled(true);
      startAnalyser(stream);
    } catch {
      setPermissionDenied(true);
      setIsEnabled(false);
    }
  }, [startAnalyser]);

  const startRecording = useCallback(() => {
    if (!isEnabled) {
      return;
    }
    setIsRecording(true);
  }, [isEnabled]);

  const stopRecording = useCallback(() => {
    setIsRecording(false);
  }, []);

  useEffect(() => {
    return () => {
      disable();
    };
  }, [disable]);

  return {
    isEnabled,
    isRecording,
    permissionDenied,
    level,
    enable,
    startRecording,
    stopRecording,
    disable,
  };
}
