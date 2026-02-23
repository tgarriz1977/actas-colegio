import os
import re

# Configuración
path_local = "./ActasColegio"  # Cambia esto a tu ruta real
rango_mesa_inicio = 834
rango_mesa_fin = 968

def obtener_actas_descargadas(ruta):
    archivos = os.listdir(ruta)
    # Buscamos números de 3 cifras en los nombres de archivos
    numeros = []
    for f in archivos:
        # Filtramos para evitar las actas de Consejo Superior (CS) en este conteo
        if "CS" not in f.upper():
            match = re.search(r'(\d{3})', f)
            if match:
                numeros.append(int(match.group(1)))
    return sorted(list(set(numeros)))

def verificar_faltantes():
    descargadas = obtener_actas_descargadas(path_local)
    faltantes = [n for n in range(rango_mesa_inicio, rango_mesa_fin + 1) if n not in descargadas]
    
    print(f"--- Reporte de Actas de Mesa ---")
    print(f"Total esperado: {rango_mesa_fin - rango_mesa_inicio + 1}")
    print(f"Total encontrado: {len(descargadas)}")
    print(f"Total faltante: {len(faltantes)}")
    
    if faltantes:
        print("\nNúmeros que debes buscar en los mails de Lautaro:")
        # Agrupar para no hacer una lista gigante
        print(faltantes)

if __name__ == "__main__":
    if os.path.exists(path_local):
        verificar_faltantes()
    else:
        print("La ruta especificada no existe.")
