import js from "@eslint/js"
import jsxA11y from "eslint-plugin-jsx-a11y"
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
  {
    // Disable for context files
    files: [
      "src/**/context/**/*.{ts,tsx}",
      "src/components/theme-provider.tsx",
    ],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
])
