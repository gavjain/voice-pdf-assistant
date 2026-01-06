import { Lock, Shield } from "lucide-react"

export function TrustIndicators() {
  return (
    <section className="py-16 px-4 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-8 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            <span>Files deleted after processing</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            <span>No login required</span>
          </div>
        </div>
      </div>
    </section>
  )
}
