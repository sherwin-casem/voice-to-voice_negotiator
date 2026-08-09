"use client";

import Image from "next/image";

import type { InterviewerState } from "@/types/websocket";
import { cn } from "@/lib/format";
import { INTERVIEWER_PORTRAIT, staticAssetUrl } from "@/lib/static-assets";

const portraitSrc = staticAssetUrl(INTERVIEWER_PORTRAIT.path, INTERVIEWER_PORTRAIT.version);

const RING_SIZES = ["88%", "70%", "52%"] as const;
const RING_CENTER_Y = "54%";

function portalRingClass(index: number, isActive: boolean) {
  return cn(
    "absolute left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border",
    "transition-all duration-500",
    isActive ? "border-teal-400/45 shadow-[0_0_28px_rgba(20,184,166,0.22)]" : "border-teal-500/18",
    index === 0 && "animate-[portal-pulse_4s_ease-in-out_infinite]",
    index === 1 && "animate-[portal-pulse_4s_ease-in-out_infinite_0.6s]",
    index === 2 && "animate-[portal-pulse_4s_ease-in-out_infinite_1.2s]",
  );
}

export function InterviewerCharacterPortrait({
  state,
  audioLevel,
  isRecording,
  className,
  fillFrame = false,
}: {
  state: InterviewerState;
  audioLevel: number;
  isRecording: boolean;
  className?: string;
  /** Fit the full character into the stage (slight zoom-out for wide frames). */
  fillFrame?: boolean;
}) {
  const isSpeaking = state === "speaking";
  const isListening = state === "listening" || isRecording;
  const isProcessing = state === "processing" || state === "thinking";
  const isActive = isSpeaking || isListening || isProcessing;

  const glowScale = 1 + Math.min(0.1, audioLevel * 0.12);
  const accent = isSpeaking ? "teal" : isListening ? "cyan" : "slate";

  return (
    <div className={cn("relative h-full w-full overflow-hidden", className)} aria-hidden>
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-[#0a1628] to-slate-950" />

      <div className="absolute inset-y-0 left-[4%] w-px bg-gradient-to-b from-transparent via-teal-400/25 to-transparent" />
      <div className="absolute inset-y-0 right-[4%] w-px bg-gradient-to-b from-transparent via-cyan-400/20 to-transparent" />

      <div
        className={cn(
          "absolute inset-0 transition-transform duration-500",
          isSpeaking && "scale-[1.015]",
          isListening && "scale-[1.008]",
        )}
      >
        <div
          className={cn(
            "absolute inset-0 transition-opacity duration-500",
            isSpeaking && "opacity-100",
            isListening && "opacity-95",
            !isActive && "opacity-70",
          )}
          style={{
            background: `
              radial-gradient(circle at 50% ${RING_CENTER_Y}, rgba(20,184,166,0.22) 0%, transparent 46%),
              radial-gradient(circle at 50% ${RING_CENTER_Y}, rgba(34,211,238,0.12) 0%, transparent 62%)
            `,
          }}
        />

        {RING_SIZES.map((size, index) => (
          <div
            key={index}
            className={portalRingClass(index, isActive)}
            style={{
              top: RING_CENTER_Y,
              width: size,
              height: size,
              transform: `translate(-50%, -50%) scale(${isActive ? glowScale + index * 0.015 : 1})`,
            }}
          />
        ))}

        <div
          className={cn(
            "relative z-10 h-full w-full transition-all duration-500",
            accent === "teal" && "drop-shadow-[0_0_32px_rgba(20,184,166,0.28)]",
            accent === "cyan" && "drop-shadow-[0_0_32px_rgba(34,211,238,0.24)]",
          )}
        >
          <Image
            key={portraitSrc}
            src={portraitSrc}
            alt=""
            fill
            priority
            unoptimized
            sizes="(max-width: 768px) 100vw, 720px"
            className={cn(
              // Keep the full bust + portal in frame; cover+face-crop was over-zooming.
              fillFrame
                ? "object-contain object-[center_58%] scale-[0.92]"
                : "object-contain object-center",
            )}
          />

          <div
            className="pointer-events-none absolute inset-0 mix-blend-color opacity-[0.14]"
            style={{
              background:
                "linear-gradient(180deg, rgba(20,184,166,0.35) 0%, rgba(10,22,40,0.08) 50%, rgba(34,211,238,0.22) 100%)",
            }}
          />
        </div>
      </div>

      <div
        className={cn(
          "absolute inset-x-[14%] bottom-0 h-16 rounded-full blur-2xl transition-opacity duration-500",
          isActive ? "opacity-70" : "opacity-40",
        )}
        style={{
          background: isSpeaking
            ? "radial-gradient(ellipse, rgba(20,184,166,0.45) 0%, transparent 70%)"
            : isListening
              ? "radial-gradient(ellipse, rgba(34,211,238,0.38) 0%, transparent 70%)"
              : "radial-gradient(ellipse, rgba(20,184,166,0.2) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}
