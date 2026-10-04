import {
  createContext,
  use,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react"
import { type Direction } from "@/lib/layout"

interface DirectionContextValue {
  direction: Direction
  setDirection: Dispatch<SetStateAction<Direction>>
}

// Create context
export const DirectionContext = createContext<
  DirectionContextValue | undefined
>(undefined)

export function DirectionProvider({
  children,
  initial,
}: {
  children: ReactNode
  initial: Direction
}) {
  const [direction, setDirection] = useState<Direction>(initial)

  const value = useMemo(
    () => ({
      direction,
      setDirection,
    }),
    [direction]
  )
  return <DirectionContext value={value}>{children}</DirectionContext>
}

export function useDirectionContext() {
  const context = use(DirectionContext)
  if (!context) {
    throw new Error(
      "useDirectionContext must be used within a DirectionProvider"
    )
  }
  return context
}
