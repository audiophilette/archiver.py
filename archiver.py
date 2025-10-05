#!/usr/bin/env python3
import yt_dlp
import os
import sys
import shlex
import traceback


def read_archive_file():
    """Reads archiveme.txt for URL and optional additional args."""
    url = None
    extra_args = []
    with open("archiveme.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("url:"):
                url = line.split(":", 1)[1].strip()
            elif line.lower().startswith("addtl_args:"):
                extra_args.extend(shlex.split(line.split(":", 1)[1].strip()))
    if not url:
        raise ValueError("archiveme.txt must contain a 'url:' line.")
    return url, extra_args


def merge_cli_args(opts, args):
    """Mini-parser that merges simple CLI-style args into opts."""
    i = 0
    while i < len(args):
        arg = args[i]
        # key=value pattern or --flag value pattern
        if arg.startswith("--"):
            key = arg.lstrip("-").replace("-", "_")
            # Handle boolean flags (no following value)
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                opts[key] = True
            else:
                opts[key] = args[i + 1]
                i += 1
        i += 1
    return opts


def build_opts(extra_args):
    """Build yt-dlp options with safe defaults and overridable extras."""
    opts = {
        "match_filter": yt_dlp.utils.match_filter_func("!is_short"),
        "format": "bestaudio/best",
        "min_sleep_interval": 10,
        "max_sleep_interval": 60,
        "nooverwrites": True,
        "continuedl": True,
        "download_archive": "downloaded.txt",
        "cookiefile": "youtube.com_cookies.txt",
        "outtmpl": "%(title)s [%(id)s] %(uploader)s.%(ext)s",
        "prefer_ffmpeg": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "flac",
            "preferredquality": "0",
            "when": "post_process",
        }],
    }

    if extra_args:
        opts = merge_cli_args(opts, extra_args)

    # If user didn’t specify audioformat, default to FLAC
    if "audioformat" not in opts and "preferredcodec" not in opts["postprocessors"][0]:
        opts["postprocessors"][0]["preferredcodec"] = "flac"

    return opts


def main():
    try:
        url, extra_args = read_archive_file()
        opts = build_opts(extra_args)

        print(f"Downloading from: {url}")
        if extra_args:
            print(f"   Extra args: {' '.join(extra_args)}")

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        print("Download complete.")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

