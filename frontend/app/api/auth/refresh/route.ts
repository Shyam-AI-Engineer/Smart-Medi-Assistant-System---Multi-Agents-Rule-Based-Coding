import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const IS_PROD = process.env.NODE_ENV === "production";

export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get("medi_refresh")?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: "No refresh token" }, { status: 401 });
  }

  let res: Response;
  try {
    res = await fetch(`${BACKEND}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${refreshToken}` },
    });
  } catch {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 503 });
  }

  const data = await res.json();
  if (!res.ok) {
    const response = NextResponse.json(data, { status: res.status });
    // Refresh token is invalid/expired — clear both cookies
    response.cookies.delete("medi_token");
    response.cookies.delete("medi_refresh");
    return response;
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set("medi_token", data.access_token, {
    httpOnly: true,
    secure: true,
    sameSite: "none",
    path: "/",
    maxAge: 30 * 60,
  });
  return response;
}
