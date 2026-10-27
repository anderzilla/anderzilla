import { readFile } from "node:fs/promises";
import path from "node:path";
export const runtime = "nodejs";
export const dynamic = "force-static";
export const alt = "AnderZilla - Games, IA e boas descobertas";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export default async function OgImage() {
 const bytes = await readFile(path.join(process.cwd(), "public", "brand", "social-card.png"));
 return new Response(new Uint8Array(bytes), { headers: { "Content-Type": "image/png" } });
}
