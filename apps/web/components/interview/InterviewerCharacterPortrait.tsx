"use client";



import Image from "next/image";



import type { InterviewerState } from "@/types/websocket";

import { cn } from "@/lib/format";



const RING_SIZES = ["96%", "78%", "60%"] as const;

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

}: {

  state: InterviewerState;

  audioLevel: number;

  isRecording: boolean;

  className?: string;

}) {

  const isSpeaking = state === "speaking";

  const isListening = state === "listening" || isRecording;

  const isProcessing = state === "processing" || state === "thinking";

  const isActive = isSpeaking || isListening || isProcessing;



  const glowScale = 1 + Math.min(0.1, audioLevel * 0.12);

  const accent = isSpeaking ? "teal" : isListening ? "cyan" : "slate";



  return (

    <div className={cn("relative h-full w-full overflow-hidden", className)} aria-hidden>

      {/* Booth backdrop */}

      <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-[#0a1628] to-slate-950" />



      {/* Vertical light bars — sci-fi booth accents */}

      <div className="absolute inset-y-0 left-[5%] w-px bg-gradient-to-b from-transparent via-teal-400/25 to-transparent" />

      <div className="absolute inset-y-0 right-[5%] w-px bg-gradient-to-b from-transparent via-cyan-400/20 to-transparent" />



      {/* Unified stage — character + portal rings share the same coordinate space */}

      <div

        className={cn(

          "absolute inset-x-[2%] bottom-[3%] top-[1%] transition-transform duration-500 sm:inset-x-[3%] sm:bottom-[4%]",

          isSpeaking && "scale-[1.012]",

          isListening && "scale-[1.006]",

        )}

      >

        {/* Portal glow aligned with rings in the portrait */}

        <div

          className={cn(

            "absolute inset-0 transition-opacity duration-500",

            isSpeaking && "opacity-100",

            isListening && "opacity-95",

            !isActive && "opacity-75",

          )}

          style={{

            background: `

              radial-gradient(circle at 50% ${RING_CENTER_Y}, rgba(20,184,166,0.24) 0%, transparent 46%),

              radial-gradient(circle at 50% ${RING_CENTER_Y}, rgba(34,211,238,0.14) 0%, transparent 62%)

            `,

          }}

        />



        {/* Concentric rings — sized to match the portrait's built-in portal */}

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



        {/* Character portrait */}

        <div

          className={cn(

            "relative z-10 h-full w-full transition-all duration-500",

            accent === "teal" && "drop-shadow-[0_0_32px_rgba(20,184,166,0.3)]",

            accent === "cyan" && "drop-shadow-[0_0_32px_rgba(34,211,238,0.26)]",

          )}

        >

          <Image

            src="/interviewer-portrait.png"

            alt=""

            fill

            priority

            sizes="(max-width: 768px) 92vw, 640px"

            className="object-contain object-center"

          />

          {/* Subtle teal grade — keeps palette without hiding image rings */}

          <div

            className="pointer-events-none absolute inset-0 mix-blend-color opacity-[0.18]"

            style={{

              background:

                "linear-gradient(180deg, rgba(20,184,166,0.4) 0%, rgba(10,22,40,0.1) 50%, rgba(34,211,238,0.25) 100%)",

            }}

          />

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[12%] bg-gradient-to-t from-[#0a1628]/90 via-transparent to-transparent" />

        </div>

      </div>



      {/* Floor glow */}

      <div

        className={cn(

          "absolute inset-x-[12%] bottom-0 h-20 rounded-full blur-2xl transition-opacity duration-500",

          isActive ? "opacity-75" : "opacity-45",

        )}

        style={{

          background: isSpeaking

            ? "radial-gradient(ellipse, rgba(20,184,166,0.5) 0%, transparent 70%)"

            : isListening

              ? "radial-gradient(ellipse, rgba(34,211,238,0.42) 0%, transparent 70%)"

              : "radial-gradient(ellipse, rgba(20,184,166,0.22) 0%, transparent 70%)",

        }}

      />

    </div>

  );

}


