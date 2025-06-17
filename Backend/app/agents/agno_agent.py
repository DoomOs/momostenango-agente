"""
Configuración del agente Agno con integración a OpenRouter LLM y búsqueda vectorial en PostgreSQL.

Incluye herramientas para:
- Búsqueda vectorial en documentos.
- Consulta de FAQs.
- Lógica para derivar a humano si confianza es baja.
"""

import os
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from app.db.connection import db
from app.db.crud import obtener_faqs
from app.utils.helpers import sanitizar_texto


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class VectorSearchTool:
    """
    Herramienta para búsqueda vectorial en la tabla documentos usando pgvector.

    Esta clase permite realizar consultas vectoriales en la base de datos PostgreSQL
    para obtener documentos relevantes según un embedding de consulta.
    """

    def __init__(self, pool):
        """
        Inicializa la herramienta con el pool de conexiones a la base de datos.

        :param pool: Pool de conexiones async a PostgreSQL.
        """
        self.pool = pool

    async def search(self, query_embedding: list, top_k: int = 5):
        """
        Realiza búsqueda vectorial y devuelve documentos más relevantes.

        :param query_embedding: Embedding de la consulta (lista de floats).
        :param top_k: Número de resultados a devolver.
        :return: Lista de diccionarios con documentos que incluyen id, nombre_archivo, contenido y distancia.
        """
        sql = """
        SELECT id, nombre_archivo, contenido, embedding <=> $1 AS distance
        FROM documentos
        ORDER BY embedding <=> $1
        LIMIT $2;
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, query_embedding, top_k)
            return [dict(row) for row in rows]


class AgnoMunicipalAgent:
    """
    Clase que encapsula el agente Agno configurado para el agente municipal.

    Integra un modelo LLM gratuito de OpenRouter y herramientas de búsqueda vectorial
    y FAQs para responder preguntas de ciudadanos con contexto relevante.
    """

    def __init__(self):
        """
        Inicializa el agente con el modelo OpenRouter gratuito y la herramienta de búsqueda vectorial.
        """
        self.llm = OpenRouter(id=":free", api_key=OPENROUTER_API_KEY)
        self.agent = Agent(model=self.llm, markdown=True)
        self.vector_tool = VectorSearchTool(db.pool)

    async def responder(self, pregunta: str, embedding: list):
        """
        Método principal para responder preguntas.

        1. Sanitiza la pregunta.
        2. Busca documentos relevantes con búsqueda vectorial.
        3. Obtiene FAQs para respuestas rápidas.
        4. Construye un contexto combinando documentos y FAQs.
        5. Genera respuesta con el LLM.
        6. Evalúa confianza y decide si derivar a humano.

        :param pregunta: Pregunta del usuario en texto plano.
        :param embedding: Embedding de la pregunta para búsqueda vectorial.
        :return: Diccionario con la respuesta generada, nivel de confianza y flag para derivar a humano.
        """
        pregunta = sanitizar_texto(pregunta)

        # Buscar documentos relevantes
        docs = await self.vector_tool.search(embedding)

        # Obtener FAQs
        faqs = await obtener_faqs(limit=5)

        # Construir contexto para LLM
        contexto_docs = "\n".join([doc['contenido'] for doc in docs])
        contexto_faqs = "\n".join([f"Q: {f['pregunta']} A: {f['respuesta']}" for f in faqs])
        contexto = f"Contexto:\n{contexto_docs}\nFAQs:\n{contexto_faqs}"

        prompt = f"{contexto}\n\nPregunta: {pregunta}\nRespuesta:"

        # Generar respuesta con LLM
        respuesta = await self.agent.run(prompt)

        # Simulación de confianza (en producción usar métricas reales)
        confianza = 0.8

        derivar_humano = confianza < 0.6

        return {
            "respuesta": respuesta.text,
            "confianza": confianza,
            "derivar_humano": derivar_humano
        }