/** "images/relaxation_0.svg" → "runs/<runId>/images/relaxation_0.svg" */
export function resolveImage(
  imagePath: string | null,
  runId: string
): string | null {
  if (!imagePath) return null
  return `runs/${runId}/${imagePath}`
}
