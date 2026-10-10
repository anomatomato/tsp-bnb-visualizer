import babel from "@rolldown/plugin-babel"
import tailwindcss from "@tailwindcss/vite"
import react, { reactCompilerPreset } from "@vitejs/plugin-react"
import path from "path"
import { defineConfig, type Plugin, type Connect } from "vite"
import { createReadStream, stat } from "node:fs"

// Only what this route exists for: the viewer's data + image assets.
// Doubles as a guard: unknown extensions — including the per-run index.html
// files the serializer writes — never reach the fs layer.
const TYPES: Record<string, string> = {
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
}

function serveRuns(): Plugin {
  // vite.config.ts lives in frontend/; the run archive is a sibling directory.
  const root = path.resolve(import.meta.dirname, "../output/runs")

  const handler: Connect.NextHandleFunction = (req, res, next) => {
    if (req.method !== "GET" && req.method !== "HEAD") return next()

    // Route-mounted (see below): req.url arrives prefix-stripped ("/index.json").
    // URL() drops the query; %2f stays encoded until the decode below.
    let rel: string
    try {
      rel = decodeURIComponent(new URL(req.url ?? "", "http://x").pathname)
    } catch {
      res.statusCode = 400 // malformed %-escape ("/runs/%") or unparseable target
      return res.end()
    }
    if (rel.includes("\0")) {
      res.statusCode = 400 // %00 — null byte would throw deep inside fs
      return res.end()
    }

    // join() normalizes ".."; containment must match the separator too,
    // or a sibling like output/runs-old would pass the check.
    const file = path.join(root, rel)
    if (file !== root && !file.startsWith(root + path.sep)) {
      res.statusCode = 403
      return res.end()
    }

    const type = TYPES[path.extname(file)]
    if (!type) {
      res.statusCode = 404 // not a type this route serves — no fs call needed
      return res.end()
    }

    stat(file, (err, info) => {
      if (err || !info.isFile()) {
        res.statusCode = 404 // missing OR directory — deterministic 4xx; never
        return res.end() // falls through to Vite's SPA fallback (200 + HTML)
      }
      res.setHeader("Content-Type", type)
      res.setHeader("Content-Length", info.size)
      if (req.method === "HEAD") return res.end()
      createReadStream(file)
        .on("error", () => res.destroy())
        .pipe(res)
    })
  }

  return {
    name: "serve-output-runs",
    // Mounting on the path prefix: Connect matches only /runs/* and strips
    // the prefix from req.url — no manual startsWith/slice bail-out.
    configureServer(server) {
      server.middlewares.use("/runs", handler)
    },
    configurePreviewServer(server) {
      server.middlewares.use("/runs", handler)
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({
      presets: [reactCompilerPreset()],
    }),
    tailwindcss(),
    serveRuns(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
})
