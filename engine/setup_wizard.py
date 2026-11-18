"""
Interactive Setup Wizard for Reel Editor.
Verifies system dependencies, guides user through API key configuration,
and sets up local directories and assets.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_banner():
    print("""
==================================================================
           REEL EDITOR — AI ENGINE SETUP WIZARD
==================================================================
  Transform raw footage into viral, engaging vertical reels
==================================================================
""")

def check_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run_setup_wizard():
    print_banner()
    root_dir = Path(__file__).resolve().parent.parent
    env_file = root_dir / ".env"

    # 1. Check System Dependencies
    print("1. Checking System Dependencies:")
    print("---------------------------------")
    py_ok = sys.version_info >= (3, 10)
    print(f"  Python {sys.version.split()[0]:<10} : {'[OK]' if py_ok else '[FAIL - 3.10+ required]'}")

    node_ok = check_command("node")
    print(f"  Node.js        : {'[OK]' if node_ok else '[FAIL - install from https://nodejs.org]'}")

    ffmpeg_ok = check_command("ffmpeg")
    print(f"  FFmpeg         : {'[OK]' if ffmpeg_ok else '[FAIL - must be installed in PATH]'}")

    docker_ok = check_command("docker")
    print(f"  Docker         : {'[OK]' if docker_ok else '[OPTIONAL - for postgres/redis containers]'}")

    print()

    # 2. Collect API Keys
    print("2. Free AI Provider Configuration:")
    print("---------------------------------")
    print("  You can leave any of these blank to skip or use offline mode.\n")

    current_env = {}
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    current_env[k.strip()] = v.strip()

    groq_cur = current_env.get("GROQ_API_KEY", "")
    print("  [1] Groq API Key (Recommended for 0.4s Whisper transcription)")
    print("      Get free key at: https://console.groq.com")
    prompt_str = f"      Enter Groq Key [{groq_cur[:8]}...]: " if groq_cur else "      Enter Groq Key: "
    groq_input = input(prompt_str).strip()
    groq_key = groq_input if groq_input else groq_cur

    gemini_cur = current_env.get("GEMINI_API_KEY", "")
    print("\n  [2] Google Gemini API Key (Director LLM)")
    print("      Get free key at: https://aistudio.google.com")
    prompt_str = f"      Enter Gemini Key [{gemini_cur[:8]}...]: " if gemini_cur else "      Enter Gemini Key: "
    gemini_input = input(prompt_str).strip()
    gemini_key = gemini_input if gemini_input else gemini_cur

    openrouter_cur = current_env.get("OPENROUTER_API_KEY", "")
    print("\n  [3] OpenRouter API Key (Fallback free models)")
    print("      Get free key at: https://openrouter.ai")
    prompt_str = f"      Enter OpenRouter Key [{openrouter_cur[:8]}...]: " if openrouter_cur else "      Enter OpenRouter Key: "
    or_input = input(prompt_str).strip()
    openrouter_key = or_input if or_input else openrouter_cur

    # 3. Write .env
    env_content = f"""# Reel Editor Environment Configuration
GROQ_API_KEY={groq_key}
GEMINI_API_KEY={gemini_key}
OPENROUTER_API_KEY={openrouter_key}

# Local AI (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# Database & Queue (Docker)
DATABASE_URL=postgresql://reeluser:reelpass@localhost:5432/reeldb
REDIS_URL=redis://localhost:6379/0

# Model Cache
MODEL_CACHE_DIR={Path.home() / '.cache' / 'reel-engine' / 'models'}

# Asset Paths
ASSET_REGISTRY_DIR={root_dir / 'engine' / 'assets'}
SFX_DIR={root_dir / 'assets' / 'sfx'}
LOGO_CACHE_DIR={root_dir / 'assets' / 'cache' / 'logos'}
OUTPUT_DIR={root_dir / 'Export'}
"""
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)

    print(f"\n[OK] Configuration written to {env_file}")

    # 4. Verify Local Assets
    print("\n3. Verifying Sound Effects & Assets:")
    print("-----------------------------------")
    sfx_dir = root_dir / "assets" / "sfx"
    sfx_files = list(sfx_dir.glob("*.wav")) if sfx_dir.exists() else []
    print(f"  Local SFX Files : {len(sfx_files)} loaded in assets/sfx/")

    logos_dir = root_dir / "assets" / "cache" / "logos"
    logo_files = list(logos_dir.glob("*.svg")) if logos_dir.exists() else []
    print(f"  Local Logo SVGs : {len(logo_files)} loaded in assets/cache/logos/")

    print("\n==================================================================")
    print("                   SETUP COMPLETED SUCCESSFULLY                   ")
    print("==================================================================")
    print("To process a video, run:")
    print('  python engine/cli.py edit "Raw Footage/your_video.mp4"')
    print()

if __name__ == "__main__":
    run_setup_wizard()
