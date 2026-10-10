import { cn } from "cn"
import type { ComponentPropsWithoutRef } from "react"

type CenteredProps = ComponentPropsWithoutRef<"div"> & { fullScreen?: boolean }

export function Centered({
  className,
  fullScreen = true,
  ...props
}: CenteredProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center",
        fullScreen && "min-h-svh",
        className
      )}
      {...props}
    />
  )
}
