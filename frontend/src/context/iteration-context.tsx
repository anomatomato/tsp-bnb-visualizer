import {
  createContext,
  use,
  useMemo,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react"
import { useClampedState } from "@/hooks/use-clamped-state"

interface IterationContextValue {
  iteration: number
  setIteration: Dispatch<SetStateAction<number>>
  max: number
}

// Create context
const IterationContext = createContext<IterationContextValue | undefined>(
  undefined
)

export function IterationProvider({
  children,
  max,
}: {
  children: ReactNode
  initial?: number
  max: number
}) {
  const [iteration, setIteration] = useClampedState(max, 1, max)

  const value = useMemo(
    () => ({
      iteration,
      setIteration,
      max,
    }),
    [iteration, setIteration, max]
  )
  return <IterationContext value={value}>{children}</IterationContext>
}

export function useIterationContext() {
  const context = use(IterationContext)
  if (!context) {
    throw new Error(
      "useIterationContext must be used within a IterationProvider"
    )
  }
  return context
}
