"use client";

import { useEffect, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

import type { InterviewerState } from "@/types/websocket";

const TEAL = new THREE.Color("#14b8a6");
const CYAN = new THREE.Color("#22d3ee");

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return reduced;
}

function stateColor(state: InterviewerState, isRecording: boolean): THREE.Color {
  if (state === "speaking") return TEAL;
  if (state === "listening" || isRecording) return CYAN;
  if (state === "processing" || state === "thinking") return new THREE.Color("#64748b");
  return new THREE.Color("#94a3b8");
}

function AudioPresenceHost({
  state,
  audioLevel,
  isRecording,
  frozen,
}: {
  state: InterviewerState;
  audioLevel: number;
  isRecording: boolean;
  frozen: boolean;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const leftEyeRef = useRef<THREE.Mesh>(null);
  const rightEyeRef = useRef<THREE.Mesh>(null);
  const ring1Ref = useRef<THREE.Mesh>(null);
  const ring2Ref = useRef<THREE.Mesh>(null);
  const ring3Ref = useRef<THREE.Mesh>(null);

  const isSpeaking = state === "speaking";
  const isListening = state === "listening" || isRecording;
  const isProcessing = state === "processing" || state === "thinking";
  const accent = stateColor(state, isRecording);

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();
    const level = Math.min(1, audioLevel * 1.2 + 0.05);
    const pulse = 1 + Math.sin(t * (isSpeaking ? 4 : 2)) * 0.04 * (0.3 + level);

    if (groupRef.current) {
      groupRef.current.rotation.y = isProcessing ? t * 0.4 : Math.sin(t * 0.3) * 0.08;
    }

    if (headRef.current) {
      headRef.current.scale.setScalar(pulse);
      const material = headRef.current.material as THREE.MeshStandardMaterial;
      material.emissive.copy(accent);
      material.emissiveIntensity = isSpeaking ? 0.9 + level * 0.5 : isListening ? 0.6 + level * 0.4 : 0.35;
    }

    if (glowRef.current) {
      glowRef.current.scale.setScalar(pulse * 1.35);
      const material = glowRef.current.material as THREE.MeshBasicMaterial;
      material.opacity = isSpeaking ? 0.18 + level * 0.12 : isListening ? 0.14 + level * 0.1 : 0.08;
    }

    const eyeIntensity = isListening ? 1.2 + level : isSpeaking ? 0.9 + level * 0.5 : 0.4;
    [leftEyeRef, rightEyeRef].forEach((ref) => {
      if (!ref.current) return;
      const material = ref.current.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = eyeIntensity;
    });

    const rings = [ring1Ref, ring2Ref, ring3Ref];
    rings.forEach((ref, i) => {
      if (!ref.current) return;
      const base = 0.55 + i * 0.12;
      const expand = isSpeaking ? level * 0.15 : isListening ? -level * 0.05 : 0;
      const scale = base + expand + Math.sin(t * 2 + i) * 0.02;
      ref.current.scale.set(scale, scale, scale);
      ref.current.rotation.x = Math.PI / 2 + Math.sin(t + i) * 0.1;
      ref.current.rotation.z = t * (0.3 + i * 0.15);
      const material = ref.current.material as THREE.MeshBasicMaterial;
      material.opacity = isSpeaking ? 0.35 + level * 0.3 : isListening ? 0.25 + level * 0.2 : 0.12;
    });
  });

  return (
    <group ref={groupRef} position={[0, -0.15, 0]}>
      <ambientLight intensity={0.45} />
      <pointLight position={[2, 2, 3]} intensity={1.5} color="#22d3ee" />
      <pointLight position={[-2, 0, 2]} intensity={0.8} color="#14b8a6" />

      {/* Shoulders / bust base */}
      <mesh position={[0, -0.55, 0]} rotation={[0.1, 0, 0]}>
        <cylinderGeometry args={[0.55, 0.75, 0.5, 32]} />
        <meshStandardMaterial color="#1e293b" metalness={0.5} roughness={0.6} />
      </mesh>
      <mesh position={[0, -0.35, 0]}>
        <sphereGeometry args={[0.42, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial color="#334155" metalness={0.4} roughness={0.5} />
      </mesh>

      {/* Head */}
      <mesh ref={headRef} position={[0, 0.15, 0]}>
        <icosahedronGeometry args={[0.38, 2]} />
        <meshStandardMaterial color="#475569" emissive={TEAL} emissiveIntensity={0.35} metalness={0.55} roughness={0.35} />
      </mesh>
      <mesh ref={glowRef} position={[0, 0.15, 0]}>
        <sphereGeometry args={[0.38, 24, 24]} />
        <meshBasicMaterial color={CYAN} transparent opacity={0.1} />
      </mesh>

      {/* Eyes */}
      <mesh ref={leftEyeRef} position={[-0.13, 0.22, 0.3]}>
        <sphereGeometry args={[0.045, 12, 12]} />
        <meshStandardMaterial color="#0f172a" emissive={CYAN} emissiveIntensity={0.5} />
      </mesh>
      <mesh ref={rightEyeRef} position={[0.13, 0.22, 0.3]}>
        <sphereGeometry args={[0.045, 12, 12]} />
        <meshStandardMaterial color="#0f172a" emissive={CYAN} emissiveIntensity={0.5} />
      </mesh>

      {/* Audio presence rings */}
      <mesh ref={ring1Ref}>
        <torusGeometry args={[0.5, 0.012, 12, 48]} />
        <meshBasicMaterial color={TEAL} transparent opacity={0.2} />
      </mesh>
      <mesh ref={ring2Ref}>
        <torusGeometry args={[0.5, 0.01, 12, 48]} />
        <meshBasicMaterial color={CYAN} transparent opacity={0.15} />
      </mesh>
      <mesh ref={ring3Ref}>
        <torusGeometry args={[0.5, 0.008, 12, 48]} />
        <meshBasicMaterial color={TEAL} transparent opacity={0.1} />
      </mesh>
    </group>
  );
}

export function InterviewerCharacter3D({
  state,
  audioLevel,
  isRecording,
  className,
}: {
  state: InterviewerState;
  audioLevel: number;
  isRecording: boolean;
  className?: string;
}) {
  const reducedMotion = usePrefersReducedMotion();

  return (
    <div className={className} aria-hidden>
      <Canvas
        className="pointer-events-none h-full w-full"
        camera={{ position: [0, 0.1, 2.2], fov: 38 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <fog attach="fog" args={["#0f172a", 2, 6]} />
        <AudioPresenceHost
          state={state}
          audioLevel={audioLevel}
          isRecording={isRecording}
          frozen={reducedMotion}
        />
      </Canvas>
    </div>
  );
}
