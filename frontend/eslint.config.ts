import js from "@eslint/js"
import jsxA11y from "eslint-plugin-jsx-a11y"
import { plugin as shadcn } from "@shadcn/lint"
import reactHooks from "eslint-plugin-react-hooks"
import reactRefresh from "eslint-plugin-react-refresh"
import eslintTailwindcss from "eslint-plugin-tailwindcss"
import { defineConfig, globalIgnores } from "eslint/config"
import globals from "globals"
import tseslint from "typescript-eslint"
import type { CompatibleConfigArray } from "typescript-eslint"
import type { PluginSettings } from "eslint-plugin-tailwindcss"

export default defineConfig([
  globalIgnores(["dist"]),
  // eslintTailwindcss.configs.recommended,
  {
    settings: {
      tailwindcss: {
        cssConfigPath: "./src/index.css",
      } satisfies PluginSettings,
    },
    files: ["**/*.{ts,tsx}"],
    // Plugin registered only — no @shadcn/lint rules enabled yet.
    // Enable rules per-entry under `rules` (e.g. "shadcn/no-restyle"):
    // https://github.com/shadcn-ui/lint/blob/main/docs/rules.md
    plugins: { shadcn },
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      jsxA11y.flatConfigs.recommended,
      eslintTailwindcss.configs.recommended as CompatibleConfigArray,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          args: "all",
          argsIgnorePattern: "^_",
          caughtErrors: "all",
          caughtErrorsIgnorePattern: "^_",
          destructuredArrayIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          ignoreRestSiblings: true,
        },
      ],
      "shadcn/no-arbitrary-values": ["error", { allow: ["layout"] }],
      "shadcn/no-restyle": ["error", { allow: ["layout"] }],
      "shadcn/require-static-classes": "error",
    },
  },
  {
    // Vendored shadcn/ui components: they export cva variant helpers
    // (buttonVariants, badgeVariants, ...) alongside components by design.
    files: ["src/components/ui/**/*.{ts,tsx}"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
])
