# AGENTS.md - ActasColegio

> Documentación técnica para despliegue en cluster con Docling OCR

## 🎯 Propósito del Proyecto

Sistema de procesamiento de actas del Colegio de Técnicos de la Provincia de Buenos Aires.
- **Entrada**: 46 archivos PDF escaneados (~286 MB)
- **Proceso**: OCR + extracción estructurada de tablas financieras
- **Salida**: Datos estructurados (JSON/Markdown) para análisis y archivo

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         VM / Cluster                             │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │   PDFs Originales│───▶│  Docling OCR     │───▶│  Output     │ │
│  │   /ActasColegio/ │    │  + pdfplumber    │    │  /output/   │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
│           │                      │                     │        │
│           ▼                      ▼                     ▼        │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │  Git Repo       │    │  Redis/Queue     │    │  PostgreSQL │ │
│  │  (versionado)   │    │  (workers OCR)   │    │  (metadata) │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Directorios

```
/home/tgarriz/lab/colegio/actasColegio/
├── ActasColegio/              # PDFs originales (46 archivos)
│   ├── ACTA CS-592-13-7-2023.pdf
│   ├── ...
│   └── ACTA CS-634-11-12-2025 Firmada.pdf
├── output/                    # Resultados OCR (generado)
│   ├── json/                  # Extracción estructurada
│   ├── markdown/              # Texto formateado
│   └── tablas/                # CSVs de tablas financieras
├── scripts/                   # Scripts de procesamiento
│   ├── process_acta.py        # Procesador individual
│   ├── batch_process.py       # Procesamiento batch
│   └── extract_tables.py      # Extracción de tablas
├── k8s/                       # Kubernetes manifests
│   ├── docling-deployment.yaml
│   ├── docling-service.yaml
│   └── job-ocr-batch.yaml
├── Dockerfile                 # Imagen de Docling
├── requirements.txt           # Dependencias Python
├── README.md                  # Documentación usuario
└── AGENTS.md                  # Este archivo
```

## 🐳 Build de Docling

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar docling con soporte OCR
RUN pip install --no-cache-dir docling[pdf,tesseract]>=2.0.0

# Copiar scripts
COPY scripts/ ./scripts/
COPY ActasColegio/ ./ActasColegio/

# Entrypoint
ENTRYPOINT ["python", "-m", "scripts.process_acta"]
```

### requirements.txt
```txt
docling>=2.0.0
pdfplumber>=0.10.0
pymupdf>=1.23.0
pandas>=2.0.0
openpyxl>=3.1.0
tabulate>=0.9.0
click>=8.0.0
pydantic>=2.0.0
```

## 🚀 Deployment en Cluster

### 1. Build y push de imagen
```bash
# En la VM con acceso al registry del cluster
docker build -t registry.cluster.local/actas-colegio/docling:latest .
docker push registry.cluster.local/actas-colegio/docling:latest
```

### 2. Deploy Docling Service
```bash
kubectl apply -f k8s/docling-deployment.yaml
kubectl apply -f k8s/docling-service.yaml
```

### 3. Ejecutar batch OCR
```bash
kubectl apply -f k8s/job-ocr-batch.yaml
```

## 🔧 Scripts Principales

### `scripts/process_acta.py`
Procesa un acta individual con Docling:

```python
#!/usr/bin/env python3
"""Procesa un acta PDF con Docling OCR."""

import json
import sys
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult


def process_acta(pdf_path: str, output_dir: str = "output"):
    """Procesa un PDF de acta y extrae texto y tablas."""
    
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convertir con Docling
    converter = DocumentConverter()
    result = converter.convert(str(pdf_file))
    
    # Exportar a Markdown
    markdown = result.document.export_to_markdown()
    md_file = output_path / f"{pdf_file.stem}.md"
    md_file.write_text(markdown, encoding="utf-8")
    
    # Exportar a JSON estructurado
    json_data = {
        "acta_numero": pdf_file.stem,
        "pages": len(result.document.pages),
        "tables": [],
        "text": markdown
    }
    
    # Extraer tablas si existen
    for table_idx, table in enumerate(result.document.tables):
        table_data = {
            "index": table_idx,
            "rows": []
        }
        # Procesar celdas de la tabla
        for row in table.data:
            row_data = [cell.text for cell in row]
            table_data["rows"].append(row_data)
        json_data["tables"].append(table_data)
    
    # Guardar JSON
    json_file = output_path / "json" / f"{pdf_file.stem}.json"
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ Procesado: {pdf_file.name}")
    print(f"   Markdown: {md_file}")
    print(f"   JSON: {json_file}")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python process_acta.py <ruta_al_pdf>")
        sys.exit(1)
    
    process_acta(sys.argv[1])
```

### `scripts/extract_tables.py`
Extracción especializada de tablas con pdfplumber (fallback):

```python
#!/usr/bin/env python3
"""Extracción de tablas financieras con pdfplumber."""

import csv
import sys
from pathlib import Path
import pdfplumber


def extract_financial_tables(pdf_path: str, output_dir: str = "output/tablas"):
    """Extrae tablas de presupuesto y tesorería."""
    
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
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
                    csv_file = output_path / f"{pdf_file.stem}_p{page_num}_t{table_idx}.csv"
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(table)
                    print(f"   📊 Tabla guardada: {csv_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python extract_tables.py <ruta_al_pdf>")
        sys.exit(1)
    
    extract_financial_tables(sys.argv[1])
```

### `scripts/batch_process.py`
Procesamiento batch de todas las actas:

```python
#!/usr/bin/env python3
"""Procesa todas las actas en batch."""

import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from process_acta import process_acta


def process_all_actas(input_dir: str = "ActasColegio", max_workers: int = 4):
    """Procesa todas las actas en paralelo."""
    
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    total = len(pdf_files)
    
    print(f"🚀 Procesando {total} actas con {max_workers} workers...")
    
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
                print(f"   ✅ {completed}/{total} completado")
            except Exception as e:
                failed.append((pdf.name, str(e)))
                print(f"   ❌ Error en {pdf.name}: {e}")
    
    print(f"\n📊 Resumen:")
    print(f"   Completados: {completed}/{total}")
    print(f"   Fallidos: {len(failed)}")
    
    if failed:
        print("\n❌ Archivos con error:")
        for name, error in failed:
            print(f"   - {name}: {error}")


if __name__ == "__main__":
    process_all_actas()
```

## ⚙️ Configuración del Cluster

### k8s/docling-deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docling-ocr
  namespace: actas-colegio
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docling-ocr
  template:
    metadata:
      labels:
        app: docling-ocr
    spec:
      containers:
      - name: docling
        image: registry.cluster.local/actas-colegio/docling:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        volumeMounts:
        - name: pdfs
          mountPath: /app/ActasColegio
        - name: output
          mountPath: /app/output
      volumes:
      - name: pdfs
        persistentVolumeClaim:
          claimName: actas-pdfs-pvc
      - name: output
        persistentVolumeClaim:
          claimName: actas-output-pvc
```

### k8s/job-ocr-batch.yaml
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ocr-batch-job
  namespace: actas-colegio
spec:
  template:
    spec:
      containers:
      - name: processor
        image: registry.cluster.local/actas-colegio/docling:latest
        command: ["python", "scripts/batch_process.py"]
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
        volumeMounts:
        - name: pdfs
          mountPath: /app/ActasColegio
        - name: output
          mountPath: /app/output
      volumes:
      - name: pdfs
        persistentVolumeClaim:
          claimName: actas-pdfs-pvc
      - name: output
        persistentVolumeClaim:
          claimName: actas-output-pvc
      restartPolicy: Never
  backoffLimit: 3
```

## 🔍 Comandos Útiles

### En la VM

```bash
# Activar entorno
source /home/tgarriz/lab/colegio/actasColegio/venv/bin/activate

# Procesar una acta individual
python scripts/process_acta.py ActasColegio/ACTA\ CS-592-13-7-2023.pdf

# Extraer solo tablas
python scripts/extract_tables.py ActasColegio/ACTA\ CS-592-13-7-2023.pdf

# Procesar todas (local)
python scripts/batch_process.py

# Verificar resultado
ls -la output/json/
ls -la output/tablas/
```

### En el Cluster

```bash
# Verificar pods
kubectl get pods -n actas-colegio

# Logs del procesamiento
kubectl logs -n actas-colegio -l app=docling-ocr

# Seguir job batch
kubectl logs -n actas-colegio -f job/ocr-batch-job

# Copiar resultados del cluster
kubectl cp -n actas-colegio docling-ocr-xxx:/app/output ./output

# Escalar workers
kubectl scale deployment docling-ocr --replicas=5 -n actas-colegio
```

## 🧪 Validación de OCR

### Verificar calidad de extracción
```bash
# Comparar valores clave del Acta 592
grep -A5 "Ingreso C.E.P" output/markdown/ACTA\ CS-592-13-7-2023.md
grep -A5 "TOTAL RECAUDADO" output/markdown/ACTA\ CS-592-13-7-2023.md

# Validar JSON estructurado
python -m json.tool output/json/ACTA\ CS-592-13-7-2023.json > /dev/null && echo "✅ JSON válido"

# Verificar tablas CSV
head -10 output/tablas/ACTA\ CS-592-13-7-2023_p5_t0.csv
```

## 📝 Notas Importantes

1. **Docling requiere GPU** para OCR óptimo. Si no hay GPU disponible, usar CPU con `max_workers` reducido.

2. **Tablas complejas**: Las tablas financieras con celdas fusionadas pueden requerir post-procesamiento manual.

3. **Memoria**: Los PDFs escaneados grandes (>50MB) requieren ~4GB RAM por archivo.

4. **Tesseract**: El OCR en español requiere `tesseract-ocr-spa` instalado.

5. **Git LFS**: Los PDFs están versionados con Git LFS. Asegurar que `git lfs pull` se ejecute antes del procesamiento.

## 🔗 Recursos

- Docling: https://github.com/DS4SD/docling
- pdfplumber: https://github.com/jsvine/pdfplumber
- Dataset: 46 actas CTPBA (2023-2025)
