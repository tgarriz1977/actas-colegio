#!/usr/bin/env python3
"""Procesa todas las actas en batch."""

import os
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Añadir el directorio scripts al path
sys.path.insert(0, str(Path(__file__).parent))

from process_acta import process_acta


def process_all_actas(input_dir: str = "ActasColegio", max_workers: int = 4):
    """Procesa todas las actas en paralelo."""
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"❌ Error: Directorio no encontrado: {input_dir}")
        sys.exit(1)
    
    pdf_files = list(input_path.glob("*.pdf"))
    total = len(pdf_files)
    
    if total == 0:
        print(f"⚠️  No se encontraron PDFs en {input_dir}")
        return
    
    print(f"🚀 Procesando {total} actas con {max_workers} workers...\n")
    
    completed = 0
    failed = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_acta, str(pdf)): pdf 
            for pdf in pdf_files
        }
        
        for future in as_completed(futures):
            pdf = futures[future]
            try:
                future.result()
                completed += 1
                print(f"   ✅ Progreso: {completed}/{total}")
            except Exception as e:
                failed.append((pdf.name, str(e)))
                print(f"   ❌ Error en {pdf.name}: {e}")
    
    print(f"\n" + "="*60)
    print(f"📊 RESUMEN DEL PROCESAMIENTO")
    print(f"="*60)
    print(f"   Total actas: {total}")
    print(f"   Completadas: {completed}")
    print(f"   Fallidas: {len(failed)}")
    print(f"   Éxito: {completed/total*100:.1f}%")
    
    if failed:
        print(f"\n❌ Archivos con error:")
        for name, error in failed:
            print(f"   - {name}")
            print(f"     Error: {error[:100]}...")
    
    print(f"\n📁 Resultados guardados en: output/")


if __name__ == "__main__":
    process_all_actas()
