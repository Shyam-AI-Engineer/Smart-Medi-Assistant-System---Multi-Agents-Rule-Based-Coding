import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function handler(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const { path } = await params;
  const token = req.cookies.get("medi_token")?.value;
  const url = `${BACKEND}/api/v1/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (token) headers.set("authorization", `Bearer ${token}`);

  const hasBody = !["GET", "HEAD"].includes(req.method);

  let res: Response;
  try {
    res = await fetch(url, {
      method: req.method,
      headers,
      body: hasBody ? req.body : undefined,
      // Required for streaming request bodies (file uploads, audio)
      // @ts-expect-error -- duplex not yet in TypeScript fetch types
      duplex: "half",
    });
  } catch {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 503 });
  }

  return new NextResponse(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/json",
      // Preserve content-disposition for PDF/file downloads
      ...(res.headers.get("content-disposition")
        ? { "content-disposition": res.headers.get("content-disposition")! }
        : {}),
    },
  });
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
