import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const REFRESH_COOKIE = "vvn_refresh_token";

const PROTECTED_PREFIXES = ["/evaluations", "/interviews"];

const PUBLIC_PATHS = new Set([
  "/",
  "/features",
  "/pricing",
  "/resources",
  "/login",
  "/register",
]);

function isProtectedPath(pathname: string, searchParams: URLSearchParams): boolean {
  if (pathname.startsWith("/interviews/") && searchParams.get("preview") === "1") {
    return false;
  }
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PUBLIC_PATHS.has(pathname) || pathname.startsWith("/_next") || pathname.includes(".")) {
    return NextResponse.next();
  }

  if (!isProtectedPath(pathname, request.nextUrl.searchParams)) {
    return NextResponse.next();
  }

  const hasRefreshCookie = Boolean(request.cookies.get(REFRESH_COOKIE)?.value);
  if (hasRefreshCookie) {
    return NextResponse.next();
  }

  const signupUrl = request.nextUrl.clone();
  signupUrl.pathname = "/register";
  signupUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(signupUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg|apple-icon.svg).*)"],
};
