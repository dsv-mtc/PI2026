# run_all.py
import subprocess
import sys
from pathlib import Path

# Orden en que se deben ejecutar los scripts
SCRIPTS_IN_ORDER = [
    "municipalidades_build.py",        # 1) construye municipalidades
    "process_colegios.py",             # 2) procesa colegios
    "split_establecimientos_to_excels.py",  # 3) splits
    "split_excels_por_muni.py",
    ["split_excels_por_muni.py", "--only-mantenimiento", "--section-dir", "Mantenimiento"],
    "split_intersecciones_to_excels.py",
    "maps_establecimientos.py",        # 4) maps
    "maps_colegios.py",
    ["maps_colegios.py", "--excels-dir", "./Mantenimiento/excels", "--out-dir", "./Mantenimiento/maps", "--mode", "mantenimiento"],
    "maps_intersecciones.py",
    "build_resumen_excels.py",         # 5) resumenes excel
    "build_site.py",                   # 6) sitio final
    "cache_bust.py"                    # 7) cache busting
]

def run_script(script_cmd):
    if isinstance(script_cmd, (list, tuple)):
        script_name = script_cmd[0]
        extra_args = list(script_cmd[1:])
    else:
        script_name = script_cmd
        extra_args = []

    script_path = Path(__file__).parent / script_name
    print(f"\n=== Ejecutando: {script_path.name} ===")

    # Llama a cada script con el mismo interprete de Python
    result = subprocess.run(
        [sys.executable, str(script_path), *extra_args],
        check=True
    )

    print(f"Terminado: {script_path.name}")
    return result

def main():
    for script in SCRIPTS_IN_ORDER:
        try:
            run_script(script)
        except subprocess.CalledProcessError as e:
            print(f"\nError ejecutando {script}. Codigo de salida: {e.returncode}")
            # Si quieres que se detenga todo al primer error, dejamos el break:
            break

if __name__ == "__main__":
    main()
