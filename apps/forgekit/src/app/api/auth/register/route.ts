import { NextRequest, NextResponse } from "next/server";
import { createSession, isDemoMode, registerUser } from "@/lib/auth";

export async function POST(req: NextRequest) {
  if (isDemoMode()) {
    await createSession("demo-user", "demo@forgekit.dev");
    return NextResponse.json({ ok: true, demo: true });
  }

  const body = (await req.json()) as {
    email?: string;
    password?: string;
    name?: string;
  };
  if (!body.email || !body.password) {
    return NextResponse.json({ error: "Email and password required" }, { status: 400 });
  }
  if (body.password.length < 8) {
    return NextResponse.json({ error: "Password must be at least 8 characters" }, { status: 400 });
  }

  try {
    const user = await registerUser(body.email, body.password, body.name);
    await createSession(user.id, user.email);
    return NextResponse.json({ ok: true, email: user.email });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Registration failed" },
      { status: 400 }
    );
  }
}
