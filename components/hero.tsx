"use client"

import { VoiceCommandInterface } from "./voice-command-interface"

export function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-4 py-20">
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-background to-background pointer-events-none" />

      <div className="relative z-10 w-full max-w-5xl mx-auto text-center space-y-8">
        {/* Headline */}
        <div className="space-y-4">
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-balance">
            Talk to your PDF. <span className="text-primary">We'll do the rest.</span>
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto text-balance">
            Edit, convert, and extract PDFs using just your voice.
          </p>
        </div>

        {/* Voice Command Interface */}
        <VoiceCommandInterface />
      </div>
    </section>
  )
}
