# -*- coding: utf-8 -*-
"""
split_excels_por_muni.py

Genera un Excel por cada UBIGEO_GESTOR a partir de:
- ZonasEscolares/processed/Colegios_priorizados_PI2026_clean.csv
- data/municipalidades_catalog.csv

Salida por defecto:
- ZonasEscolares/excels/<slug_o_ubigeo>.xlsx   (o jerárquico DEP/PROV/DIST si se usa --by-hierarchy)

Uso:
  python split_excels_por_muni.py \
    --colegios-csv ./ZonasEscolares/processed/Colegios_priorizados_PI2026_clean.csv \
    --catalog-csv  ./data/municipalidades_catalog.csv \
    --by-hierarchy
"""
import argparse
import unicodedata
from pathlib import Path
import pandas as pd
from typing import Optional, Dict

# ---------------- utilitarios ----------------
TRUE_SET = {"true", "1", "si", "x", "t", "y", "s", "verdadero", "yes"}
FALSE_SET = {"false", "0", "no", "n", "f", "flase", "falso", "not"}
def to_ubigeo6(x) -> Optional[str]:
    if pd.isna(x): return None
    s = str(x).strip()
    if s.endswith(".0"): s = s[:-2]
    s = "".join(ch for ch in s if ch.isdigit())
    return s.zfill(6)[:6] if s else None

def safe_slug(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    t = str(s).strip()
    # evitar caracteres problemáticos en nombres de archivo
    return t.replace("/", "-").replace("\\", "-")

def to_bool_soft(x) -> bool:
    if isinstance(x, bool):
        return x
    if pd.isna(x):
        return False
    s = str(x).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    if s in TRUE_SET:
        return True
    if s in FALSE_SET:
        return False
    return bool(s)

def format_si_no(x) -> str:
    return "Sí" if to_bool_soft(x) else "No"

# ---------------- carga ----------------
def load_colegios_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    # normalizar tipos numéricos si existen
    for col in ("latitud","longitud","alumnos","docentes","siniestros"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # normalizar gestor
    if "ubigeo_gestor" not in df.columns:
        raise KeyError("El CSV de colegios no tiene la columna 'ubigeo_gestor'.")
    df["ubigeo_gestor"] = df["ubigeo_gestor"].map(to_ubigeo6)
    return df

def load_catalog(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    if "ubigeo" not in df.columns:
        raise KeyError("El catálogo debe contener la columna 'ubigeo'.")
    df["ubigeo"] = df["ubigeo"].map(to_ubigeo6)
    # asegurar admin aunque no existan
    for c in ("departamento","provincia","distrito","slug"):
        if c not in df.columns:
            df[c] = None
    return df

# ---------------- núcleo ----------------
def ensure_out_dirs(project_root: Path, section_dir: str, by_hierarchy: bool) -> Path:
    base = project_root / section_dir / "excels"
    base.mkdir(parents=True, exist_ok=True)
    return base

def pick_filename_and_dirs(ubigeo: str, row_cat: pd.Series, by_hierarchy: bool, base_dir: Path) -> Path:
    """
    Elige nombre de archivo y (opcional) subcarpetas jerárquicas.
    - Si hay 'slug' lo usa como nombre; si no, usa el propio ubigeo.
    - Si by_hierarchy: crea DEP/PROV/DIST usando los nombres del catálogo (si existen),
      de lo contrario se queda plano en /excels.
    """
    slug = row_cat.get("slug")
    name = safe_slug(slug) if isinstance(slug, str) and slug else ubigeo
    out_dir = base_dir

    if by_hierarchy:
        dep = row_cat.get("departamento") or ubigeo[:2]
        prov = row_cat.get("provincia") or ubigeo[:4]
        dist = row_cat.get("distrito") or ubigeo
        # limpiar para carpeta
        def norm_folder(x):
            t = str(x or "").strip()
            t = (t.replace("á","a").replace("é","e").replace("í","i")
                   .replace("ó","o").replace("ú","u").replace("ñ","n"))
            t = " ".join(t.split()).upper().replace(" ", "_")
            return t if t else "_"
        out_dir = base_dir / norm_folder(dep) / norm_folder(prov) / norm_folder(dist)
        out_dir.mkdir(parents=True, exist_ok=True)

    return out_dir / f"{name}.xlsx"

def build_admin_row(ubigeo: str, cat: pd.DataFrame) -> Dict[str, Optional[str]]:
    row = cat.loc[cat["ubigeo"] == ubigeo]
    if row.empty:
        return {"departamento": None, "provincia": None, "distrito": None, "slug": None}
    r = row.iloc[0]
    return {
        "departamento": r.get("departamento"),
        "provincia": r.get("provincia"),
        "distrito": r.get("distrito"),
        "slug": r.get("slug"),
    }

def display_admin(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return str(value).replace("_", " ")

def export_excels(df_colegios: pd.DataFrame, cat: pd.DataFrame, out_base: Path, by_hierarchy: bool, mode: str) -> pd.DataFrame:
    """
    Genera un XLSX por cada ubigeo_gestor.
    Columnas exportadas (si existen en 'colegios'): 
    ubigeo_gestor, departamento, provincia, distrito, codigo_ce, descripcion,
    latitud, longitud, alumnos, docentes, siniestros, implementacion, intervencion_pi2024
    """
    rows = []
    base_cols = ["codigo_ce","descripcion","latitud","longitud","alumnos","docentes","siniestros"]
    if mode == "zonas":
        base_cols.extend(["intervencion_pi2024"])

    for ubigeo, gdf in df_colegios.groupby("ubigeo_gestor", dropna=True):
        u6 = to_ubigeo6(ubigeo)
        adm = build_admin_row(u6, cat)

        # armar dataframe de salida
        gdf_out = gdf.copy()
        cols_presentes = [c for c in base_cols if c in gdf_out.columns]
        gdf_out = gdf_out[cols_presentes]
        if mode == "zonas":
            interv_col = None
            for c in ("intervencion_pi2024", "intervenido_pi2024"):
                if c in gdf_out.columns:
                    interv_col = c
                    break
            if interv_col:
                gdf_out["Intervenido PI2024"] = gdf_out[interv_col].map(format_si_no)
                gdf_out = gdf_out.drop(columns=[interv_col])
        # insertar al inicio
        gdf_out.insert(0, "distrito", display_admin(adm["distrito"]))
        gdf_out.insert(0, "provincia", display_admin(adm["provincia"]))
        gdf_out.insert(0, "departamento", display_admin(adm["departamento"]))
        gdf_out.insert(0, "ubigeo_gestor", u6)

        # escoger ruta de salida
        # (si no hay fila de catálogo, igual exporta usando el propio ubigeo como nombre)
        row_cat = cat.loc[cat["ubigeo"] == u6]
        row_cat = row_cat.iloc[0] if not row_cat.empty else pd.Series({})
        out_path = pick_filename_and_dirs(u6, row_cat, by_hierarchy, out_base)

        gdf_out.to_excel(out_path, index=False)

        # resumen
        try:
            rel = out_path.relative_to(out_base.parent.parent)   # relativo desde raíz del proyecto
            rel_str = str(rel)
        except Exception:
            rel_str = str(out_path)

        rows.append({
            "ubigeo_gestor": u6,
            "archivo_abs": str(out_path.resolve()),
            "archivo_rel": rel_str,
            "n_colegios": int(len(gdf))
        })

    return pd.DataFrame.from_records(rows)

# ---------------- CLI ----------------
def main():
    ap = argparse.ArgumentParser(description="Genera excels individuales por ubigeo_gestor.")
    ap.add_argument("--colegios-csv", default="./ZonasEscolares/processed/Colegios_priorizados_PI2026_clean.csv")
    ap.add_argument("--catalog-csv",  default="./data/municipalidades_catalog.csv")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--section-dir",  default="ZonasEscolares",
                    help="Carpeta de salida (ej: ZonasEscolares o Mantenimiento).")
    ap.add_argument("--by-hierarchy", action="store_true", help="Si se activa, anida en DEP/PROV/DIST.")
    ap.add_argument("--only-mantenimiento", action="store_true",
                    help="Si se activa, solo exporta filas con mantenimiento=True.")
    ap.add_argument("--only-implementacion", action="store_true",
                    help="Si se activa, solo exporta filas con implementacion=True.")
    args = ap.parse_args()

    root = Path(args.project_root)
    df_colegios = load_colegios_clean(Path(args.colegios_csv))
    cat = load_catalog(Path(args.catalog_csv))

    if args.only_mantenimiento:
        if "mantenimiento" not in df_colegios.columns:
            raise KeyError("El CSV de colegios no tiene la columna 'mantenimiento'.")
        df_colegios = df_colegios[df_colegios["mantenimiento"].map(to_bool_soft)].copy()
    if args.only_implementacion:
        if "implementacion" not in df_colegios.columns:
            raise KeyError("El CSV de colegios no tiene la columna 'implementacion'.")
        df_colegios = df_colegios[df_colegios["implementacion"].map(to_bool_soft)].copy()

    # Comprobación de cobertura (sin modificar nada)
    s_colegios = set(df_colegios["ubigeo_gestor"].dropna())
    s_catalogo = set(cat["ubigeo"].dropna())
    sin_match = sorted(u for u in s_colegios if u not in s_catalogo)
    if sin_match:
        print("[Aviso] Existen UBIGEO_gestor sin fila en el catálogo. Se exportarán igual con ubigeo como nombre de archivo:")
        print("  Ejemplos:", ", ".join(sin_match[:20]), ("... (+{})".format(len(sin_match)-20) if len(sin_match)>20 else ""))

    out_base = ensure_out_dirs(root, args.section_dir, args.by_hierarchy)
    mode = "mantenimiento" if args.only_mantenimiento else "zonas"
    resumen = export_excels(df_colegios, cat, out_base, args.by_hierarchy, mode)

    # Guardar un resumen de lo generado
    resumen_path = root / args.section_dir / "excels" / "_resumen_excels_por_muni.csv"
    resumen.to_csv(resumen_path, index=False, encoding="utf-8")

    print("\n=== EXCELS INDIVIDUALES GENERADOS ===")
    print(resumen.sort_values("ubigeo_gestor").to_string(index=False))
    print("\nResumen guardado en:", resumen_path)

if __name__ == "__main__":
    main()
