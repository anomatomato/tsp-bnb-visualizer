// Vite glob: keys are module-relative paths, values are hashed asset URLs.
// Normalized to filename → URL so image_path ("images/relaxation_0.svg") resolves.
const images = import.meta.glob<string>("../mock/eil51/images/*.svg", {
  eager: true,
  query: "?url",
  import: "default",
})

const byName = new Map<string, string>(
  Object.entries(images).map(([path, url]) => [path.split("/").pop()!, url])
)

/** "images/relaxation_0.svg" → bundled URL | null. Same signature will serve
 *  file-picker runs later (populated from URL.createObjectURL instead). */
export function resolveImage(imagePath: string | null): string | null {
  if (!imagePath) return null
  return byName.get(imagePath.split("/").pop()!) ?? null
}
