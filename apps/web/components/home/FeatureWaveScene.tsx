"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { CYAN, DEEP_BG, TEAL } from "@/components/visuals/scene-theme";
import { usePrefersReducedMotion } from "@/components/visuals/usePrefersReducedMotion";
import { cn } from "@/lib/format";

const BAR_COUNT = 32;

function VoiceWaveform({ frozen }: { frozen: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const micRef = useRef<THREE.Group>(null);

  const bars = useMemo(
    () =>
      Array.from({ length: BAR_COUNT }, (_, i) => ({
        x: (i - BAR_COUNT / 2) * 0.14,
        phase: (i / BAR_COUNT) * Math.PI * 3,
      })),
    [],
  );

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();

    if (micRef.current) {
      micRef.current.position.y = Math.sin(t * 1.8) * 0.06;
    }
    if (groupRef.current) {
      groupRef.current.children.forEach((child, i) => {
        const mesh = child as THREE.Mesh;
        const { phase } = bars[i];
        const h =
          0.15 +
          (Math.sin(t * 4 + phase) * 0.5 + 0.5) * 0.9 +
          (Math.sin(t * 7.5 + phase * 2) * 0.5 + 0.5) * 0.35;
        mesh.scale.y = h;
        mesh.position.y = h / 2 - 0.5;
      });
    }
  });

  return (
    <group>
      <group ref={micRef} position={[0, 0.55, 0]}>
        <mesh>
          <capsuleGeometry args={[0.18, 0.55, 8, 16]} />
          <meshStandardMaterial color="#0a1628" emissive="#14b8a6" emissiveIntensity={1.6} metalness={0.7} roughness={0.25} />
        </mesh>
        <mesh position={[0, -0.42, 0]}>
          <torusGeometry args={[0.22, 0.04, 8, 24]} />
          <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={0.8} />
        </mesh>
        <mesh position={[0, -0.62, 0]}>
          <cylinderGeometry args={[0.04, 0.04, 0.35, 12]} />
          <meshStandardMaterial color="#64748b" metalness={0.8} roughness={0.3} />
        </mesh>
      </group>

      <group ref={groupRef} position={[0, -0.15, 0]}>
        {bars.map(({ x }, i) => (
          <mesh key={i} position={[x, 0, 0]}>
            <boxGeometry args={[0.08, 1, 0.08]} />
            <meshStandardMaterial
              color={i % 2 === 0 ? "#14b8a6" : "#22d3ee"}
              emissive={i % 2 === 0 ? "#14b8a6" : "#22d3ee"}
              emissiveIntensity={0.5}
              transparent
              opacity={0.85}
            />
          </mesh>
        ))}
      </group>

      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, -0.95, 0]}>
        <ringGeometry args={[1.2, 1.35, 64]} />
        <meshBasicMaterial color="#22d3ee" transparent opacity={0.2} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/** Compact animated 3D mic + live waveform for the features teaser section. */
export function FeatureWaveScene({ className }: { className?: string }) {
  const reducedMotion = usePrefersReducedMotion();

  return (
    <div className={cn("relative h-[22rem] w-full max-w-sm", className)} aria-hidden>
      <div className="absolute inset-0 rounded-2xl bg-[radial-gradient(circle_at_50%_60%,rgba(20,184,166,0.15),transparent_65%)]" />
      <Canvas
        className="!absolute inset-0"
        camera={{ position: [0, 0.3, 3.8], fov: 42 }}
        dpr={[1, 1.5]}
        frameloop={reducedMotion ? "demand" : "always"}
        gl={{ antialias: true, alpha: true }}
      >
        <fog attach="fog" args={[DEEP_BG, 4, 12]} />
        <ambientLight intensity={0.45} />
        <pointLight position={[2, 3, 4]} intensity={1.8} color={CYAN} />
        <pointLight position={[-2, -1, 3]} intensity={1.2} color={TEAL} />
        <VoiceWaveform frozen={reducedMotion} />
      </Canvas>
    </div>
  );
}
