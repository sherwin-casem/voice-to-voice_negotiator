"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

import { CYAN, TEAL } from "@/components/visuals/scene-theme";
import { usePrefersReducedMotion } from "@/components/visuals/usePrefersReducedMotion";

const PARTICLE_COUNT = 1800;
const STREAM_COUNT = 10;
const BAR_COUNT = 72;

function DialogueCore({ frozen }: { frozen: boolean }) {
  const coreRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();
    const pulse = 1 + Math.sin(t * 2.4) * 0.08;

    if (coreRef.current) {
      coreRef.current.scale.setScalar(pulse);
      coreRef.current.rotation.y = t * 0.35;
      coreRef.current.rotation.x = Math.sin(t * 0.6) * 0.15;
    }
    if (glowRef.current) {
      glowRef.current.scale.setScalar(pulse * 1.6);
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.5;
      ringRef.current.rotation.x = Math.PI / 2 + Math.sin(t * 0.8) * 0.12;
    }
  });

  return (
    <group>
      <mesh ref={coreRef}>
        <icosahedronGeometry args={[0.55, 1]} />
        <meshStandardMaterial
          color="#0a1628"
          emissive="#14b8a6"
          emissiveIntensity={1.8}
          metalness={0.6}
          roughness={0.25}
        />
      </mesh>
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.55, 32, 32]} />
        <meshBasicMaterial color="#22d3ee" transparent opacity={0.12} />
      </mesh>
      <mesh ref={ringRef}>
        <torusGeometry args={[0.85, 0.025, 16, 64]} />
        <meshBasicMaterial color="#14b8a6" transparent opacity={0.45} />
      </mesh>
    </group>
  );
}

function AudioPourParticles({ frozen }: { frozen: boolean }) {
  const pointsRef = useRef<THREE.Points>(null);
  const materialRef = useRef<THREE.PointsMaterial>(null);

  const { positions, colors, seeds } = useMemo(() => {
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    const colors = new Float32Array(PARTICLE_COUNT * 3);
    const seeds = new Float32Array(PARTICLE_COUNT * 4);

    for (let i = 0; i < PARTICLE_COUNT; i += 1) {
      const stream = i % STREAM_COUNT;
      const offset = Math.random();
      seeds[i * 4] = stream;
      seeds[i * 4 + 1] = offset;
      seeds[i * 4 + 2] = 0.4 + Math.random() * 0.9;
      seeds[i * 4 + 3] = Math.random() * Math.PI * 2;

      positions[i * 3] = 0;
      positions[i * 3 + 1] = 0;
      positions[i * 3 + 2] = 0;

      const mix = stream / STREAM_COUNT;
      const color = TEAL.clone().lerp(CYAN, mix);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    return { positions, colors, seeds };
  }, []);

  useFrame(({ clock }) => {
    if (frozen || !pointsRef.current) return;

    const t = clock.getElapsedTime();
    const attr = pointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = attr.array as Float32Array;

    for (let i = 0; i < PARTICLE_COUNT; i += 1) {
      const stream = seeds[i * 4];
      const offset = seeds[i * 4 + 1];
      const speed = seeds[i * 4 + 2];
      const phase = seeds[i * 4 + 3];

      const life = ((t * speed * 0.22 + offset) % 1);
      const streamAngle = (stream / STREAM_COUNT) * Math.PI * 2;
      const pourAngle = streamAngle + Math.sin(t * 0.4 + phase) * 0.35;

      const radius = life * 5.5;
      const lift = Math.sin(life * Math.PI) * 1.2;
      const wave = Math.sin(life * 12 + t * 3 + phase) * 0.35 * (1 - life);
      const gravity = -life * life * 2.2;

      arr[i * 3] = Math.cos(pourAngle) * radius + wave * Math.cos(pourAngle + Math.PI / 2);
      arr[i * 3 + 1] = lift + gravity + Math.sin(t * 2 + phase) * 0.08;
      arr[i * 3 + 2] = Math.sin(pourAngle) * radius + wave * Math.sin(pourAngle + Math.PI / 2);
    }

    attr.needsUpdate = true;

    if (materialRef.current) {
      materialRef.current.opacity = 0.55 + Math.sin(t * 1.5) * 0.1;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        ref={materialRef}
        size={0.045}
        vertexColors
        transparent
        opacity={0.6}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}

function SpectralRing({ frozen }: { frozen: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const bars = useMemo(
    () =>
      Array.from({ length: BAR_COUNT }, (_, i) => ({
        angle: (i / BAR_COUNT) * Math.PI * 2,
        phase: (i / BAR_COUNT) * Math.PI * 4,
      })),
    [],
  );

  useFrame(({ clock }) => {
    if (frozen || !groupRef.current) return;
    const t = clock.getElapsedTime();
    groupRef.current.rotation.y = t * 0.12;

    groupRef.current.children.forEach((child, i) => {
      const mesh = child as THREE.Mesh;
      const { angle, phase } = bars[i];
      const height =
        0.15 +
        (Math.sin(t * 2.8 + phase) * 0.5 + 0.5) * 0.9 +
        (Math.sin(t * 5.1 + phase * 2) * 0.5 + 0.5) * 0.35;
      mesh.scale.y = height;
      mesh.position.y = height / 2 - 0.5;
      const radius = 3.2 + Math.sin(t * 0.6 + phase) * 0.08;
      mesh.position.x = Math.cos(angle) * radius;
      mesh.position.z = Math.sin(angle) * radius;
      mesh.rotation.y = -angle;
    });
  });

  return (
    <group ref={groupRef} rotation={[0.35, 0, 0]}>
      {bars.map(({ angle }, i) => (
        <mesh key={i} position={[Math.cos(angle) * 3.2, 0, Math.sin(angle) * 3.2]} rotation={[0, -angle, 0]}>
          <boxGeometry args={[0.06, 1, 0.06]} />
          <meshStandardMaterial
            color={i % 2 === 0 ? "#14b8a6" : "#22d3ee"}
            emissive={i % 2 === 0 ? "#14b8a6" : "#22d3ee"}
            emissiveIntensity={0.35}
            metalness={0.4}
            roughness={0.4}
            transparent
            opacity={0.75}
          />
        </mesh>
      ))}
    </group>
  );
}

function RippleWaves({ frozen }: { frozen: boolean }) {
  const rings = useRef<(THREE.Mesh | null)[]>([]);

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();

    rings.current.forEach((ring, i) => {
      if (!ring) return;
      const cycle = ((t * 0.35 + i * 0.33) % 1);
      const scale = 1 + cycle * 4.5;
      ring.scale.set(scale, scale, scale);
      const material = ring.material as THREE.MeshBasicMaterial;
      material.opacity = (1 - cycle) * 0.22;
    });
  });

  return (
    <group rotation={[Math.PI / 2, 0, 0]}>
      {[0, 1, 2].map((i) => (
        <mesh
          key={i}
          ref={(el) => {
            rings.current[i] = el;
          }}
        >
          <ringGeometry args={[0.9, 1, 64]} />
          <meshBasicMaterial color="#22d3ee" transparent opacity={0.15} side={THREE.DoubleSide} />
        </mesh>
      ))}
    </group>
  );
}

function FountainScene({ frozen }: { frozen: boolean }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (frozen || !groupRef.current) return;
    groupRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.15) * 0.25;
  });

  return (
    <>
      <fog attach="fog" args={["#0a1628", 6, 18]} />
      <ambientLight intensity={0.25} />
      <pointLight position={[4, 4, 6]} intensity={2.2} color="#22d3ee" />
      <pointLight position={[-5, -2, 4]} intensity={1.4} color="#14b8a6" />
      <group ref={groupRef} position={[1.8, -0.3, 0]}>
        <DialogueCore frozen={frozen} />
        <AudioPourParticles frozen={frozen} />
        <SpectralRing frozen={frozen} />
        <RippleWaves frozen={frozen} />
      </group>
    </>
  );
}

export function AudioFountainScene() {
  const reducedMotion = usePrefersReducedMotion();
  const sentinelRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(true);

  // The container spans the full page, but the scene is only visible behind
  // the hero. Watch a viewport-height sentinel at the top and stop the render
  // loop once the user scrolls past it, so it doesn't burn GPU further down.
  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => setInView(entries.some((entry) => entry.isIntersecting)),
      { threshold: 0, rootMargin: "25% 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const frozen = reducedMotion || !inView;

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div ref={sentinelRef} className="absolute inset-x-0 top-0 h-screen" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a1628]/30 via-transparent to-[#0a1628]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_70%_45%,rgba(20,184,166,0.14),transparent_65%)]" />
      <Canvas
        className="pointer-events-none !absolute inset-0 h-full w-full"
        camera={{ position: [0, 0.5, 9], fov: 42 }}
        dpr={[1, 1.75]}
        frameloop={frozen ? "demand" : "always"}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <FountainScene frozen={frozen} />
      </Canvas>
      <div className="absolute inset-0 bg-gradient-to-r from-[#0a1628] via-[#0a1628]/70 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#0a1628] to-transparent" />
    </div>
  );
}
