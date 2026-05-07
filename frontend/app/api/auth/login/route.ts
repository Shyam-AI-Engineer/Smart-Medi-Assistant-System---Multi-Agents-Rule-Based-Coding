import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const IS_PROD = process.env.NODE_ENV === "production";

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Invalid request body" }, { status: 400 });
  }

  let res: Response;
  try {
    res = await fetch(`${BACKEND}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 503 });
  }

  const data = await res.json();

  if (!res.ok) {
    return NextResponse.json(data, { status: res.status });
  }

  const response = NextResponse.json({
    user_id: data.user_id,
    email: data.email,
    role: data.role,
    full_name: data.full_name ?? null,
  });

  response.cookies.set("medi_token", data.access_token, {
    httpOnly: true,
    secure: IS_PROD,
    sameSite: "strict",
    path: "/",
    maxAge: 30 * 60,
  });

  if (data.refresh_token) {
    response.cookies.set("medi_refresh", data.refresh_token, {
      httpOnly: true,
      secure: IS_PROD,
      sameSite: "strict",
      path: "/",
      maxAge: 7 * 24 * 60 * 60,
    });
  }

  return response;
}
