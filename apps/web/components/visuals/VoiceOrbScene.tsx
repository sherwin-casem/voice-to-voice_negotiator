"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

import { CYAN, DEEP_BG, TEAL, lerpAccent } from "@/components/visuals/scene-theme";
import { usePrefersReducedMotion } from "@/components/visuals/usePrefersReducedMotion";
import { cn } from "@/lib/format";

const HALO_COUNT = 340;

/** Deterministic 0–1 value from index — stable across renders (no Math.random in render). */
function seededUnit(seed: number) {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

const ORB_VERTEX_SHADER = /* glsl */ `
  uniform float uTime;
  uniform float uAmplitude;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  varying float vDisplacement;

  // Cheap layered-sine displacement — enough organic motion for a small
  // decorative orb without pulling in a noise library.
  float wave(vec3 p) {
    return
      sin(p.x * 3.1 + uTime * 0.9) * 0.35 +
      sin(p.y * 4.3 + uTime * 1.3) * 0.3 +
      sin((p.z + p.x) * 2.7 + uTime * 0.7) * 0.35;
  }

  void main() {
    float displacement = wave(normal * 2.0) * uAmplitude;
    vec3 displaced = position + normal * displacement;
    vDisplacement = displacement;
    vNormal = normalize(normalMatrix * normal);
    vec4 mvPosition = modelViewMatrix * vec4(displaced, 1.0);
    vViewDir = normalize(-mvPosition.xyz);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const ORB_FRAGMENT_SHADER = /* glsl */ `
  uniform vec3 uColorA;
  uniform vec3 uColorB;
  uniform vec3 uBase;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  varying float vDisplacement;

  void main() {
    float fresnel = pow(1.0 - clamp(dot(vNormal, vViewDir), 0.0, 1.0), 2.2);
    vec3 rim = mix(uColorA, uColorB, clamp(vDisplacement * 4.0 + 0.5, 0.0, 1.0));
    vec3 color = mix(uBase, rim, fresnel * 1.4 + 0.08);
    gl_FragColor = vec4(color, 0.55 + fresnel * 0.45);
  }
`;

function ShaderOrb({ frozen }: { frozen: boolean }) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const meshRef = useRef<THREE.Mesh>(null);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uAmplitude: { value: 0.09 },
      uColorA: { value: TEAL.clone() },
      uColorB: { value: CYAN.clone() },
      uBase: { value: new THREE.Color(DEEP_BG) },
    }),
    [],
  );

  useFrame(({ clock }) => {
    if (frozen) return;
    const t = clock.getElapsedTime();
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = t;
    }
    if (meshRef.current) {
      meshRef.current.rotation.y = t * 0.18;
      meshRef.current.rotation.x = Math.sin(t * 0.25) * 0.12;
    }
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1.15, 48]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        vertexShader={ORB_VERTEX_SHADER}
        fragmentShader={ORB_FRAGMENT_SHADER}
        transparent
        depthWrite={false}
      />
    </mesh>
  );
}

function ParticleHalo({ frozen }: { frozen: boolean }) {
  const pointsRef = useRef<THREE.Points>(null);

  const { positions, colors, seeds } = useMemo(() => {
    const positions = new Float32Array(HALO_COUNT * 3);
    const colors = new Float32Array(HALO_COUNT * 3);
    const seeds = new Float32Array(HALO_COUNT * 3);

    for (let i = 0; i < HALO_COUNT; i += 1) {
      const angle = seededUnit(i * 3 + 1) * Math.PI * 2;
      const radius = 1.7 + seededUnit(i * 3 + 2) * 0.9;
      seeds[i * 3] = angle;
      seeds[i * 3 + 1] = radius;
      seeds[i * 3 + 2] = 0.15 + seededUnit(i * 3 + 3) * 0.5;

      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = (seededUnit(i * 5 + 4) - 0.5) * 0.5;
      positions[i * 3 + 2] = Math.sin(angle) * radius;

      const color = lerpAccent(seededUnit(i * 7 + 5));
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

    for (let i = 0; i < HALO_COUNT; i += 1) {
      const angle = seeds[i * 3] + t * seeds[i * 3 + 2];
      const radius = seeds[i * 3 + 1];
      arr[i * 3] = Math.cos(angle) * radius;
      arr[i * 3 + 1] = Math.sin(t * 0.8 + seeds[i * 3] * 3.0) * 0.22;
      arr[i * 3 + 2] = Math.sin(angle) * radius;
    }

    attr.needsUpdate = true;
    pointsRef.current.rotation.x = 0.5 + Math.sin(t * 0.3) * 0.08;
  });

  return (
    <points ref={pointsRef} rotation={[0.5, 0, 0]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.035}
        vertexColors
        transparent
        opacity={0.85}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}

/**
 * Compact, self-contained animated 3D "voice orb": a shader-displaced
 * fresnel sphere with an orbiting particle halo. Sized by its parent —
 * intended as decorative art on auth pages and small hero slots.
 * Freezes on `prefers-reduced-motion` and stays transparent over the
 * app's navy background.
 */
export function VoiceOrbScene({ className }: { className?: string }) {
  const reducedMotion = usePrefersReducedMotion();

  return (
    <div className={cn("pointer-events-none relative", className)} aria-hidden>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(20,184,166,0.16),transparent_65%)]" />
      <Canvas
        className="!absolute inset-0"
        camera={{ position: [0, 0, 4.4], fov: 42 }}
        dpr={[1, 1.5]}
        frameloop={reducedMotion ? "demand" : "always"}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[3, 3, 4]} intensity={1.6} color={CYAN} />
        <pointLight position={[-3, -2, 3]} intensity={1.1} color={TEAL} />
        <ShaderOrb frozen={reducedMotion} />
        <ParticleHalo frozen={reducedMotion} />
      </Canvas>
    </div>
  );
}
