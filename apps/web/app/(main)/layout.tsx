import { Suspense } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { Spinner } from "@/components/ui/Alert";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="flex min-h-[40vh] items-center justify-center">
            <Spinner label="Loading" />
          </div>
        }
      >
        <RequireAuth>{children}</RequireAuth>
      </Suspense>
    </AppShell>
  );
}
