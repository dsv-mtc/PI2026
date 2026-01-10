# build_resumen_excels.py
from pathlib import Path
import pandas as pd

ROOT = Path(".")
RESUMEN_DIR = ROOT / "Resumen"
RESUMEN_DIR.mkdir(parents=True, exist_ok=True)

SECCIONES = [
    "ZonasEscolares",
    "Mantenimiento",
    "Intersecciones",
    "EstablecimientoSalud",
]

def combinar_excels_seccion(seccion: str):
    excels_dir = ROOT / seccion / "excels"
    if not excels_dir.exists():
        print(f"[WARN] No existe carpeta {excels_dir}")
        return

    dfs = []
    for x in sorted(excels_dir.glob("*.xlsx")):
        stem_lower = x.stem.lower()

        # 🔸 Evitar que el propio resumen (o el _resumen_excel_muni) se vuelva a concatenar
        if stem_lower.startswith("_resumen"):
            continue

        try:
            df = pd.read_excel(x, dtype=str)  # o sin dtype si prefieres
            #df["__archivo_origen"] = x.name   # opcional, pero útil
            dfs.append(df)
        except Exception as e:
            print(f"[ERROR] Leyendo {x}: {e}")

    if not dfs:
        print(f"[WARN] No hay excels válidos en {excels_dir}")
        return

    df_all = pd.concat(dfs, ignore_index=True)

    out_path = RESUMEN_DIR / f"{seccion}_resumen.xlsx"
    df_all.to_excel(out_path, index=False)
    print(f"[OK] {out_path.resolve()} (filas: {len(df_all)})")

def main():
    for seccion in SECCIONES:
        combinar_excels_seccion(seccion)

if __name__ == "__main__":
    main()
