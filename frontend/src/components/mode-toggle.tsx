import { cn } from "cn"
import { Check, Monitor, Moon, Sun } from "lucide-react"

import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function ModeToggle() {
  const { theme, setTheme } = useTheme()

  const iconClass = (active: boolean) => {
    return cn(
      "absolute transition-all",
      active ? "scale-100 rotate-0" : "scale-0 rotate-90"
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="outline" size="icon" className="relative">
            {/* 'relative' custom added, also maybe the following h-[] and w-[] not needed, as Button already defines explicit size */}
            <Sun className={iconClass(theme === "light")} />
            <Moon className={iconClass(theme === "dark")} />
            <Monitor className={iconClass(theme === "system")} />
            <span className="sr-only">Toggle theme</span>
          </Button>
        }
      />
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme("light")}>
          <Sun /> Light {theme === "light" && <Check className="ml-auto" />}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")}>
          <Moon /> Dark
          {theme === "dark" && <Check className="ml-auto" />}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("system")}>
          <Monitor /> System
          {theme === "system" && <Check className="ml-auto" />}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
