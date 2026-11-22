#!/usr/bin/env python3
"""remotezip: list a ZIP on a web server and take ONE file out of it, without downloading the archive.

A ZIP keeps its table of contents (the central directory) at the end. With HTTP Range requests that table is read
from the last bytes of the file, and then only the bytes of the one member are fetched and unpacked. A 700 MB
sound pack costs a few hundred KB for its list and a few MB per sound taken from it.

  python remotezip.py list URL [--grep whoosh]
  python remotezip.py get URL "Folder/Whoosh Fast 01.wav" --out DIR

Standard library only. Handles ZIP64 (archives over 4 GB) and the two methods sound packs use: stored and deflate.
"""
import argparse
import re
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) avelune-sound/1.1"


class RangeError(RuntimeError):
    pass


_SIZES = {}


def remote_size(url):
    if url not in _SIZES:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA, "Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=60) as r:
            n = r.headers.get("Content-Length")
            if not n:
                raise RangeError(f"no Content-Length for {url}")
            _SIZES[url] = int(n)
    return _SIZES[url]


def http_range(url, start, end=None):
    """Bytes [start, end] of url (end inclusive); start < 0 means the last -start bytes. Ranges are always sent as
    explicit start-end: some servers (Cloudflare in front of downloads.sonniss.com) ignore a suffix range and start
    sending the whole multi-GB file."""
    if start < 0:
        size = remote_size(url)
        start, end = max(0, size + start), size - 1
    elif end is None:
        end = remote_size(url) - 1
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": f"bytes={start}-{end}",
                                               "Accept-Encoding": "identity"})
    # the CDN now and then answers a Range request with 200 and the whole file (seen on 74 of 78 Sonniss archives in
    # one run, none a minute later): close it unread and ask again, a few times, before giving up on the archive
    status = None
    for attempt in range(4):
        if attempt:
            time.sleep(1.5 * attempt)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                status = r.status
                if r.status == 206:
                    return r.read()
        except urllib.error.HTTPError as e:
            status = e.code
            if e.code not in (429, 500, 502, 503, 504, 520, 522, 524):
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            status = f"{type(e).__name__}: {e}"
    raise RangeError(f"server ignored the Range request (HTTP {status}) four times: {url}")


def _eocd(tail):
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RangeError("no end-of-central-directory record in the last bytes (not a zip, or a long comment)")
    (_, disk, _, n_disk, n, cd_size, cd_off, _) = struct.unpack("<IHHHHIIH", tail[i:i + 22])
    j = tail.rfind(b"PK\x06\x06", 0, i)            # ZIP64 end of central directory
    if j >= 0 and (n == 0xFFFF or cd_size == 0xFFFFFFFF or cd_off == 0xFFFFFFFF):
        (_, _, _, _, _, _, _, n, cd_size, cd_off) = struct.unpack("<IQHHIIQQQQ", tail[j:j + 56])
    return n, cd_size, cd_off, i


def _parse_cd(cd):
    out, p = [], 0
    while p + 46 <= len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        (_, _, _, flags, method, _, _, crc, csize, usize, nlen, xlen, clen, _, _, _, off) = \
            struct.unpack("<IHHHHHHIIIHHHHHII", cd[p:p + 46])
        raw = cd[p + 46:p + 46 + nlen]
        name = raw.decode("utf-8" if flags & 0x800 else "cp437", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + xlen]
        q = 0
        while q + 4 <= len(extra):                    # ZIP64 extra field: the real sizes and offset
            hid, hlen = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals = extra[q + 4:q + 4 + hlen]
                k = 0
                if usize == 0xFFFFFFFF:
                    usize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF:
                    csize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if off == 0xFFFFFFFF:
                    off = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
            q += 4 + hlen
        out.append({"name": name, "method": method, "csize": csize, "size": usize, "offset": off, "crc": crc,
                    "flags": flags})
        p += 46 + nlen + xlen + clen
    return out


def list_members(url, fetch=http_range):
    tail = fetch(url, -65536)
    n, cd_size, cd_off, _ = _eocd(tail)
    if cd_size > 64 * 1024 * 1024:
        raise RangeError(f"central directory is {cd_size >> 20} MB: too big")
    cd = fetch(url, cd_off, cd_off + cd_size - 1)
    members = _parse_cd(cd)
    if len(members) != n:
        print(f"WARN remotezip: {len(members)} of {n} entries parsed", file=sys.stderr)
    return [m for m in members if not m["name"].endswith("/")]


def extract(url, member, dst, fetch=http_range):
    """Fetch one member (a dict from list_members) and write it to dst. Checks the CRC."""
    if member["flags"] & 1:
        raise RangeError(f"{member['name']}: encrypted")
    head = fetch(url, member["offset"], member["offset"] + 29)
    if head[:4] != b"PK\x03\x04":
        raise RangeError(f"{member['name']}: no local header at offset {member['offset']}")
    nlen, xlen = struct.unpack("<HH", head[26:30])
    start = member["offset"] + 30 + nlen + xlen
    data = fetch(url, start, start + member["csize"] - 1) if member["csize"] else b""
    if member["method"] == 0:
        raw = data
    elif member["method"] == 8:
        raw = zlib.decompressobj(-15).decompress(data)
    else:
        raise RangeError(f"{member['name']}: compression method {member['method']} not supported")
    if zlib.crc32(raw) & 0xFFFFFFFF != member["crc"]:
        raise RangeError(f"{member['name']}: CRC mismatch (download damaged)")
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(raw)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("url")
    ls.add_argument("--grep")
    g = sub.add_parser("get")
    g.add_argument("url")
    g.add_argument("name")
    g.add_argument("--out", default=".")
    a = ap.parse_args()
    ms = list_members(a.url)
    if a.cmd == "list":
        rx = re.compile(a.grep, re.I) if a.grep else None
        for m in ms:
            if not rx or rx.search(m["name"]):
                print(f"{m['size'] / 1e6:8.2f} MB  {m['name']}")
        print(f"{len(ms)} files")
    else:
        m = next((m for m in ms if m["name"] == a.name), None)
        if not m:
            sys.exit(f"not in the archive: {a.name}")
        print(extract(a.url, m, Path(a.out) / Path(m["name"]).name))


if __name__ == "__main__":
    main()
