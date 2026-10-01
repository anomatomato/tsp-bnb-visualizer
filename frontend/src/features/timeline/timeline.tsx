import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Minus, Pause, Play, Plus, SkipBack, SkipForward } from "lucide-react"
import { type Dispatch, type SetStateAction } from "react"
import { usePlayback } from "./hooks/use-playback"

interface TimeLineProps {
  iteration: number
  max: number
  setIteration: Dispatch<SetStateAction<number>>
}

export function TimeLine({ iteration, max, setIteration }: TimeLineProps) {
  const { isPlaying, togglePlay, prev, next, jumpToFirst, jumpToLast } =
    usePlayback(iteration, max, setIteration)

  const isFirstIteration = iteration <= 1
  const isLastIteration = iteration >= max

  return (
    <div className="flex w-full flex-col items-center justify-center gap-2">
      {/* Row 1: slider + count, sharing one line */}
      <div className="flex w-full max-w-md items-center gap-3">
        <Slider
          value={[iteration]}
          onValueChange={(v: number | readonly number[]) => {
            setIteration(Array.isArray(v) ? v[0] : v)
          }}
          min={1}
          max={max}
          step={1}
          className="min-w-2xs"
        />
        <span className="shrink-0 font-mono text-sm text-muted-foreground tabular-nums">
          {iteration}/{max}
        </span>
      </div>

      {/* Row 2: transport controls */}
      <div className="flex items-center gap-1">
        <Button
          size="icon-lg"
          variant="ghost"
          disabled={isFirstIteration}
          onClick={jumpToFirst}
        >
          <SkipBack />
        </Button>
        <Button
          onClick={prev}
          size="icon-lg"
          disabled={isFirstIteration}
          variant="secondary"
        >
          <Minus />
        </Button>
        <Button size="icon-lg" onClick={togglePlay} disabled={isLastIteration}>
          {isPlaying ? <Pause /> : <Play />}
        </Button>
        <Button
          size="icon-lg"
          variant="secondary"
          disabled={isLastIteration}
          onClick={next}
        >
          <Plus />
        </Button>
        <Button
          size="icon-lg"
          variant="ghost"
          disabled={isLastIteration}
          onClick={jumpToLast}
        >
          <SkipForward />
        </Button>
      </div>
    </div>
  )
}
