import { cookies } from "next/headers";
import { createHash, timingSafeEqual } from "crypto";
import bcrypt from "bcryptjs";
import { prisma } from "./prisma";

const SESSION_COOKIE = "forgekit_session";
const SESSION_DAYS = 14;

export function isDemoMode() {
  return process.env.DEMO_MODE === "true";
}

function signSession(userId: string, email: string): string {
  const secret = process.env.AUTH_SECRET ?? "dev-secret";
  const payload = Buffer.from(JSON.stringify({ userId, email, exp: Date.now() + SESSION_DAYS * 864e5 })).toString(
    "base64url"
  );
  const sig = createHash("sha256").update(`${payload}.${secret}`).digest("base64url");
  return `${payload}.${sig}`;
}

function verifySession(token: string): { userId: string; email: string } | null {
  const [payload, sig] = token.split(".");
  if (!payload || !sig) return null;
  const secret = process.env.AUTH_SECRET ?? "dev-secret";
  const expected = createHash("sha256").update(`${payload}.${secret}`).digest("base64url");
  try {
    const a = Buffer.from(sig);
    const b = Buffer.from(expected);
    if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  } catch {
    return null;
  }
  try {
    const data = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as {
      userId: string;
      email: string;
      exp: number;
    };
    if (Date.now() > data.exp) return null;
    return { userId: data.userId, email: data.email };
  } catch {
    return null;
  }
}

export async function hashPassword(password: string) {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string) {
  return bcrypt.compare(password, hash);
}

export async function createSession(userId: string, email: string) {
  const token = signSession(userId, email);
  const jar = await cookies();
  jar.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_DAYS * 86400,
  });
}

export async function destroySession() {
  const jar = await cookies();
  jar.delete(SESSION_COOKIE);
}

export async function getSession() {
  if (isDemoMode()) {
    return {
      userId: "demo-user",
      email: "demo@forgekit.dev",
      demo: true as const,
    };
  }
  const jar = await cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  const session = verifySession(token);
  if (!session) return null;
  return { ...session, demo: false as const };
}

export async function requireSession() {
  const session = await getSession();
  if (!session) {
    return null;
  }
  return session;
}

export async function registerUser(email: string, password: string, name?: string) {
  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    throw new Error("Email already registered");
  }
  const passwordHash = await hashPassword(password);
  return prisma.user.create({
    data: { email, passwordHash, name },
  });
}

export async function loginUser(email: string, password: string) {
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user?.passwordHash) {
    throw new Error("Invalid email or password");
  }
  const ok = await verifyPassword(password, user.passwordHash);
  if (!ok) {
    throw new Error("Invalid email or password");
  }
  return user;
}
