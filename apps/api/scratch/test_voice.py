import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

def load_env():
    """Load .env.local from the repository root and validate required vars.
    Returns a dict with the loaded values.
    """
    # The environment file lives in the **api** directory (one level up from this script)
    api_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    env_path_local = api_dir / ".env.local"
    env_path_default = api_dir / ".env"
    env_path_root = repo_root / ".env"
    if env_path_local.is_file():
        env_path = env_path_local
    elif env_path_default.is_file():
        env_path = env_path_default
    elif env_path_root.is_file():
        env_path = env_path_root
    else:
        print(f"[ERROR] No .env found in {api_dir} or {repo_root}")
        sys.exit(1)
    load_dotenv(dotenv_path=env_path)
    # Gather required variables for both STT and TTS
    required = {
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "ELEVENLABS_STT_MODEL": os.getenv("ELEVENLABS_STT_MODEL"),
        "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID"),
        "ELEVENLABS_TTS_MODEL": os.getenv("ELEVENLABS_TTS_MODEL"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return required

def run_stt(client, stt_model):
    """Execute Speech‑to‑Text on the public sample audio and print results."""
    audio_url = "https://storage.googleapis.com/eleven-public-cdn/video/dubbing/e2e-samples/person-us.mp3"
    response = client.speech_to_text.convert(model_id=stt_model, source_url=audio_url)
    transcript = getattr(response, "text", getattr(response, "__dict__", {}).get("text", None))
    confidence = getattr(response, "confidence", getattr(response, "__dict__", {}).get("confidence", None))
    print("--- STT Result ---")
    print(f"Transcript : {transcript}")
    print(f"Confidence : {confidence}")
    print("Full response object for debugging:")
    print(response)

def run_tts(client, voice_id, tts_model):
    """Convert a test string to speech and write the audio to scratch/output.mp3."""
    text = "Hello from AetherOS. This is a backend integration test."
    print(f"Testing TTS with voice_id: '{voice_id}', model: '{tts_model}'...")
    try:
        response = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=tts_model,
            text=text,
        )
        used_voice = voice_id
    except Exception as e:
        print(f"[ERROR] TTS Conversion failed for voice_id '{voice_id}': {e}")
        # Try fetching account voices to see if voice_id is valid
        try:
            voices_res = client.voices.get_all()
            available_ids = [v.voice_id for v in voices_res.voices]
            print(f"Available voices on your account ({len(available_ids)}): {available_ids[:5]}")
        except Exception as v_err:
            print(f"Could not list voices: {v_err}")
        sys.exit(1)

    # Determine output path (scratch folder at repo root)
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = repo_root / "scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "output.mp3"
    with open(out_path, "wb") as f:
        f.write(b"".join(response))
    print("[SUCCESS] audio generated and saved.")
    print(f"Output location : {out_path}")
    print(f"Voice ID used   : {used_voice}")
    print(f"Model used      : {tts_model}")

def main():
    parser = argparse.ArgumentParser(description="Standalone ElevenLabs STT & TTS test utility.")
    parser.add_argument(
        "--mode",
        choices=["stt", "tts", "both"],
        default="both",
        help="Select which functionality to run (default: both).",
    )
    args = parser.parse_args()
    try:
        env = load_env()
        client = ElevenLabs(api_key=env["ELEVENLABS_API_KEY"])
        if args.mode in ("stt", "both"):
            run_stt(client, env["ELEVENLABS_STT_MODEL"])
        if args.mode in ("tts", "both"):
            run_tts(client, env["ELEVENLABS_VOICE_ID"], env["ELEVENLABS_TTS_MODEL"])
    except Exception as e:
        print(f"[EXCEPTION] {e.__class__.__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
