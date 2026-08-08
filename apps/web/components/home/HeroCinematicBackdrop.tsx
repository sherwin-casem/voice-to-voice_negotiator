"use client";

import { useEffect, useRef } from "react";

import { usePrefersReducedMotion } from "@/components/visuals/usePrefersReducedMotion";
import { cn } from "@/lib/format";

/**
 * Canvas-driven cinematic energy field — flowing aurora blobs, light streaks,
 * and a subtle scan grid. Reads like motion graphics / video without a heavy
 * media file. Hero-only backdrop layer.
 */
export function HeroCinematicBackdrop({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    let raf = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio, 2);
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    resize();
    window.addEventListener("resize", resize);

    const blobs = [
      { x: 0.72, y: 0.38, r: 0.42, hue: 174, speed: 0.0008 },
      { x: 0.58, y: 0.52, r: 0.28, hue: 186, speed: 0.0011 },
      { x: 0.82, y: 0.62, r: 0.22, hue: 168, speed: 0.0009 },
    ];

    const draw = () => {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);

      // Deep vignette base
      const base = ctx.createRadialGradient(w * 0.5, h * 0.45, 0, w * 0.5, h * 0.5, w * 0.75);
      base.addColorStop(0, "rgba(10, 22, 40, 0)");
      base.addColorStop(1, "rgba(10, 22, 40, 0.85)");
      ctx.fillStyle = base;
      ctx.fillRect(0, 0, w, h);

      if (!reducedMotion) {
        for (const blob of blobs) {
          const ox = blob.x + Math.sin(frame * blob.speed + blob.hue) * 0.04;
          const oy = blob.y + Math.cos(frame * blob.speed * 1.3) * 0.03;
          const grad = ctx.createRadialGradient(ox * w, oy * h, 0, ox * w, oy * h, blob.r * w);
          grad.addColorStop(0, `hsla(${blob.hue}, 85%, 55%, 0.22)`);
          grad.addColorStop(0.45, `hsla(${blob.hue + 8}, 90%, 50%, 0.08)`);
          grad.addColorStop(1, "transparent");
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, w, h);
        }

        // Horizontal light streaks
        for (let i = 0; i < 5; i += 1) {
          const y = h * (0.25 + i * 0.12) + Math.sin(frame * 0.002 + i) * 12;
          const streak = ctx.createLinearGradient(0, y, w, y);
          streak.addColorStop(0, "transparent");
          streak.addColorStop(0.45, "rgba(34, 211, 238, 0.04)");
          streak.addColorStop(0.55, "rgba(20, 184, 166, 0.06)");
          streak.addColorStop(1, "transparent");
          ctx.strokeStyle = streak;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(w, y + Math.sin(frame * 0.003 + i * 2) * 8);
          ctx.stroke();
        }
      }

      // Perspective grid floor
      ctx.save();
      ctx.globalAlpha = 0.07;
      ctx.strokeStyle = "#22d3ee";
      const horizon = h * 0.72;
      for (let i = -8; i <= 8; i += 1) {
        ctx.beginPath();
        ctx.moveTo(w * 0.5 + i * 18, horizon);
        ctx.lineTo(w * 0.5 + i * 90, h);
        ctx.stroke();
      }
      for (let j = 0; j < 6; j += 1) {
        const y = horizon + j * ((h - horizon) / 6);
        ctx.beginPath();
        ctx.moveTo(w * 0.08, y);
        ctx.lineTo(w * 0.92, y);
        ctx.stroke();
      }
      ctx.restore();

      frame += 1;
      raf = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(raf);
    };
  }, [reducedMotion]);

  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)} aria-hidden>
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#0a1628] via-[#0a1628]/55 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#0a1628] to-transparent" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_90%_70%_at_65%_40%,rgba(20,184,166,0.12),transparent_60%)]" />
    </div>
  );
}
