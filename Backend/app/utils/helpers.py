"""
Funciones auxiliares para el backend.

Incluye generación de embeddings usando sentence-transformers localmente,
ya que OpenRouter no ofrece embeddings gratuitos.

También incluye saneamiento básico de texto para evitar inyección.
"""

from sentence_transformers import SentenceTransformer
import asyncio
import re

model = SentenceTransformer('all-MiniLM-L6-v2')

async def generar_embedding(texto: str) -> list:
    """
    Genera un embedding para un texto dado usando sentence-transformers.

    :param texto: Texto a vectorizar.
    :return: Lista de floats representando el embedding.
    """
    loop = asyncio.get_event_loop()
    embedding = await loop.run_in_executor(None, model.encode, texto)
    return embedding.tolist()

def sanitizar_texto(texto: str) -> str:
    """
    Sanitiza texto para evitar inyección y caracteres no deseados.

    :param texto: Texto original.
    :return: Texto sanitizado.
    """
    # Elimina caracteres no imprimibles y recorta espacios
    texto = re.sub(r'[^\x20-\x7E]+', ' ', texto)
    texto = texto.strip()
    return texto