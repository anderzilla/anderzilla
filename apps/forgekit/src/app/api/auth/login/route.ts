import { NextRequest, NextResponse } from "next/server";
import { createSession, isDemoMode, loginUser } from "@/lib/auth";

export async function POST(req: NextRequest) {
  if (isDemoMode()) {
    await createSession("demo-user", "demo@forgekit.dev");
    return NextResponse.json({ ok: true, demo: true });
  }

  const body = (await req.json()) as { email?: string; password?: string };
  if (!body.email || !body.password) {
    return NextResponse.json({ error: "Email and password required" }, { status: 400 });
  }

  try {
    const user = await loginUser(body.email, body.password);
    await createSession(user.id, user.email);
    return NextResponse.json({ ok: true, email: user.email });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Login failed" },
      { status: 401 }
    );
  }
}
