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
    "split_intersecciones_to_excels.py",
    "maps_establecimientos.py",        # 4) maps
    "maps_colegios.py",        # (nombre con espacio, igual funciona)
    "maps_intersecciones.py",
    "build_resumen_excels.py",        # 5) resúmenes excel
    "build_site.py",                   # 6) sitio final
]

def run_script(script_name: str):
    script_path = Path(__file__).parent / script_name
    print(f"\n=== Ejecutando: {script_path.name} ===")

    # Llama a cada script con el mismo intérprete de Python
    result = subprocess.run(
        [sys.executable, str(script_path)],
        check=True
    )

    print(f"✔ Terminado: {script_path.name}")
    return result

def main():
    for script in SCRIPTS_IN_ORDER:
        try:
            run_script(script)
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error ejecutando {script}. Código de salida: {e.returncode}")
            # Si quieres que se detenga todo al primer error, dejamos el break:
            break

if __name__ == "__main__":
    main()
