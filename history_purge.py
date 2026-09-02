#!/usr/bin/env python3
"""
history_purge.py -- content scrubber for the supply-chain-attack payload
=======================================================================

Single source of truth for *what* gets stripped out of infected files.

Used two ways:

  * .github/workflows/history-purge.yml runs it as a ``git filter-repo``
    blob callback, so the payload is removed from **every commit** in a
    repository's history (not just the current checkout).

  * Standalone, for humans:

        python history_purge.py path/to/file ...     # clean files in place
        python history_purge.py --self-check         # verify the regexes

    Use the file form to try the transforms on a working tree before you
    run the irreversible history rewrite.

A blob is only modified when it contains a *hard* indicator: the target
wallet address, the ``A10-...4650`` wallet marker, an ``eth_get*`` probe,
an ``rpc*`` wrapper, or ``spawn('node', [... '-e' ...])``. Files that
merely contain ``_0x`` identifiers -- ordinary minified JS -- are left
byte-for-byte unchanged.
"""
from __future__ import annotations

import re
import sys

# --- detection ---------------------------------------------------------------

# If NONE of these match, the blob is returned untouched.
HARD_INDICATORS = [
    re.compile(rb"""global\.i\s*=\s*["']A10-[^"']*4650["']"""),
    re.compile(rb"0xa322E5f3", re.IGNORECASE),
    re.compile(rb"\b(?:eth_getTra|eth_blockN|eth_getBlo)\w*"),
    re.compile(rb"\b(?:withRpcEndpoints|rpcCall|rpcBatch)\b"),
    re.compile(rb"""spawn\s*\(\s*["']node["'][^)]*["']-e["']"""),
]


def is_infected(data: bytes) -> bool:
    """True if `data` contains a hard malware indicator."""
    return any(rx.search(data) for rx in HARD_INDICATORS)


# Same set as a single str regex, for locating the first payload byte.
_HARD_STR = re.compile(
    r"""global\.i\s*=\s*["']A10-[^"']*4650["']"""
    r"""|0xa322E5f3"""
    r"""|\beth_(?:getTra|blockN|getBlo)\w*"""
    r"""|\b(?:withRpcEndpoints|rpcCall|rpcBatch)\b"""
    r"""|spawn\s*\(\s*["']node["'][^)]*["']-e["']""",
    re.IGNORECASE,
)

_TERMINATORS = ";})]"


def _truncate_before_payload(text: str):
    """The attack appends its payload after otherwise-legit code. Return the
    text up to the last top-level statement boundary before the first hard
    indicator, or None if no legit prefix exists (whole blob is payload)."""
    m = _HARD_STR.search(text)
    if not m:
        return text  # nothing to cut

    head = text[: m.start()]
    depth = 0
    in_str = None
    esc = False
    last_boundary = -1
    for i, c in enumerate(head):
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == in_str:
                in_str = None
            continue
        if c in "\"'`":
            in_str = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "\n" and depth <= 0:
            j = i - 1
            while j >= 0 and head[j] in " \t":
                j -= 1
            if j >= 0 and head[j] in _TERMINATORS:
                last_boundary = i
    if last_boundary == -1:
        return None
    return text[:last_boundary] + "\n"


# --- content transforms (only applied to infected text blobs) ---------------

_TEXT_SUBS = [
    # wallet-marker assignment -- drop the whole line
    (re.compile(r"""(?m)^[^\n]*\bglobal\.i\s*=\s*["']A10-[^"'\n]*["'][^\n]*$\n?"""), ""),
    # other injected globals: global.r = ...  global['_V'] = ...  global["_H"]=...
    (re.compile(
        r"""(?m)^[ \t]*global\s*(?:\.\s*[A-Za-z_$][\w$]*"""
        r"""|\[\s*["'][^"'\]]+["']\s*\])\s*=\s*[^;\n]*;?[ \t]*$\n?"""), ""),
    # obfuscated declarations
    (re.compile(r"""(?s)\bconst\s+_0x[0-9a-fA-F]{3,}\s*=\s*.*?;"""), ""),
    (re.compile(r"""(?s)\b(?:var|let)\s+_0x[0-9a-fA-F]{3,}\s*=\s*.*?;"""), ""),
    # obfuscated function decl -- single-line body ...
    (re.compile(r"""\bfunction\s+_0x[0-9a-fA-F]{3,}\s*\([^)]*\)\s*\{[^{}]*\}"""), ""),
    # ... and multi-line block body
    (re.compile(r"""(?s)\bfunction\s+_0x[0-9a-fA-F]{3,}\s*\([^)]*\)\s*\{.*?\n[ \t]*\}"""), ""),
    # RPC wrapper helpers (both body shapes)
    (re.compile(
        r"""\b(?:async\s+)?function\s+"""
        r"""(?:withRpcEndpoints|rpcCall|rpcBatch)\s*\([^)]*\)\s*\{[^{}]*\}"""), ""),
    (re.compile(
        r"""(?s)\b(?:async\s+)?function\s+"""
        r"""(?:withRpcEndpoints|rpcCall|rpcBatch)\s*\([^)]*\)\s*\{.*?\n[ \t]*\}"""), ""),
    (re.compile(
        r"""(?s)\b(?:const|let|var)\s+"""
        r"""(?:withRpcEndpoints|rpcCall|rpcBatch)\s*=\s*.*?;"""), ""),
    # RPC probe method-name string literals -> empty string
    (re.compile(r"""["'](?:eth_getTra|eth_blockN|eth_getBlo)\w*["']"""), '""'),
    # inline-node command execution
    (re.compile(r"""(?s)\bspawn\s*\(\s*["']node["']\s*,\s*\[[^\]]*\]\s*\)"""), "null"),
    # target wallet address -> zero address (keeps surrounding code parseable)
    (re.compile(r"0xa322E5f3[0-9a-fA-F]*"), "0x" + "0" * 40),
    # long hex-escape string blobs "\x61\x62\x63..."
    (re.compile(r"""["'](?:\\x[0-9a-fA-F]{2}){6,}["']"""), '""'),
]

# .gitignore lines that hide the attack's helper files. Match the filename
# stem so every extension form is caught: temp_auto_push.bat, .ps1, .*, etc.
_GITIGNORE_HELPERS = (
    r"temp_auto_push|temp_interactive_push|branch_structure\.json"
)
_MALICIOUS_GITIGNORE = re.compile(r"(?m)^.*(?:" + _GITIGNORE_HELPERS + r").*$\n?")
_MALICIOUS_GITIGNORE_B = re.compile((r"(?:" + _GITIGNORE_HELPERS + r")").encode())

# The attack prepends a `createRequire` shim so its appended payload can call
# require() from an ESM file. Once the payload is gone the shim is dead code.
_CREATEREQUIRE = re.compile(
    r"(?m)^[ \t]*(?:"
    r"import[ \t]*\{[ \t]*createRequire[ \t]*\}[ \t]*from[ \t]*['\"](?:node:)?module['\"]"
    r"|(?:const|let|var)[ \t]+require[ \t]*=[ \t]*createRequire\([ \t]*import\.meta\.url[ \t]*\)"
    r")[ \t]*;?[ \t]*\n(?:[ \t]*\n)?"  # also eat one trailing blank line
)
_REQUIRE_CALL = re.compile(r"(?<![A-Za-z0-9_$.])require[ \t]*\(")

_BLANKS = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")

# The real payload is glued onto the end of a legit file on the *same physical
# line*, hidden behind a long run of padding whitespace. Legit source (even
# minified) never has 40+ consecutive spaces/tabs, so that run is the seam.
_PAYLOAD_PAD = re.compile(r"[ \t\r\x0b\x0c]{40,}")

_STUB = b"// removed by security cleanup: file contained supply-chain malware\n"


def _infected_text(text: str) -> bool:
    return is_infected(text.encode("utf-8", "ignore"))


def _dead_createrequire(text: str) -> bool:
    """True if the file sets up `require` via createRequire but never calls it."""
    if "createRequire(import.meta.url" not in text.replace(" ", ""):
        return False
    return not _REQUIRE_CALL.search(text)


def scrub(data: bytes) -> bytes:
    """Return `data` with the payload removed. Safe to call on any blob."""
    hard = is_infected(data)
    gitignore = _MALICIOUS_GITIGNORE_B.search(data) is not None
    shim = b"createRequire" in data
    if not (hard or gitignore or shim):
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        # infected but binary (e.g. payload hidden in a "font" file):
        # history-purge.yml removes those paths wholesale instead.
        return data

    before = text

    if gitignore:
        text = _MALICIOUS_GITIGNORE.sub("", text)

    if hard:
        # 1. Cut at the padding-whitespace seam, if the payload is past it.
        cut = None
        for pad in _PAYLOAD_PAD.finditer(text):
            if _infected_text(text[pad.start():]):
                cut = pad.start()
                break
        if cut is not None:
            head = text[:cut].rstrip()
            text = (head + "\n") if head else _STUB.decode()
        else:
            # 2. No seam -> brace-aware cut, else stub the whole file.
            t = _truncate_before_payload(text)
            text = _STUB.decode() if t is None else t

        # 3. Mop up any indicator left inside the surviving region.
        for rx, repl in _TEXT_SUBS:
            text = rx.sub(repl, text)
        if _infected_text(text):
            return _STUB

    # Dead createRequire shim left by the attack (only when require is unused).
    if _dead_createrequire(text):
        text = _CREATEREQUIRE.sub("", text)

    if text == before:
        return data
    text = _BLANKS.sub("\n\n", text)
    return text.encode("utf-8")


# --- git filter-repo blob callback -----------------------------------------
# history-purge.yml passes the body below via --blob-callback; `blob` is
# provided by git-filter-repo.
def _filter_repo_callback(blob, metadata):  # pragma: no cover
    blob.data = scrub(blob.data)


# --- self-check ------------------------------------------------------------
_LEGIT_CONFIG = (
    b'import tseslint from "typescript-eslint";\n\n'
    b"export default tseslint.config({\n"
    b'  files: ["**/*.ts"],\n'
    b'  rules: { "no-unused-vars": "warn" },\n'
    b"});\n"
)

# Real-world shape: payload glued onto the last line of the legit file behind a
# long whitespace pad, everything on one physical line, ending with run();
_REAL_PAYLOAD = (
    b'global.i="A10-*4650";const _0x499797=_0x1574;'
    b"(function(_0x50cf58,_0x4b5935){})( _0x303e,123),global['r']=require);"
    b"async function withRpcEndpoints(a,b){}"
    b"async function rpcCall(u,m,p,s){}async function rpcBatch(u,b,s){}"
    b'const R=["https://eth.drpc.org","0xa322E5f3"];'
    b'function run(){eval("x");spawn("node",["-e",y]);}run();'
)

# (source, tokens_that_must_be_gone, exact_expected_output_or_None)
_SELF_CHECK_CASES = [
    # 1. payload appended behind a whitespace pad -> legit config kept verbatim
    (
        _LEGIT_CONFIG.rstrip() + b"\n);" + b" " * 400 + _REAL_PAYLOAD + b"\n",
        [b"A10-", b"_0x", b"0xa322E5f3", b"eth_", b"rpcBatch", b"withRpcEndpoints",
         b"spawn(", b"eval("],
        _LEGIT_CONFIG.rstrip() + b"\n);\n",
    ),
    # 1b. payload appended with a plain newline (no pad) after a legit config
    (
        _LEGIT_CONFIG + _REAL_PAYLOAD + b"\n",
        [b"A10-", b"0xa322E5f3", b"withRpcEndpoints", b"rpcBatch"],
        None,  # must at least be clean; exact form not asserted
    ),
    # 2. ordinary minified JS (no hard indicator) -> byte-for-byte identical
    (
        b"const _0x12ab=require('react');function _0x34(a){return a+1}\n"
        b"module.exports={_0x34};\n",
        [],
        None,  # only assert unchanged
    ),
    # 3. poisoned .gitignore (attacker's real glob forms) -> lines dropped
    (
        b"node_modules\n.env\nbranch_structure.json\ndist\n"
        b"temp_auto_push.*\ntemp_interactive_push.*\n.next\n",
        [b"temp_auto_push", b"temp_interactive_push", b"branch_structure"],
        b"node_modules\n.env\ndist\n.next\n",
    ),
    # 4. whole file is payload -> replaced with a stub
    (
        b'global.i="A10-*4650";\nfunction _0x1(){ return "0xa322E5f3"; }\n',
        [b"A10-", b"0xa322E5f3", b"_0x1"],
        _STUB,
    ),
    # 5. dead createRequire shim (require never called) -> shim removed
    (
        b"import { createRequire } from 'module';\n\n"
        b"const require = createRequire(import.meta.url);\n\n"
        b"export default {\n  plugins: { tailwindcss: {}, autoprefixer: {} },\n};\n",
        [b"createRequire"],
        b"export default {\n  plugins: { tailwindcss: {}, autoprefixer: {} },\n};\n",
    ),
    # 6. createRequire that IS used -> left untouched
    (
        b'import { createRequire } from "node:module";\n'
        b"const require = createRequire(import.meta.url);\n"
        b'const pkg = require("./package.json");\n'
        b"export default { name: pkg.name };\n",
        [],
        None,  # unchanged
    ),
]


def _self_check() -> int:
    ok = True
    for i, (src, must_be_gone, expected) in enumerate(_SELF_CHECK_CASES, 1):
        out = scrub(src)
        problems = []
        if not must_be_gone and out != src:
            problems.append("clean blob was modified")
        problems += [f"indicator survived: {tok!r}" for tok in must_be_gone if tok in out]
        if expected is not None and out != expected:
            problems.append(f"output mismatch\n     got: {out!r}\n    want: {expected!r}")
        if problems:
            ok = False
            print(f"[FAIL] case {i}: " + "; ".join(problems))
        else:
            print(f"[ok]   case {i} ({len(src) - len(out):+d} bytes)")
    print("\nself-check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --- standalone CLI ------------------------------------------------------
if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--self-check" in argv:
        raise SystemExit(_self_check())

    files = [a for a in argv if not a.startswith("-")]
    if not files:
        print("usage: python history_purge.py [--self-check] <file> [<file> ...]",
              file=sys.stderr)
        raise SystemExit(2)

    changed = 0
    for path in files:
        with open(path, "rb") as fh:
            original = fh.read()
        cleaned = scrub(original)
        if cleaned != original:
            with open(path, "wb") as fh:
                fh.write(cleaned)
            changed += 1
            print(f"[cleaned] {path} ({len(original) - len(cleaned):+d} bytes)")
        else:
            print(f"[ok]      {path}")
    print(f"\n{changed} file(s) modified")
