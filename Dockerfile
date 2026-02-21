FROM python:3.11-slim

WORKDIR /app

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

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
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instalar docling con soporte OCR (versión específica para estabilidad)
RUN pip install --no-cache-dir "docling>=2.0.0,<3.0.0"

# Copiar scripts y datos
COPY scripts/ ./scripts/
COPY ActasColegio/ ./ActasColegio/

# Crear directorio de salida
RUN mkdir -p output

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Entrypoint por defecto
ENTRYPOINT ["python", "-m", "scripts.process_acta"]
CMD ["--help"]
