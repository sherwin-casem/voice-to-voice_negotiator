import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { routes, type HomeSection } from "@/lib/routes";

const DEFAULT_RETRIES = 8;

export function scrollToHomeSection(
  section: HomeSection,
  options: { retries?: number; behavior?: ScrollBehavior } = {},
) {
  const { retries = DEFAULT_RETRIES, behavior = "smooth" } = options;

  function attempt(remaining: number) {
    const target = document.getElementById(section);
    if (target) {
      target.scrollIntoView({ behavior, block: "start" });
      window.history.replaceState(null, "", routes.homeSection(section));
      return;
    }
    if (remaining > 0) {
      window.requestAnimationFrame(() => attempt(remaining - 1));
    }
  }

  attempt(retries);
}

export function navigateToHomeSection(
  section: HomeSection,
  router: AppRouterInstance,
  pathname: string,
) {
  if (pathname === routes.home) {
    scrollToHomeSection(section);
    return;
  }

  router.push(routes.homeSection(section));
}

export function scrollToHashFromLocation(options: { retries?: number } = {}) {
  const hash = window.location.hash.replace("#", "") as HomeSection;
  if (!hash) {
    return;
  }

  scrollToHomeSection(hash, options);
}
