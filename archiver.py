#!/usr/bin/env python3
import yt_dlp
import os
import sys
import shlex
import re
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


def make_combined_filter(title_regex=None):
    """Return a callable that skips Shorts and non-matching titles."""
    regex = re.compile(title_regex, re.IGNORECASE) if title_regex else None

    def _filter(info):
        # Block obvious YouTube Shorts
        if info.get("duration") and info["duration"] < 60:
            return "short video (<60s)"
        if "/shorts/" in info.get("webpage_url", ""):
            return "YouTube Shorts URL"
        # Apply match-title regex if given
        if regex and not regex.search(info.get("title", "")):
            return f"title doesn't match {regex.pattern}"
        return None
    return _filter


def apply_manual_args(opts, args):
    """Merge a small whitelist of CLI flags into opts."""
    i = 0
    title_pattern = None
    while i < len(args):
        arg = args[i]
        nxt = args[i + 1] if i + 1 < len(args) else None
        try:
            if arg == "--match-title" and nxt:
                title_pattern = nxt
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

    # Always rebuild the combined filter (handles Shorts + optional title)
    opts["match_filter"] = make_combined_filter(title_pattern)
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
        "outtmpl": "%(title)s [%(id)s].%(ext)s",
        "prefer_ffmpeg": True,
        "match_filter": make_combined_filter(None),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "flac",
            "preferredquality": "0",
            "when": "post_process",
        },
         # Step 2 – add tags from yt-dlp metadata
       {
           "key": "FFmpegMetadata",
           "add_metadata": True,
           "when": "post_process",
       },
  ],
    }

    if extra_args:
        opts = apply_manual_args(opts, extra_args)

    if debug:
        opts["verbose"] = True

    return opts


# ---------- main -------------------------------------------------------------

def main():
    debug = "--debug" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--debug"]

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

