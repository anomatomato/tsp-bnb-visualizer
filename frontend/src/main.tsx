import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import "@/index.css"
import App from "@/app"
import { ThemeProvider } from "@/components/theme-provider.tsx"
import { TooltipProvider } from "@/components/ui/tooltip"

const rootId = "root"
let rootElement = document.getElementById("root")

// Create root if it doesn't exist
if (!rootElement) {
  rootElement = document.createElement("div")
  rootElement.id = rootId
  document.body.append(rootElement)
}

createRoot(rootElement).render(
  <StrictMode>
    <ThemeProvider>
      <TooltipProvider delay={150}>
        <App />
      </TooltipProvider>
    </ThemeProvider>
  </StrictMode>
)
