"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Spinner } from "@/components/ui/Alert";
import { useAppContext } from "@/context/AppProvider";
import { routes } from "@/lib/routes";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { isAuthReady, isAuthenticated } = useAppContext();

  useEffect(() => {
    if (!isAuthReady) {
      return;
    }
    if (!isAuthenticated) {
      const query = searchParams.toString();
      const returnPath = query ? `${pathname}?${query}` : pathname;
      router.replace(`${routes.login}?next=${encodeURIComponent(returnPath)}`);
    }
  }, [isAuthReady, isAuthenticated, pathname, router, searchParams]);

  if (!isAuthReady) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Loading your session" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Redirecting to login" />
      </div>
    );
  }

  return children;
}
