import os
import re
import shutil

# Configuración
path_local = "./ActasColegio"

# Rangos definidos según la información de tus correos
MAPEO_ACTAS = {
    "2023": range(834, 874),
    "2024": range(874, 931),
    "2025": range(931, 969)
}

def obtener_ruta_unica(ruta_final):
    """Si el archivo ya existe, genera un nombre nuevo para no sobrescribir."""
    base, ext = os.path.splitext(ruta_final)
    contador = 1
    nueva_ruta = ruta_final
    while os.path.exists(nueva_ruta):
        nueva_ruta = f"{base}_copy{contador}{ext}"
        contador += 1
    return nueva_ruta

def organizar_actas():
    # 1. Crear las carpetas de los años
    for anio in MAPEO_ACTAS.keys():
        folder_path = os.path.join(path_local, anio)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # 2. Procesar los archivos
    archivos = [f for f in os.listdir(path_local) if os.path.isfile(os.path.join(path_local, f))]
    
    for nombre_original in archivos:
        if nombre_original.startswith('.'): continue

        # Extraer número: busca después de ACTA, N°, ME o al inicio
        match = re.search(r'(?:ACTA|N°|ME|CS)?\s*(\d{3,4})', nombre_original.upper())
        
        if match:
            num = int(match.group(1))
            anio_destino = None
            tipo = "ACTA_CS" if "CS" in nombre_original.upper() else "ACTA_ME"
            
            # Lógica para actas de Mesa (ME)
            for anio, rango in MAPEO_ACTAS.items():
                if num in rango:
                    anio_destino = anio
                    break
            
            # Lógica específica para CS si no cayó en rango ME (usan numeración distinta)
            if not anio_destino and tipo == "ACTA_CS":
                match_anio_cs = re.search(r'(2023|2024|2025)', nombre_original)
                if match_anio_cs:
                    anio_destino = match_anio_cs.group(1)

            if anio_destino:
                nuevo_nombre = f"{tipo}_{num}_{anio_destino}.pdf"
                path_viejo = os.path.join(path_local, nombre_original)
                path_destino_final = os.path.join(path_local, anio_destino, nuevo_nombre)
                
                # Validar duplicados
                path_final_unico = obtener_ruta_unica(path_destino_final)
                
                print(f"Moviendo: {nombre_original} -> {os.path.relpath(path_final_unico, path_local)}")
                shutil.move(path_viejo, path_final_unico)
            else:
                print(f"⚠️ No se pudo clasificar por año: {nombre_original}")
        else:
            print(f"❌ No se encontró número en: {nombre_original}")

if __name__ == "__main__":
    if os.path.exists(path_local):
        organizar_actas()
        print("\n✅ Estructura de carpetas actualizada.")
    else:
        print(f"Error: La carpeta {path_local} no existe.")
