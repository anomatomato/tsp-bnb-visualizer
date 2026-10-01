import { type Dispatch, type SetStateAction, useEffect, useState } from "react"

export function usePlayback(
  iteration: number,
  max: number,
  setIteration: Dispatch<SetStateAction<number>>
) {
  const [isPlaying, setIsPlaying] = useState(false)

  const isLastIteration = iteration >= max

  if (isPlaying && isLastIteration) {
    setIsPlaying(false)
  }

  useEffect(() => {
    if (!isPlaying) return

    const id = setInterval(() => {
      setIteration((prev) => Math.min(prev + 1, max))
    }, 400)

    return () => clearInterval(id)
  }, [max, isPlaying, setIteration])

  function togglePlay() {
    const nextIsPlaying = !isPlaying
    setIsPlaying(nextIsPlaying)
  }

  function next() {
    setIteration((i) => Math.min(i + 1, max))
  }

  function prev() {
    setIteration((i) => Math.max(i - 1, 1))
  }

  function jumpTo(value: number) {
    setIteration(value)
  }

  function jumpToFirst() {
    setIteration(1)
  }

  function jumpToLast() {
    setIteration(max)
  }

  return { isPlaying, togglePlay, next, prev, jumpTo, jumpToFirst, jumpToLast }
}
