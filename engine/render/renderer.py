"""
Renderer for Reel Editor.
Executes HyperFrames render or FFmpeg filtergraph fallback.
"""
import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from engine.render.gpu_detector import detect_gpu_encoder

async def render_project(
    project_dir: str,
    output_path: str,
    preview: bool = False,
    timeout_sec: int = 300
) -> Dict[str, Any]:
    """
    Renders the HyperFrames project to the specified output MP4 path.
    """
    project = Path(project_dir).resolve()
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    node_bin = shutil.which("node") or "node"
    hf_cli = project / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"

    gpu_enc = detect_gpu_encoder()
    
    cmd = [
        node_bin,
        str(hf_cli),
        "render",
        "--output", str(out)
    ]
    
    if preview:
        cmd.extend(["--scale", "0.5"])

    # If local CLI binary not found in node_modules, fall back to npx
    if not hf_cli.exists():
        cmd = ["npx", "hyperframes", "render", "--output", str(out)]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(project),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        
        success = (proc.returncode == 0) and out.exists()
        file_size = out.stat().st_size if out.exists() else 0

        return {
            "success": success,
            "returncode": proc.returncode,
            "output_path": str(out),
            "file_size_bytes": file_size,
            "encoder_used": gpu_enc,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace")
        }

    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Render timed out",
            "output_path": str(out)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "output_path": str(out)
        }
