import type { ReactNode } from "react"
import { IterationProvider } from "@/context/iteration-context"
import { Suspense } from "react"
import { ErrorBoundary } from "react-error-boundary"
import { MainErrorFallback } from "@/components/errors/main"
import { RunProvider, useRunContext } from "@/context/run-context"
import Loading from "@/components/loading"

interface AppProviderProps {
  children: ReactNode
}

export default function AppProvider({ children }: AppProviderProps) {
  return (
    <Suspense fallback={<Loading />}>
      <ErrorBoundary
        FallbackComponent={MainErrorFallback}
        onError={(error, info) => {
          console.error("App error: ", error, info.componentStack)
        }}
      >
        <RunProvider>
          <RunStage>{children}</RunStage>
        </RunProvider>
      </ErrorBoundary>
    </Suspense>
  )
}

// Keyed subtree: iteration state resets when the active run changes.
// Must sit INSIDE RunProvider (needs runId + runData) and OWN the key,
// because the key must remount IterationProvider when runId changes.
function RunStage({ children }: AppProviderProps) {
  const { runId, runData } = useRunContext()
  return (
    <IterationProvider key={runId} max={runData.processing_order.length}>
      {children}
    </IterationProvider>
  )
}
