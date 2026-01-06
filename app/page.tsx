import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { TrustIndicators } from "@/components/trust-indicators"

export default function Page() {
  return (
    <main className="min-h-screen">
      <Hero />
      <Features />
      <TrustIndicators />
    </main>
  )
}
