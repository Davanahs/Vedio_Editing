"""
CLI Entrypoint for Reel Editor.
Commands:
  edit       Process video into viral reel
  setup      Interactive configuration wizard
  check      Verify dependencies and AI providers
  benchmark  Run performance benchmark against reference video
"""
import sys
import os
import asyncio
from pathlib import Path

# Ensure project root is the primary sys.path entry, and remove subpackages from sys.path
_ROOT = Path(__file__).resolve().parent.parent
_ENGINE = Path(__file__).resolve().parent

if str(_ENGINE) in sys.path:
    sys.path.remove(str(_ENGINE))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    import typer
    app = typer.Typer(help="Reel Editor — Autonomous AI Short-Form Video Engine")
except ImportError:
    # Minimal fallback runner if typer is not installed
    class TyperFallback:
        def __init__(self, **kwargs): pass
        def command(self, *args, **kwargs):
            def decorator(fn): return fn
            return decorator
        def __call__(self):
            args = sys.argv[1:]
            if not args or args[0] in ["-h", "--help"]:
                print("Usage: python engine/cli.py [edit|setup|check|benchmark]")
            elif args[0] == "setup":
                from engine.setup_wizard import run_setup_wizard
                run_setup_wizard()
            elif args[0] == "check":
                check_cmd()
            elif args[0] == "edit":
                video = args[1] if len(args) > 1 else "Raw Footage/WhatsApp Video 2026-11-17 at 21.48.47.mp4"
                edit_cmd(video_path=video)
            elif args[0] == "benchmark":
                benchmark_cmd()
    app = TyperFallback()

def check_cmd():
    from engine.providers.registry import get_transcription_provider, get_director_provider
    import shutil
    print("=== Reel Editor System Status ===")
    print(f"Node.js    : {'Available' if shutil.which('node') else 'Missing'}")
    print(f"FFmpeg     : {'Available' if shutil.which('ffmpeg') else 'Missing'}")
    print(f"Docker     : {'Available' if shutil.which('docker') else 'Not Running / Missing'}")
    
    tx = get_transcription_provider()
    print(f"Transcript : {tx.name}")
    dr = get_director_provider()
    print(f"Director   : {dr.name}")
    print("=================================")

def edit_cmd(video_path: str, output: str = "", preview: bool = False):
    from engine.pipeline import run_pipeline
    asyncio.run(run_pipeline(
        video_path=video_path,
        output_path=output if output else None,
        preview=preview
    ))

def benchmark_cmd():
    from engine.pipeline import run_pipeline
    ref_video = _ROOT / "Raw Footage" / "WhatsApp Video 2026-11-17 at 21.48.47.mp4"
    if not ref_video.exists():
        print(f"Error: Reference video not found at {ref_video}")
        return
    print("Running performance benchmark on 48s reference reel...")
    res = asyncio.run(run_pipeline(
        video_path=str(ref_video),
        preview=True
    ))
    print("\nBenchmark completed successfully.")

if isinstance(app, typer.Typer if 'typer' in globals() and hasattr(typer, 'Typer') else type):
    @app.command("edit")
    def edit(
        video_path: str = typer.Argument(..., help="Path to input video"),
        output: str = typer.Option("", "--output", "-o", help="Custom output MP4 path"),
        preview: bool = typer.Option(False, "--preview", "-p", help="Render fast low-res preview")
    ):
        edit_cmd(video_path, output, preview)

    @app.command("setup")
    def setup():
        from engine.setup_wizard import run_setup_wizard
        run_setup_wizard()

    @app.command("check")
    def check():
        check_cmd()

    @app.command("benchmark")
    def benchmark():
        benchmark_cmd()

if __name__ == "__main__":
    if hasattr(app, "__call__") and not isinstance(app, typer.Typer if 'typer' in globals() and hasattr(typer, 'Typer') else type):
        app()
    else:
        app()
