#!/usr/bin/env python3
import argparse, re
from datetime import datetime
from pathlib import Path

EXTS = ("css", "js", "png", "jpg", "jpeg", "webp", "svg")
DEFAULT_FILES = [
    "index.html",
    "ZonasEscolares/index.html",
    "Intersecciones/index.html",
    "EstablecimientoSalud/index.html",
]
PATTERN = re.compile(
    rf'(?P<attr>href|src)\s*=\s*"(?P<url>[^"]+?\.(?:{"|".join(EXTS)}))(?P<rest>[^"]*)"',
    re.IGNORECASE,
)

def cache_bust_html(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    def repl(m):
        url, rest = m.group("url"), m.group("rest")
        if "?" in url or "?v=" in rest:
            return m.group(0)
        return f'{m.group("attr")}="{url}?v={version}{rest}"'
    new = PATTERN.sub(repl, text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print(f"[ok] {path} (v={version})")
    else:
        print(f"[skip] {path} (sin cambios)")

def main():
    ap = argparse.ArgumentParser(description="Cache busting para recursos estáticos en HTML.")
    ap.add_argument("files", nargs="*", help="Rutas de archivos HTML a actualizar. Si no pasas nada, se usan DEFAULT_FILES.")
    ap.add_argument("--version", help="Versión a usar; por defecto timestamp UTC.")
    args = ap.parse_args()
    version = args.version or datetime.utcnow().strftime("%Y%m%d%H%M%S")
    targets = args.files or DEFAULT_FILES
    for f in targets:
        cache_bust_html(Path(f), version)

if __name__ == "__main__":
    main()
