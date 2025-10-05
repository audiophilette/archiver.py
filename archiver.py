#!/usr/bin/env python3
import yt_dlp
import os
import sys
import shlex
import traceback


# ---------- helpers ----------------------------------------------------------

def read_archive_file(filename="archiveme.txt"):
    """Read archiveme.txt for URL and optional CLI-style args."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        raise FileNotFoundError(f"Missing required file: {filename}")

    url, extra_args = None, []
    for line in lines:
        if line.lower().startswith("url:"):
            url = line.split(":", 1)[1].strip()
        elif line.lower().startswith("addtl_args:"):
            extra_args.extend(shlex.split(line.split(":", 1)[1].strip()))

    if not url:
        raise ValueError(f"{filename} must contain a 'url:' line.")
    return url, extra_args


def apply_manual_args(opts, args):
    """Merge a small whitelist of CLI flags into opts."""
    i = 0
    while i < len(args):
        arg = args[i]
        nxt = args[i + 1] if i + 1 < len(args) else None
        try:
            if arg == "--match-title" and nxt:
                opts["match_title"] = nxt
                i += 1
            elif arg == "--reject-title" and nxt:
                opts["reject_title"] = nxt
                i += 1
            elif arg == "--audio-format" and nxt:
                opts["postprocessors"][0]["preferredcodec"] = nxt
                i += 1
            elif arg == "--sleep-interval" and nxt:
                val = int(nxt)
                opts["min_sleep_interval"] = opts["max_sleep_interval"] = val
                i += 1
            elif arg == "--no-continue":
                opts["continuedl"] = False
            elif arg == "--no-overwrites":
                opts["nooverwrites"] = False
        except Exception as e:
            print(f"⚠️  Ignoring malformed argument '{arg}': {e}")
        i += 1
    return opts


def build_opts(extra_args, debug=False):
    """Compose yt-dlp options with defaults and safe overrides."""
    opts = {
        "format": "bestaudio/best",
        "min_sleep_interval": 10,
        "max_sleep_interval": 60,
        "nooverwrites": True,
        "continuedl": True,
        "download_archive": "downloaded.txt",
        "cookiefile": "youtube.com_cookies.txt",
        "outtmpl": "%(title)s [%(id)s] %(uploader)s.%(ext)s",
        "prefer_ffmpeg": True,
        "match_filter": yt_dlp.utils.match_filter_func("!is_short"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "flac",
            "preferredquality": "0",
            "when": "post_process",
        }],
    }

    if extra_args:
        opts = apply_manual_args(opts, extra_args)

    if debug:
        opts["verbose"] = True

    return opts


# ---------- main -------------------------------------------------------------

def main():
    debug = "--debug" in sys.argv
    # remove our own flag so yt-dlp never sees it
    sys.argv = [arg for arg in sys.argv if arg != "--debug"]

    try:
        url, extra_args = read_archive_file()
        opts = build_opts(extra_args, debug=debug)

        print(f"▶️  Downloading from: {url}")
        if extra_args:
            print(f"   Extra args: {' '.join(extra_args)}")

        if debug:
            print("----- DEBUG INFO -----")
            for k, v in opts.items():
                if callable(v):
                    print(f"{k}: <callable>")
                else:
                    print(f"{k}: {v}")
            print("----------------------")

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            print(f"❌ yt-dlp download error: {e}")
            sys.exit(2)

        print("✅ Download complete.")
        sys.exit(0)

    except (FileNotFoundError, ValueError) as e:
        print(f"⚠️  Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹ Interrupted by user.")
        sys.exit(130)
    except Exception:
        print("💥 Unexpected error:")
        traceback.print_exc()
        sys.exit(99)


# ---------- entry ------------------------------------------------------------

if __name__ == "__main__":
    main()

