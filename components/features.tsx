import { FileText, Wand2, Zap } from "lucide-react"

const features = [
  {
    icon: Wand2,
    title: "Voice-Controlled",
    description: "Simply speak your command. No buttons, no menus, no complexity.",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Get results in seconds. Faster than traditional PDF tools.",
  },
  {
    icon: FileText,
    title: "Intent-Based",
    description: "Say what you want, not how to do it. We handle the rest.",
  },
]

export function Features() {
  return (
    <section className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div key={feature.title} className="text-center space-y-4">
                <div className="flex justify-center">
                  <div className="rounded-2xl bg-primary/10 p-4">
                    <Icon className="h-8 w-8 text-primary" />
                  </div>
                </div>
                <h3 className="text-xl font-semibold">{feature.title}</h3>
                <p className="text-muted-foreground text-balance">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
