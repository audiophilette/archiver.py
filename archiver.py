#!/usr/bin/env python3
import yt_dlp
import os
import sys
import time
import random
import traceback

ARCHIVE_FILE = "archiveme.txt"
COOKIES_FILE = "youtube.com_cookies.txt"
DOWNLOAD_LOG = "downloaded.txt"


def read_archive_file():
    """
    Reads archiveme.txt in the current working directory.
    Expected format:
        url: https://www.youtube.com/@Example/videos
        addtl_args: --playlist-items 1-10
    Returns (url, extra_args)
    """
    url = None
    extra_args = []

    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("url:"):
                    url = line.split(":", 1)[1].strip()
                elif line.lower().startswith("addtl_args:"):
                    parts = line.split(":", 1)[1].strip().split()
                    extra_args.extend(parts)
    except FileNotFoundError:
        raise FileNotFoundError(f"Missing required file: {ARCHIVE_FILE}")

    if not url:
        raise ValueError(f"{ARCHIVE_FILE} must contain a 'url:' line.")

    return url, extra_args


def build_opts(extra_args):
    """
    Constructs yt-dlp options with universal defaults,
    then merges in any additional arguments found in archiveme.txt.
    """
    opts = {
        "match_filter": yt_dlp.utils.match_filter_func("!is_short"),
        "min_sleep_interval": 10,
        "max_sleep_interval": 60,
        "nooverwrites": True,
        "continuedl": True,
        "download_archive": DOWNLOAD_LOG,
        "cookiefile": COOKIES_FILE,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "flac",
            "preferredquality": "0"
        }],
        "outtmpl": "%(title)s.%(ext)s",
    }

    # Merge additional arguments
    if extra_args:
        try:
            parser = yt_dlp.parse_options(extra_args)
            opts.update(parser[0])
        except Exception as e:
            raise ValueError(f"Failed to parse addtl_args: {extra_args}\n{e}")

    return opts


def main():
    try:
        if not os.path.exists(ARCHIVE_FILE):
            raise FileNotFoundError(f"No {ARCHIVE_FILE} found in current directory.")

        url, extra_args = read_archive_file()
        opts = build_opts(extra_args)

        if not os.path.exists(COOKIES_FILE):
            print(f"Warning: {COOKIES_FILE} not found. Some videos may fail to download.")

        print(f"Starting download from: {url}")
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        print("✅ Download completed successfully.")

    except yt_dlp.utils.DownloadError as e:
        print(f"yt-dlp failed: {e}")
        sys.exit(2)
    except (FileNotFoundError, ValueError) as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹ Interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print("Unexpected error occurred:")
        traceback.print_exc()
        sys.exit(99)


if __name__ == "__main__":
    main()
