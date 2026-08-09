/**
 * Static assets served from `apps/web/public/`.
 *
 * When you replace a file on disk, bump its `version` (or set the matching
 * NEXT_PUBLIC_* env var) so browsers and devtools pick up the new image.
 */
export const INTERVIEWER_PORTRAIT = {
  /** File: apps/web/public/interviewer-portrait.png */
  path: "/interviewer-portrait.png",
  version: process.env.NEXT_PUBLIC_INTERVIEWER_PORTRAIT_VERSION ?? "4",
} as const;

export function staticAssetUrl(path: string, version: string): string {
  return `${path}?v=${encodeURIComponent(version)}`;
}
