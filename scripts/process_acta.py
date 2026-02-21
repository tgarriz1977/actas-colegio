#!/usr/bin/env python3
"""Procesa un acta PDF con Docling OCR."""

import json
import sys
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat


def process_acta(pdf_path: str, output_dir: str = "output"):
    """Procesa un PDF de acta y extrae texto y tablas."""
    
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📄 Procesando: {pdf_file.name}")
    
    # Convertir con Docling
    converter = DocumentConverter()
    result = converter.convert(str(pdf_file))
    
    # Exportar a Markdown
    markdown = result.document.export_to_markdown()
    md_file = output_path / "markdown" / f"{pdf_file.stem}.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text(markdown, encoding="utf-8")
    print(f"   📝 Markdown: {md_file}")
    
    # Exportar a JSON estructurado
    json_data = {
        "acta_numero": pdf_file.stem,
        "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
        "tables": [],
        "text": markdown
    }
    
    # Extraer tablas si existen
    if hasattr(result.document, 'tables'):
        for table_idx, table in enumerate(result.document.tables):
            table_data = {
                "index": table_idx,
                "rows": []
            }
            # Procesar celdas de la tabla
            if hasattr(table, 'data'):
                for row in table.data:
                    row_data = [cell.text for cell in row] if row else []
                    table_data["rows"].append(row_data)
            json_data["tables"].append(table_data)
    
    # Guardar JSON
    json_file = output_path / "json" / f"{pdf_file.stem}.json"
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   📊 JSON: {json_file}")
    
    print(f"✅ Completado: {pdf_file.name}\n")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python process_acta.py <ruta_al_pdf>")
        sys.exit(1)
    
    process_acta(sys.argv[1])
