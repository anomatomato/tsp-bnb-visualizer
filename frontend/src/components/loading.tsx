import { Spinner } from "@/components/ui/spinner"
import { Centered } from "@/components/layouts/centered"

export default function Loading() {
  return (
    <Centered role="status">
      <Spinner className="size-8" />
      <span className="sr-only">Loading…</span>
    </Centered>
  )
}
