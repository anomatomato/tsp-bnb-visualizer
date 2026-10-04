import js from "@eslint/js"
import reactHooks from "eslint-plugin-react-hooks"
import reactRefresh from "eslint-plugin-react-refresh"
import eslintPluginTailwindcss from "eslint-plugin-tailwindcss"
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
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      eslintPluginTailwindcss.configs.recommended as CompatibleConfigArray,
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
