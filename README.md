# archiver.py
youtube music script

I use this to archive youtube AI music channels mostly cuz i think the legal system will eventually destroy them.

This uses yt-dlp module via pip.

You will need a youtube cookies file, as generated from a chrome-based "cookies.txt" exporter (e.g. "get cookies.txt"
This archiver will also expect a "archiveme.txt" with, at LEAST a url: line with the root url you want to grab.  you can set addtl yt-dlp arguments in an additional line:

    addtl_args: --match-title "(?i)AI covers"

These arguments SHOULD be able to override the defauilts, but i've not tested it yet.
