#!/usr/bin/env python3
"""Builds dist/video-effects-pack.zip for upload to Claude (Settings > Capabilities > Skills).
The folder `video-effects-pack/` sits at the root of the ZIP, as Claude expects.
Usage: python3 tools/make_zip.py"""
import os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "skills", "video-effects-pack")
OUT = os.path.join(ROOT, "dist", "video-effects-pack.zip")

def check_frontmatter():
    text = open(os.path.join(SRC, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m: sys.exit("SKILL.md: frontmatter not found")
    name = re.search(r"^name:\s*(\S+)\s*$", m.group(1), re.M).group(1)
    desc = re.search(r"^description:\s*(.+?)\s*$", m.group(1), re.M).group(1)
    if name != os.path.basename(SRC): sys.exit("SKILL.md: name '%s' must equal the folder name" % name)
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64: sys.exit("SKILL.md: bad name")
    if len(desc) > 200: sys.exit("SKILL.md: description is %d chars (claude.ai accepts at most 200)" % len(desc))
    print("frontmatter OK: name=%s, description=%d chars" % (name, len(desc)))

def main():
    check_frontmatter()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d, dirs, files in os.walk(SRC):
            dirs[:] = sorted(x for x in dirs if x != "__pycache__")
            for f in sorted(files):
                if f.endswith((".pyc", ".mp4", ".mov")) or f in (".DS_Store", "Thumbs.db"): continue
                p = os.path.join(d, f)
                z.write(p, os.path.join("video-effects-pack", os.path.relpath(p, SRC)).replace(os.sep, "/"))
    print("written %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1048576.0))

if __name__ == "__main__":
    main()
