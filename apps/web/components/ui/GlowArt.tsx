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
        masked &&
          "[mask-image:radial-gradient(ellipse_70%_70%_at_50%_50%,#000_55%,transparent_98%)]",
        className,
      )}
    />
  );
}
