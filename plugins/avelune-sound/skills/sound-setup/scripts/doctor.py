#!/usr/bin/env python3
"""doctor: what of the avelune-sound toolchain works on this machine, and what to do about the rest.

  python doctor.py            # human summary + the next commands
  python doctor.py --json     # the same as JSON (for the agent)
  python doctor.py --net      # also check that api.openverse.org answers

STATUS (last line, and the exit code):
  READY       0  ffmpeg, Python and a library of REAL recordings; earshot or the real-sfx tags are there
  LIMITED     1  works, but the agent picks sounds without "ears" (no earshot, no tags): say so in the report
  NO_LIBRARY  3  tools work, but there are no real recordings: connect a folder or build the starter library;
                 never fall back to synthesis on your own
  BLOCKED     2  no ffmpeg/ffprobe or Python too old: nothing can be measured or mixed
"""
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
RSFX = SKILLS / "real-sfx"
sys.path.insert(0, str(RSFX / "scripts"))

WIN = os.name == "nt"
MAC = sys.platform == "darwin"


def sh(args, timeout=30):
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 127, str(e)


def install_hint(what):
    hints = {
        "ffmpeg": ("winget install Gyan.FFmpeg" if WIN else "brew install ffmpeg-full" if MAC else
                   "sudo apt install ffmpeg"),
        "python": ("winget install Python.Python.3.12" if WIN else "brew install python" if MAC else
                   "sudo apt install python3"),
        "uv": ("winget install astral-sh.uv" if WIN else "brew install uv" if MAC else
               "curl -LsSf https://astral.sh/uv/install.sh | sh"),
        "earshot": 'uv tool install "earshot[mcp] @ git+https://github.com/Leonxlnx/earshot" && earshot doctor --fetch',
        "earshot_mcp": "claude mcp add earshot --scope user -e EARSHOT_THREADS=3 -- earshot mcp",
        "tags": f'python "{RSFX / "scripts" / "listen.py"}" install --yes && python "{RSFX / "scripts" / "listen.py"}" tag-index',
    }
    return hints[what]


def main():
    as_json = "--json" in sys.argv
    net = "--net" in sys.argv
    r = {"os": f"{platform.system()} {platform.release()}", "python": sys.version.split()[0], "checks": [],
         "next": []}

    def add(name, ok, detail, fix=None, level="need"):
        r["checks"].append({"name": name, "ok": bool(ok), "detail": detail, "level": level})
        if not ok and fix:
            r["next"].append(fix)

    # python, ffmpeg
    py_ok = sys.version_info >= (3, 9)
    add("python >= 3.9", py_ok, r["python"], install_hint("python"))
    ff = {t: shutil.which(t) for t in ("ffmpeg", "ffprobe")}
    ff_ok = all(ff.values())
    ver = sh(["ffmpeg", "-version"])[1].splitlines()[0] if ff["ffmpeg"] else "not found"
    add("ffmpeg + ffprobe", ff_ok, ver, install_hint("ffmpeg") + "  (then open a new terminal)")
    if ff_ok:
        flt = sh(["ffmpeg", "-hide_banner", "-filters"])[1]
        for f, why, lvl in (("ebur128", "loudness meter", "need"), ("alimiter", "true-peak limiter", "need"),
                            ("amultiply", "ducking in mixdown.py", "need"),
                            ("rubberband", "pitch with length kept (real-sfx pitch/fit_dur)", "nice"),
                            ("drawtext", "frame sheets with time (real-sfx look.py)", "nice")):
            has = f" {f} " in flt
            add(f"ffmpeg filter {f}", has, why, None if has else
                (f"ffmpeg without {f}: " + ("winget install Gyan.FFmpeg (full build)" if WIN else
                                            "brew install ffmpeg-full" if MAC else "a full ffmpeg build")),
                level=lvl)

    # real-sfx library
    lib_files, libs_detail = 0, []
    try:
        import common  # real-sfx
        cfgp = common.config_path()
        cfg = common.load_config()
        for lib in cfg.get("libraries", []):
            p = Path(lib["path"])
            n = sum(1 for x in p.rglob("*") if common.is_sound_file(x)) if p.is_dir() else None
            libs_detail.append({"name": lib["name"], "path": str(p), "tier": lib.get("tier", "main"),
                                "files": n})
            lib_files += n or 0
        idx = common.index_path(cfg)
        r["real_sfx"] = {"config": str(cfgp), "data_dir": str(common.DATA_DIR), "libraries": libs_detail,
                         "index": str(idx), "index_exists": idx.exists()}
        missing = [l for l in libs_detail if l["files"] is None]
        add("real-sfx config", True, str(cfgp), level="info")
        for l in missing:
            add(f"library {l['name']}", False, f"folder not found: {l['path']}",
                f'python "{RSFX / "scripts" / "setup.py"}" add-library {l["name"]} "NEW PATH" --index   '
                "(or remove it from the config)")
        add("library of real recordings", lib_files > 0,
            f"{lib_files} files in {len(libs_detail)} libraries" if libs_detail else "no libraries connected",
            "connect your sound folder: python \"" + str(RSFX / "scripts" / "setup.py") + "\" scan \"D:/Sounds\", then "
            "setup.py add-library NAME PATH --index; or build a starter one: python \"" +
            str(HERE / "starter_library.py") + "\" --register", level="lib")
        if lib_files:
            add("library index", idx.exists(), str(idx),
                f'python "{RSFX / "scripts" / "build_index.py"}"')
        ui = Path(cfg["uisfx"]["path"])
        ui = ui if ui.is_absolute() else RSFX / ui
        add("uisfx UI cues (synthesized, only with the user's OK)", (ui / "manifest.json").exists(), str(ui),
            level="info")
        venv = common.venv_python()
        add("real-sfx tags (YAMNet, 45 MB): search by meaning", bool(venv), str(venv or "not installed"),
            install_hint("tags"), level="ears")
    except SystemExit as e:
        add("real-sfx config", False, str(e), f'python "{RSFX / "scripts" / "setup.py"}" check')
    except Exception as e:
        add("real-sfx", False, f"{type(e).__name__}: {e}", None)

    # earshot
    es = shutil.which("earshot")
    if es:
        code, out = sh(["earshot", "--version"], timeout=60)
        add("earshot (ears: rank, match, realness, timeline)", code == 0, out.strip().splitlines()[0] if out else es,
            None, level="ears")
        code, out = sh(["claude", "mcp", "list"], timeout=60) if shutil.which("claude") else (1, "")
        add("earshot MCP server (models stay loaded)", "earshot" in out, "in claude mcp list" if "earshot" in out
            else "not registered", install_hint("earshot_mcp"), level="nice")
    else:
        add("earshot (ears: rank, match, realness, timeline)", False, "not installed (~1.1 GB of models)",
            (f"{install_hint('uv')}  then  {install_hint('earshot')}" if not shutil.which("uv") else
             install_hint("earshot")), level="ears")

    if net:
        try:
            with urllib.request.urlopen("https://api.openverse.org/v1/audio/?q=whoosh&page_size=1", timeout=20) as u:
                ok = u.status == 200
        except Exception as e:
            ok, err = False, str(e)
        add("api.openverse.org", ok, "answers" if ok else err[:120], "no internet to Openverse: use your own library",
            level="nice")

    blocked = not (py_ok and ff_ok and all(c["ok"] for c in r["checks"] if c["level"] == "need"))
    ears = any(c["ok"] for c in r["checks"] if c["level"] == "ears")
    status = "BLOCKED" if blocked else "NO_LIBRARY" if lib_files == 0 else "READY" if ears else "LIMITED"
    r["status"] = status
    code = {"READY": 0, "LIMITED": 1, "BLOCKED": 2, "NO_LIBRARY": 3}[status]

    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(code)
    print(f"avelune-sound doctor  ({r['os']}, Python {r['python']})")
    for c in r["checks"]:
        mark = "ok  " if c["ok"] else {"need": "MISS", "lib": "MISS", "ears": "no  ", "nice": "no  ",
                                        "info": "--  "}[c["level"]]
        print(f"  {mark} {c['name']}: {c['detail']}")
    if r["next"]:
        print("next:")
        for n in dict.fromkeys(r["next"]):
            print(f"  - {n}")
    meaning = {"READY": "everything for scoring a film with real sounds and measuring it",
               "LIMITED": "works; sounds are picked by numbers and pictures, not by meaning or realness: say so",
               "NO_LIBRARY": "no real recordings: ask the user for a folder or build the starter library; do NOT "
                             "synthesize instead",
               "BLOCKED": "install ffmpeg / Python first; nothing can be measured or mixed"}[status]
    print(f"STATUS: {status}  ({meaning})")
    sys.exit(code)


if __name__ == "__main__":
    main()
