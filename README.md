<div align="center">

# Wrapzip

**Pack files into self-extracting email payloads when attachments aren't an option.**

</div>

## Overview

Wrapzip compresses and base64-encodes a file into a standalone Python script. The recipient just runs the script to reconstruct the original file — no tools needed beyond Python 3.

## Usage

```bash
# Pack a file into a self-extracting script
./wrapzip.py pack myfile.zip -o myfile_packed.py

# Unpack a previously packed script
./wrapzip.py unpack myfile_packed.py
```

Pack outputs a script containing gzip-compressed, base64-encoded data with a SHA-256 integrity check. Unpack extracts and validates the original file.

## Motivation

Some email environments strip or block attachments. Wrapzip gives you a copy-pasteable payload that survives restrictive filters — a self-contained Python script that recreates the file on the other end.

## Commands

| Command   | Description                         |
|-----------|-------------------------------------|
| `pack`    | Compress, encode, and wrap a file   |
| `unpack`  | Extract the original from a payload |

## Options

```
positional arguments:
  {pack,unpack}
    pack         Compress and encode a file
    unpack       Decode a previously packed script

options:
  -h, --help     show this help message and exit
```

### Pack-specific

```
pack [-h] [--output OUTPUT] file

positional arguments:
  file                  Path to the file to pack

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o   Output script path (default: stdout)
```

## How it works

1. **Compress** — the input file is gzip-compressed
2. **Encode** — compressed bytes are base64-encoded
3. **Wrap** — the encoded data is embedded in a Python script with a SHA-256 checksum
4. **Run** — the recipient executes the script, which verifies the checksum, decompresses, and writes the original file

A warning is printed if the payload exceeds 20 MB (most email providers reject messages over ~25 MB).

## Example

```bash
./wrapzip.py pack document.pdf -o document_packed.py
# Original: 2.3 MB | Compressed: 1.8 MB (78%)
# Email payload: ~2.4 MB
# Written to document_packed.py

# On the receiving end:
python3 document_packed.py
# Extracted: document.pdf (2383872 bytes)
```

## Requirements

- Python 3.x (standard library only — no pip install needed)
