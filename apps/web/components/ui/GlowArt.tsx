import Image, { type StaticImageData } from "next/image";

import { cn } from "@/lib/format";

/**
 * Decorative 3D artwork rendered with `mix-blend-screen` so the near-black
 * backgrounds of the source PNGs dissolve into the app's dark navy theme,
 * plus an optional radial mask that feathers the edges to avoid visible
 * rectangle boundaries.
 */
export function GlowArt({
  src,
  width,
  height,
  className,
  masked = true,
  sizes,
}: {
  src: string | StaticImageData;
  width: number;
  height: number;
  className?: string;
  masked?: boolean;
  sizes?: string;
}) {
  return (
    <Image
      src={src}
      alt=""
      aria-hidden
      width={width}
      height={height}
      sizes={sizes}
      className={cn(
        "pointer-events-none select-none mix-blend-screen",
        // Aggressive radial feather: kills the rectangular black plate common in
        // AI-generated 3D PNGs so they dissolve into the navy page background.
        masked &&
          "[mask-image:radial-gradient(ellipse_62%_68%_at_50%_48%,#000_38%,transparent_82%)] [-webkit-mask-image:radial-gradient(ellipse_62%_68%_at_50%_48%,#000_38%,transparent_82%)]",
        className,
      )}
    />
  );
}
