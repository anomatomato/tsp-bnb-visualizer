import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Pause, Play } from "lucide-react"
import { type Dispatch, type SetStateAction, useEffect, useState } from "react"

interface TimeLineProps {
  iteration: number
  max: number
  setIteration: Dispatch<SetStateAction<number>>
}

export function TimeLine({ iteration, max, setIteration }: TimeLineProps) {
  // play: setInterval 500ms advancing until max; clear on unmount/pause/end
  const [isPlaying, setIsPlaying] = useState(false)

  if (isPlaying && iteration >= max) {
    setIsPlaying(false)
  }

  useEffect(() => {
    if (!isPlaying) return

    const id = setInterval(() => {
      setIteration((prev) => Math.min(prev + 1, max))
    }, 400)

    return () => clearInterval(id)
  }, [max, isPlaying, setIteration])

  function handleClick() {
    const nextIsPlaying = !isPlaying
    setIsPlaying(nextIsPlaying)
  }

  return (
    <div className="flex flex-row items-center gap-2">
      <Button size="icon" onClick={handleClick}>
        {isPlaying ? <Pause /> : <Play />}
      </Button>
      <Slider
        value={[iteration]}
        onValueChange={(v: number | readonly number[]) => {
          setIteration(Array.isArray(v) ? v[0] : v)
        }}
        min={1}
        max={max}
        step={1}
        className="max-w-md"
      />
      <span className="font-mono text-sm tabular-nums">
        {iteration}/{max}
      </span>
    </div>
  )
}
