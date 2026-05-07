import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete("medi_token");
  response.cookies.delete("medi_refresh");
  return response;
}
