"use client";

import { Float, Html, Sparkles } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";

import { CYAN, DEEP_BG, TEAL, lerpAccent } from "@/components/visuals/scene-theme";
import { usePrefersReducedMotion } from "@/components/visuals/usePrefersReducedMotion";
import { cn } from "@/lib/format";

const SPECTRUM_BARS = 48;

function seededUnit(seed: number) {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

function usePointerParallax() {
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  return {
    pointer,
    onPointerMove: (event: React.PointerEvent<HTMLDivElement>) => {
      const rect = event.currentTarget.getBoundingClientRect();
      setPointer({
        x: ((event.clientX - rect.left) / rect.width - 0.5) * 2,
        y: ((event.clientY - rect.top) / rect.height - 0.5) * 2,
      });
    },
    onPointerLeave: () => setPointer({ x: 0, y: 0 }),
  };
}

function InterviewCore({ frozen, pointer }: { frozen: boolean; pointer: { x: number; y: number } }) {
  const groupRef = useRef<THREE.Group>(null);
  const coreRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();
    const pulse = 1 + Math.sin(t * 2.2) * 0.06;

    if (groupRef.current) {
      groupRef.current.rotation.y = pointer.x * 0.18 + t * 0.12;
      groupRef.current.rotation.x = pointer.y * -0.1 + Math.sin(t * 0.4) * 0.06;
    }
    if (coreRef.current) {
      coreRef.current.scale.setScalar(pulse);
      coreRef.current.rotation.y = t * 0.35;
    }
    if (glowRef.current) {
      glowRef.current.scale.setScalar(pulse * 1.55);
    }
    if (innerRef.current) {
      innerRef.current.rotation.x = t * 0.5;
      innerRef.current.rotation.z = t * 0.3;
    }
  });

  return (
    <group ref={groupRef}>
      <Float speed={1.4} rotationIntensity={0.15} floatIntensity={0.35} floatingRange={[-0.08, 0.08]}>
        <mesh ref={coreRef}>
          <icosahedronGeometry args={[0.72, 2]} />
          <meshStandardMaterial
            color={DEEP_BG}
            emissive="#14b8a6"
            emissiveIntensity={2.2}
            metalness={0.85}
            roughness={0.18}
          />
        </mesh>
        <mesh ref={innerRef}>
          <octahedronGeometry args={[0.38, 0]} />
          <meshStandardMaterial
            color="#22d3ee"
            emissive="#22d3ee"
            emissiveIntensity={1.4}
            wireframe
            transparent
            opacity={0.55}
          />
        </mesh>
        <mesh ref={glowRef}>
          <sphereGeometry args={[0.72, 32, 32]} />
          <meshBasicMaterial color="#22d3ee" transparent opacity={0.1} />
        </mesh>
        <Html center transform distanceFactor={2.2} style={{ pointerEvents: "none" }}>
          <div className="select-none bg-gradient-to-b from-white to-cyan-200 bg-clip-text text-4xl font-bold tracking-[0.2em] text-transparent drop-shadow-[0_0_24px_rgba(34,211,238,0.8)]">
            AI
          </div>
        </Html>
      </Float>
    </group>
  );
}

function AgentOrbitRing({
  frozen,
  radius,
  tilt,
  speed,
  offset,
  nodeCount,
}: {
  frozen: boolean;
  radius: number;
  tilt: number;
  speed: number;
  offset: number;
  nodeCount: number;
}) {
  const ringRef = useRef<THREE.Group>(null);

  const nodes = useMemo(
    () =>
      Array.from({ length: nodeCount }, (_, i) => ({
        angle: (i / nodeCount) * Math.PI * 2,
        size: 0.06 + seededUnit(i * 11 + offset) * 0.04,
        mix: i / nodeCount,
      })),
    [nodeCount, offset],
  );

  useFrame(({ clock }) => {
    if (frozen || !ringRef.current) return;
    ringRef.current.rotation.y = clock.getElapsedTime() * speed + offset;
  });

  return (
    <group rotation={[tilt, 0, 0]}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.012, 8, 96]} />
        <meshBasicMaterial color="#14b8a6" transparent opacity={0.35} />
      </mesh>
      <group ref={ringRef}>
        {nodes.map(({ angle, size, mix }, i) => {
          const color = lerpAccent(mix);
          return (
            <mesh
              key={i}
              position={[Math.cos(angle) * radius, 0, Math.sin(angle) * radius]}
            >
              <sphereGeometry args={[size, 16, 16]} />
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={0.9}
                metalness={0.5}
                roughness={0.3}
              />
            </mesh>
          );
        })}
      </group>
    </group>
  );
}

function VoiceSpectrumRing({ frozen }: { frozen: boolean }) {
  const groupRef = useRef<THREE.Group>(null);

  const bars = useMemo(
    () =>
      Array.from({ length: SPECTRUM_BARS }, (_, i) => ({
        angle: (i / SPECTRUM_BARS) * Math.PI * 2,
        phase: (i / SPECTRUM_BARS) * Math.PI * 5,
      })),
    [],
  );

  useFrame(({ clock }) => {
    if (frozen || !groupRef.current) return;
    const t = clock.getElapsedTime();
    groupRef.current.rotation.y = t * 0.08;

    groupRef.current.children.forEach((child, i) => {
      const mesh = child as THREE.Mesh;
      const { angle, phase } = bars[i];
      const height =
        0.12 +
        (Math.sin(t * 3.2 + phase) * 0.5 + 0.5) * 0.75 +
        (Math.sin(t * 6.4 + phase * 1.7) * 0.5 + 0.5) * 0.28;
      mesh.scale.y = height;
      mesh.position.y = height / 2 - 0.4;
      const r = 2.05 + Math.sin(t * 0.5 + phase) * 0.06;
      mesh.position.x = Math.cos(angle) * r;
      mesh.position.z = Math.sin(angle) * r;
      mesh.rotation.y = -angle;
    });
  });

  return (
    <group ref={groupRef} rotation={[0.42, 0, 0]}>
      {bars.map(({ angle }, i) => (
        <mesh
          key={i}
          position={[Math.cos(angle) * 2.05, 0, Math.sin(angle) * 2.05]}
          rotation={[0, -angle, 0]}
        >
          <boxGeometry args={[0.045, 1, 0.045]} />
          <meshStandardMaterial
            color={i % 2 === 0 ? "#14b8a6" : "#22d3ee"}
            emissive={i % 2 === 0 ? "#14b8a6" : "#22d3ee"}
            emissiveIntensity={0.45}
            transparent
            opacity={0.8}
          />
        </mesh>
      ))}
    </group>
  );
}

function PortalFloor({ frozen }: { frozen: boolean }) {
  const rings = useRef<(THREE.Mesh | null)[]>([]);

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();
    rings.current.forEach((ring, i) => {
      if (!ring) return;
      const cycle = ((t * 0.28 + i * 0.33) % 1);
      ring.scale.setScalar(1 + cycle * 3.2);
      (ring.material as THREE.MeshBasicMaterial).opacity = (1 - cycle) * 0.18;
    });
  });

  return (
    <group position={[0, -1.15, 0]} rotation={[Math.PI / 2, 0, 0]}>
      <mesh>
        <circleGeometry args={[1.1, 64]} />
        <meshBasicMaterial color="#14b8a6" transparent opacity={0.12} />
      </mesh>
      {[0, 1, 2].map((i) => (
        <mesh
          key={i}
          ref={(el) => {
            rings.current[i] = el;
          }}
        >
          <ringGeometry args={[0.85, 1, 64]} />
          <meshBasicMaterial color="#22d3ee" transparent opacity={0.15} side={THREE.DoubleSide} />
        </mesh>
      ))}
    </group>
  );
}

function DataParticles({ frozen }: { frozen: boolean }) {
  const pointsRef = useRef<THREE.Points>(null);
  const count = 900;

  const { positions, colors } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      const theta = seededUnit(i * 3 + 1) * Math.PI * 2;
      const phi = seededUnit(i * 3 + 2) * Math.PI;
      const r = 1.8 + seededUnit(i * 3 + 3) * 2.2;
      positions[i * 3] = Math.sin(phi) * Math.cos(theta) * r;
      positions[i * 3 + 1] = (seededUnit(i * 5 + 4) - 0.5) * 2.5;
      positions[i * 3 + 2] = Math.sin(phi) * Math.sin(theta) * r;
      const c = lerpAccent(seededUnit(i * 7 + 5));
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }
    return { positions, colors };
  }, []);

  useFrame(({ clock }) => {
    if (frozen || !pointsRef.current) return;
    pointsRef.current.rotation.y = clock.getElapsedTime() * 0.04;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.028}
        vertexColors
        transparent
        opacity={0.65}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}

function SceneContent({
  frozen,
  pointer,
}: {
  frozen: boolean;
  pointer: { x: number; y: number };
}) {
  return (
    <>
      <fog attach="fog" args={[DEEP_BG, 8, 22]} />
      <ambientLight intensity={0.35} />
      <pointLight position={[4, 5, 6]} intensity={2.4} color={CYAN} />
      <pointLight position={[-5, -2, 4]} intensity={1.6} color={TEAL} />
      <spotLight position={[0, 6, 2]} intensity={1.2} angle={0.5} penumbra={0.8} color="#22d3ee" />

      <InterviewCore frozen={frozen} pointer={pointer} />
      <AgentOrbitRing frozen={frozen} radius={1.35} tilt={0.55} speed={0.35} offset={0} nodeCount={4} />
      <AgentOrbitRing frozen={frozen} radius={1.75} tilt={0.35} speed={-0.22} offset={1.2} nodeCount={4} />
      <VoiceSpectrumRing frozen={frozen} />
      <PortalFloor frozen={frozen} />
      <DataParticles frozen={frozen} />

      {!frozen ? (
        <Sparkles count={120} scale={5} size={2.5} speed={0.35} color="#22d3ee" opacity={0.55} />
      ) : null}
    </>
  );
}

export function HeroInterviewScene({ className }: { className?: string }) {
  const reducedMotion = usePrefersReducedMotion();
  const { pointer, onPointerMove, onPointerLeave } = usePointerParallax();

  return (
    <div
      className={cn("relative h-full min-h-[320px] w-full", className)}
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
      aria-hidden
    >
      <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-teal-500/5 via-transparent to-cyan-500/5" />
      <Canvas
        className="!absolute inset-0 rounded-3xl"
        camera={{ position: [0, 0.2, 5.8], fov: 38 }}
        dpr={[1, 1.75]}
        frameloop={reducedMotion ? "demand" : "always"}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <SceneContent frozen={reducedMotion} pointer={pointer} />
      </Canvas>
      <div className="pointer-events-none absolute inset-0 rounded-3xl ring-1 ring-inset ring-white/10 shadow-[0_0_80px_rgba(20,184,166,0.15)]" />
    </div>
  );
}
