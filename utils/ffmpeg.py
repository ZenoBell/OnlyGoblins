# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""FFmpeg Launcher Module"""


import platform
import sys
import shutil
import subprocess


def get_ffmpeg_bin() -> str:
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin is None and getattr(sys, "frozen", False):
        raise RuntimeError(
            "FFmpeg is required for streaming media. Install FFmpeg, add its bin folder "
            "to PATH, and restart OnlyGoblins. See the README for setup."
        )

    if ffmpeg_bin is None:
        from pyffmpeg import FFmpeg
        ffmpeg = FFmpeg(enable_log=False)
        ffmpeg_bin = ffmpeg.get_ffmpeg_bin()

    return ffmpeg_bin


def run_ffmpeg(args: list[str]) -> bool:
    proc_args = [get_ffmpeg_bin()]

    proc_args += args

    result = subprocess.run(
        proc_args,
        encoding='utf-8',
        capture_output=True,
        check=True,
        timeout=300,
    )

    return result.returncode == 0
