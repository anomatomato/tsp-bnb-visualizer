import { type Dispatch, type SetStateAction, useState } from "react"

export function useClampedState(initial: number, min: number, max: number) {
  const [value, setValue] = useState(Math.max(Math.min(max, initial), min))

  const setClampedValue: Dispatch<SetStateAction<number>> = (v) =>
    setValue((prev) => {
      const next = typeof v === "function" ? v(prev) : v
      return Math.min(Math.max(next, min), max)
    })

  return [value, setClampedValue] as const
}
