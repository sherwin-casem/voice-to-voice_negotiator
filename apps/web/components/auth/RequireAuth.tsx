"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Spinner } from "@/components/ui/Alert";
import { useAppContext } from "@/context/AppProvider";
import { registerWithNext } from "@/lib/routes";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { isAuthReady, isAuthenticated } = useAppContext();

  const isPreviewResults =
    pathname.includes("/results") && searchParams.get("preview") === "1";

  useEffect(() => {
    if (!isAuthReady || isPreviewResults) {
      return;
    }
    if (!isAuthenticated) {
      const query = searchParams.toString();
      const returnPath = query ? `${pathname}?${query}` : pathname;
      router.replace(registerWithNext(returnPath));
    }
  }, [isAuthReady, isAuthenticated, isPreviewResults, pathname, router, searchParams]);

  if (!isAuthReady) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Loading your session" />
      </div>
    );
  }

  if (!isAuthenticated && !isPreviewResults) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Redirecting to sign up" />
      </div>
    );
  }

  return children;
}
