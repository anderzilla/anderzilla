import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "AnderZilla — tools, stacks & geek fuel";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 72,
          background: "#07070c",
          color: "#fafafa",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            width: 72,
            height: 72,
            borderRadius: 16,
            alignItems: "center",
            justifyContent: "center",
            background: "linear-gradient(135deg, #f59e0b, #8b5cf6)",
            color: "#07070c",
            fontSize: 28,
            fontWeight: 700,
          }}
        >
          Az
        </div>
        <div style={{ marginTop: 36, fontSize: 64, fontWeight: 700 }}>AnderZilla</div>
        <div style={{ marginTop: 16, fontSize: 28, color: "#a1a1aa", maxWidth: 800 }}>
          Tools, stacks & geek fuel for builders who ship.
        </div>
        <div style={{ marginTop: 40, fontSize: 22, color: "#fbbf24" }}>
          ForgeKit · StackPick · anderzilla.com
        </div>
      </div>
    ),
    { ...size }
  );
}
