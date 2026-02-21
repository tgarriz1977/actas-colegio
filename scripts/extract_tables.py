#!/usr/bin/env python3
"""Extracción de tablas financieras con pdfplumber (fallback)."""

import csv
import sys
from pathlib import Path
import pdfplumber


def extract_financial_tables(pdf_path: str, output_dir: str = "output/tablas"):
    """Extrae tablas de presupuesto y tesorería."""
    
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📊 Extrayendo tablas de: {pdf_file.name}")
    
    tables_found = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table:
                    continue
                
                # Detectar si es tabla financiera (contiene $ o montos)
                is_financial = any(
                    '$' in str(cell) or 
                    any(c.isdigit() for c in str(cell))
                    for row in table for cell in row
                )
                
                if is_financial:
                    tables_found += 1
                    csv_file = output_path / f"{pdf_file.stem}_p{page_num}_t{table_idx}.csv"
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(table)
                    print(f"   💾 Tabla financiera guardada: {csv_file.name}")
    
    print(f"✅ Total tablas extraídas: {tables_found}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python extract_tables.py <ruta_al_pdf>")
        sys.exit(1)
    
    extract_financial_tables(sys.argv[1])
