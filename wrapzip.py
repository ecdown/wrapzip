#!/usr/bin/env python3
"""Pack a file into a self-extracting email payload, or unpack one."""
#######################################################################
#
# Name: wrapzip
#
# Description:  Utility to generate a payload to send scripts and text 
#               when attachments are not allowed.  It generates a python
#               script with a runnable payload that generates the file
#               specified.
#
# Author: Eric Downing <ecdown@etechtips.com>
#
# Version:  v1 2026/05/18
#######################################################################
import argparse
import base64
import gzip
import hashlib
import os
import sys
import textwrap

WIDTH = 76
WARN_LIMIT = 20 * 1024 * 1024  # 20 MB


def pack(args):
    path = args.file
    with open(path, "rb") as f:
        raw = f.read()

    compressed = gzip.compress(raw)
    b64 = base64.b64encode(compressed).decode("ascii")
    checksum = hashlib.sha256(compressed).hexdigest()
    filename = os.path.basename(path)

    wrapped = textwrap.fill(b64, WIDTH)
    payload_size = len(b64) + len(wrapped) // WIDTH  # base64 + newlines overhead

    orig_mb = len(raw) / (1024 * 1024)
    comp_mb = len(compressed) / (1024 * 1024)
    ratio = len(compressed) / len(raw) * 100 if raw else 0
    email_mb = len(compressed) / (1024 * 1024) * 4 / 3  # base64 overhead ~33%
    email_mb += len(wrapped.splitlines()) / (1024 * 1024)  # newlines
    email_mb += 2 / (1024 * 1024)  # script overhead approx

    def fmt_size(mb: float) -> str:
        if mb < 0.01:
            kb = mb * 1024
            return f"{kb:.2f} KB"
        return f"{mb:.2f} MB"

    print(
        f"Original: {fmt_size(orig_mb)} | Compressed: {fmt_size(comp_mb)} ({ratio:.0f}%)",
        file=sys.stderr,
    )
    print(f"Email payload: ~{fmt_size(email_mb)}", file=sys.stderr)

    if len(raw) > WARN_LIMIT:
        print(
            f"### WARNING: Payload exceeds 20 MB! Most email providers reject "
            f"emails over ~25 MB. ###",
            file=sys.stderr,
        )

    script = _make_script(wrapped, checksum, filename)

    if args.output:
        with open(args.output, "w") as f:
            f.write(script)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(script)


def _make_script(data_b64: str, checksum: str, filename: str) -> str:
    return f"""#!/usr/bin/env python3
\"\"\"Extract: {filename}\"\"\"
import base64, gzip, hashlib, sys

_DATA = \"\"\"\\
{data_b64}
\"\"\"

_CHECKSUM = "{checksum}"
_FILENAME = "{filename}"

if __name__ == "__main__":
    raw = base64.b64decode(_DATA)
    got = hashlib.sha256(raw).hexdigest()
    if got != _CHECKSUM:
        print("Checksum mismatch: corrupt payload", file=sys.stderr)
        sys.exit(1)
    data = gzip.decompress(raw)
    print(f"Extracted: {{_FILENAME}} ({{len(data)}} bytes)")
    with open(_FILENAME, "wb") as f:
        f.write(data)
"""


def unpack(args):
    path = args.script
    with open(path) as f:
        content = f.read()

    # Extract _DATA, _CHECKSUM, _FILENAME
    import re

    m = re.search(r'^_DATA\s*=\s*"""\\\n(.*?)^"""', content, re.MULTILINE | re.DOTALL)
    if not m:
        print("Could not find _DATA in script", file=sys.stderr)
        sys.exit(1)
    data_b64 = m.group(1).replace("\n", "")

    m = re.search(r'^_CHECKSUM\s*=\s*"([^"]*)"', content, re.MULTILINE)
    if not m:
        print("Could not find _CHECKSUM in script", file=sys.stderr)
        sys.exit(1)
    expected_checksum = m.group(1)

    m = re.search(r'^_FILENAME\s*=\s*"([^"]*)"', content, re.MULTILINE)
    if not m:
        print("Could not find _FILENAME in script", file=sys.stderr)
        sys.exit(1)
    filename = m.group(1)

    raw = base64.b64decode(data_b64)
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_checksum:
        print("Checksum mismatch: corrupt payload", file=sys.stderr)
        sys.exit(1)
    data = gzip.decompress(raw)

    with open(filename, "wb") as f:
        f.write(data)
    print(f"Extracted: {filename} ({len(data)} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="Pack a file into a self-extracting email payload, or unpack one."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("pack", help="Compress and encode a file")
    p.add_argument("file", help="Path to the file to pack")
    p.add_argument("--output", "-o", help="Output script path (default: stdout)")

    p = sub.add_parser("unpack", help="Decode a previously packed script")
    p.add_argument("script", help="Path to the packed script")

    args = parser.parse_args()

    if args.mode == "pack":
        pack(args)
    else:
        unpack(args)


if __name__ == "__main__":
    main()
