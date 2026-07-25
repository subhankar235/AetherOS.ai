import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/tts
 * Server-side proxy to ElevenLabs Text-to-Speech API.
 * Accepts JSON { text: string } and returns audio/mpeg stream.
 * Keeps the API key server-side (never exposed to browser).
 */
export async function POST(req: NextRequest) {
  try {
    const { text } = await req.json();

    if (!text || typeof text !== "string" || text.trim().length === 0) {
      return NextResponse.json({ error: "Missing 'text' field" }, { status: 400 });
    }

    const apiKey = process.env.ELEVENLABS_API_KEY;
    if (!apiKey) {
      console.error("ELEVENLABS_API_KEY not configured");
      return NextResponse.json({ error: "TTS not configured" }, { status: 500 });
    }

    const voiceId = process.env.ELEVENLABS_VOICE_ID || "TRnaQb7q41oL7sV0w6Bu";
    const modelId = process.env.ELEVENLABS_TTS_MODEL || "eleven_flash_v2_5";

    const response = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "xi-api-key": apiKey,
        },
        body: JSON.stringify({
          text: text.slice(0, 5000), // ElevenLabs has a character limit
          model_id: modelId,
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75,
            style: 0.3,
            use_speaker_boost: true,
          },
        }),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("ElevenLabs TTS error:", response.status, errorText);
      return NextResponse.json(
        { error: `ElevenLabs API returned ${response.status}` },
        { status: 502 }
      );
    }

    // Stream the audio back to the client
    const audioBuffer = await response.arrayBuffer();
    return new NextResponse(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "no-cache",
      },
    });
  } catch (err: any) {
    console.error("TTS route error:", err);
    return NextResponse.json(
      { error: err.message || "Internal TTS error" },
      { status: 500 }
    );
  }
}
