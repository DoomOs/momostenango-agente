import os
import PyPDF2
from typing import List
from pgvector.psycopg2 import register_vector
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Cargar variables de entorno
ruta_env = Path('.') / '.env'
load_dotenv(dotenv_path=ruta_env)

# Configuración de PostgreSQL
HOST_POSTGRES = os.getenv("POSTGRES_HOST", "localhost")
BD_POSTGRES = os.getenv("POSTGRES_DB", "municipal_agent")
USUARIO_POSTGRES = os.getenv("POSTGRES_USER", "admin")
CONTRASENA_POSTGRES = os.getenv("POSTGRES_PASSWORD", "admin123")
PUERTO_POSTGRES = os.getenv("POSTGRES_PORT", "5432")

# Directorio MCP
DIRECTORIO_MCP = "../pdfs_mayo_2025"

# Cargar modelo de embeddings
modelo_embedding = SentenceTransformer('all-MiniLM-L6-v2')

def extraer_texto_pdf(ruta_pdf: str) -> str:
    texto = ""
    try:
        with open(ruta_pdf, "rb") as archivo:
            lector = PyPDF2.PdfReader(archivo)
            for pagina in lector.pages:
                texto += pagina.extract_text() or ""
    except Exception as e:
        print(f"Error al extraer texto de {ruta_pdf}: {e}")
    return texto

def obtener_todos_los_archivos(directorio: str) -> List[str]:
    rutas_archivos = []
    for raiz, _, archivos in os.walk(directorio):
        for archivo in archivos:
            ruta_archivo = os.path.join(raiz, archivo)
            rutas_archivos.append(ruta_archivo)
    return rutas_archivos

def generar_embedding(texto: str) -> List[float]:
    try:
        embedding = modelo_embedding.encode(texto).tolist()
        return embedding
    except Exception as e:
        print(f"Error al generar embedding: {e}")
        return None

def insertar_documento_en_bd(
    conexion, nombre_archivo: str, tipo: str, contenido: str, embedding: List[float]
):
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO documentos (nombre_archivo, tipo, contenido, embedding) VALUES (%s, %s, %s, %s)",
            (nombre_archivo, tipo, contenido, embedding),
        )
        conexion.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al insertar documento en la base de datos: {e}")
        conexion.rollback()

def procesar_mcp(directorio: str):
    rutas_archivos = obtener_todos_los_archivos(directorio)

    conexion = psycopg2.connect(
        host=HOST_POSTGRES,
        database=BD_POSTGRES,
        user=USUARIO_POSTGRES,
        password=CONTRASENA_POSTGRES,
        port=PUERTO_POSTGRES,
    )
    register_vector(conexion)

    for ruta_archivo in rutas_archivos:
        try:
            extension = Path(ruta_archivo).suffix.lower()
            nombre_archivo = os.path.basename(ruta_archivo)
            print(f"Procesando {nombre_archivo}...")

            if extension == ".pdf":
                contenido = extraer_texto_pdf(ruta_archivo)
                tipo = "pdf"
            elif extension == ".txt":
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                tipo = "texto"
            else:
                print(f"Tipo de archivo no soportado: {nombre_archivo}")
                continue

            if contenido.strip():
                embedding = generar_embedding(contenido)
                if embedding:
                    insertar_documento_en_bd(conexion, nombre_archivo, tipo, contenido, embedding)
                    print(f"Documento {nombre_archivo} procesado e insertado en la base de datos.")
                else:
                    print(f"No se pudo generar embedding para {nombre_archivo}.")
            else:
                print(f"No se pudo extraer contenido de {nombre_archivo}.")

        except Exception as e:
            print(f"Error al procesar {ruta_archivo}: {e}")

    conexion.close()
    print("Procesamiento del MCP completado.")

if __name__ == "__main__":
    procesar_mcp(DIRECTORIO_MCP)