import { getErrorMessage, type FallbackProps } from "react-error-boundary"
import { Button } from "@/components/ui/button"
import { Centered } from "@/components/layouts/centered"

/**
 * A fallback UI component for displaying an error message when an unexpected error occurs.
 */
export function MainErrorFallback({
  error,
  resetErrorBoundary,
}: FallbackProps) {
  return (
    <Centered className="gap-6" role="alert">
      <h2>Oops, something went wrong :( </h2>
      <pre className="max-w-lg whitespace-pre-wrap text-destructive">
        {getErrorMessage(error)}
      </pre>
      <Button onClick={resetErrorBoundary}>Try again</Button>
    </Centered>
  )
}
