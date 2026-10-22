import { useState, type ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { ChevronDown } from "lucide-react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

/** One collapsible inspector act. The trigger Button carries
 * `group/button` so the chevron's `group-data-panel-open/button:`
 * variant resolves — Base UI merges the trigger's `data-panel-open`
 * onto the rendered Button. Open state lives here, so it persists
 * across node switches (the component never remounts). */
export function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string
  defaultOpen?: boolean
  children: ReactNode
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="flex flex-col gap-1"
    >
      <CollapsibleTrigger
        render={
          <Button variant="ghost" className="group/button w-full">
            {title}
            <ChevronDown className="ml-auto size-4 transition-transform group-data-panel-open/button:rotate-180" />
          </Button>
        }
      />
      <CollapsibleContent className="flex flex-col gap-2 p-3 pt-0">
        {children}
      </CollapsibleContent>
    </Collapsible>
  )
}
