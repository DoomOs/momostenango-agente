"""
Configuración del agente Agno con integración a OpenRouter LLM, búsqueda vectorial en PostgreSQL
y capacidad de búsqueda en internet con filtro geográfico(No funcino la busqueda por internet, el metodo para usar internet en un modelo de openrouter, no es compatibles con todos lo modelos y debe de usarse un tools).

Incluye gestión inteligente de contexto, fragmentación, resumen, y streaming.
"""

import os
import asyncio
import json as jsonlib
import numpy as np
import httpx
from openai import OpenAI
from app.db.crud import obtener_faqs
from app.utils.helpers import sanitizar_texto, generar_embedding

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class VectorSearchTool:
    """
    Herramienta para búsqueda vectorial en la tabla documentos usando pgvector.

    Permite consultas vectoriales en PostgreSQL para obtener documentos relevantes.
    """

    def __init__(self, pool):
        """
        Inicializa la herramienta con el pool de conexiones async a la base de datos.

        :param pool: Pool de conexiones async a PostgreSQL.
        """
        self.pool = pool

    async def search(self, query_embedding: list, top_k: int = 5):
        """
        Realiza búsqueda vectorial y devuelve documentos más relevantes.

        :param query_embedding: Embedding de la consulta (lista de floats).
        :param top_k: Número máximo de resultados a devolver.
        :return: Lista de diccionarios con documentos (id, nombre_archivo, contenido, distancia).
        """
        sql = """
            SELECT id, nombre_archivo, contenido,
                embedding <=> $1::vector AS distance
            FROM documentos
            ORDER BY embedding <=> $1::vector
            LIMIT $2;
            """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, query_embedding, top_k)
            
            rows = await conn.fetch(sql, query_embedding, top_k)
            print(f"[VectorSearchTool] recuperé {len(rows)} docs:", [r['nombre_archivo'] for r in rows])

            
            return [dict(row) for row in rows]


class AgnoMunicipalAgent:
    """
    Clase que encapsula el agente Agno configurado para el agente municipal.

    Integra modelo LLM OpenRouter, búsqueda vectorial, gestión de contexto,
    resumen, fragmentación, filtrado y búsqueda en internet con filtro geográfico.
    """

    def __init__(self, pool, api_key: str):
        """
        Inicializa el agente con cliente OpenAI para OpenRouter y búsqueda vectorial.

        :param pool: Pool de conexiones async a PostgreSQL.
        :param api_key: API key para OpenRouter.
        """
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model_id = "deepseek/deepseek-r1-0528-qwen3-8b:free"
        self.enable_search = True
        self.pool = pool
        self.api_key = api_key
        self.vector_tool = VectorSearchTool(pool)

        self.prompt_inicial = (
            "Eres un asistente municipal experto en los diversos trámites, servicios, reglamentos y aspectos operativos que competen al gobierno local de Momostenango, en el departamento de Totonicapán, Guatemala. "
            "Tu rol es proporcionar información precisa, actualizada y relevante sobre cualquier gestión que los ciudadanos, empresas o visitantes requieran realizar ante la municipalidad. Esto abarca, pero no se restringe a: "
            "1.  **Impuestos y Arbitrios:** Como el pago del Impuesto Único sobre Inmuebles (IUSI) y el Boleto de Ornato (impuesto paga financiar obras de intraestructura urbana). "
            "2.  **Licencias y Permisos:** Incluyendo licencias de construcción, demolición, ampliación, permisos de funcionamiento para negocios (comerciales, industriales, de servicios), autorizaciones para vallas publicitarias, etc. "
            "3.  **Servicios Básicos:** Gestión y contratación de servicios de agua potable, alcantarillado, recolección de desechos sólidos (tren de aseo), alumbrado público y mantenimiento de infraestructura municipal. "
            "4.  **Certificaciones y Constancias:** **Solvencias municipales**, certificaciones de ubicación de inmuebles, certificaciones de carencia de bienes y otros documentos oficiales emitidos por la municipalidad. "
            "5.  **Asuntos Generales:** Orientación sobre normativas municipales, denuncias ante el Juzgado de Asuntos Municipales, y cualquier otro procedimiento administrativo local. "
            "Además de los trámites, debes poder indicar **dónde preguntar X cosa** o **en qué oficina se realiza cierto trámite** dentro de la municipalidad. "
            "La información de contacto y ubicación de la Municipalidad de Momostenango es la siguiente: "
            "**Dirección Física:** 2 Avenida 1-99 Z.1, Momostenango, Totonicapán. "
            "**Número de Teléfono:** +502 7790 9595 "
            "**Sitio Web Oficial:** http://www.municipalidaddemomostenango.gob.gt/ "
            "**Ubicación en Google Maps:** https://www.google.com/maps/place/Municipalidad+de+Momostenango/@15.044874,-91.4091031,18z/data=!4m6!3m5!1s0x858c1de77ae7dee7:0xc2e4f22b8c447754!8m2!3d15.0450231!4d-91.408522!16s%2Fg%2F11fs19cdrx?entry=ttu&g_ep=EgoyMDI1MDYxMS4wIKXMDSoASAFQAw%3D%3D " 
            "Debes responder ÚNICAMENTE preguntas que estén directamente relacionadas con el ámbito municipal de Momostenango o que sean aplicables al contexto de funcionamiento de su municipalidad. "
            "Tu comunicación debe ser clara, profesional, exacta y fácil de comprender, adaptada a usuarios con diferentes niveles de conocimiento, como vecinos, prestadores de servicios, inversionistas o cualquier persona que busque información o realizar un trámite municipal."
        )


    def contar_tokens(self, texto: str) -> int:
        """
        Cuenta tokens aproximados en un texto dividiendo por espacios.

        :param texto: Texto a contar tokens.
        :return: Número aproximado de tokens.
        """
        return len(texto.split())

    def filtro_basico(self, pregunta: str) -> bool:
        """
        Filtra preguntas que contengan palabras prohibidas para evitar abusos o temas sensibles.

        :param pregunta: Texto de la pregunta.
        :return: True si la pregunta es válida, False si contiene palabras prohibidas.
        """
        blacklist = [
            "hack", "jailbreak", "exploit", "bypass", "root", "sudo",
            "password", "token", "api key", "secret", "crack",
            "kill", "attack", "bomb", "terrorist", "illegal"
        ]
        pregunta_lower = pregunta.lower()
        for palabra in blacklist:
            if palabra in pregunta_lower:
                return False
        return True

    async def resumir_texto_largo(self, texto: str, max_tokens: int = 500) -> str:
        """
        Usa el modelo para resumir texto largo y reducir tokens.

        :param texto: Texto largo a resumir.
        :param max_tokens: Máximo tokens para el resumen.
        :return: Texto resumido.
        """
        prompt = (
            "Resume el siguiente texto para que sea más corto pero manteniendo la información importante:\n\n"
            f"{texto}\n\nResumen:"
        )
        try:
            completion = await self.client.chat.completions.acreate(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            resumen = completion.choices[0].message.content
            return resumen
        except Exception:
            # En caso de error, devolver texto original truncado
            return texto[:max_tokens*4]

    async def fragmentar_y_filtrar_texto(self, texto: str, pregunta: str, max_fragmentos: int = 5, max_tokens_fragmento: int = 300):
        """
        Divide texto en fragmentos, genera embeddings y selecciona los más relevantes para la pregunta.

        :param texto: Texto largo a fragmentar.
        :param pregunta: Pregunta para generar embedding y comparar relevancia.
        :param max_fragmentos: Número máximo de fragmentos a seleccionar.
        :param max_tokens_fragmento: Máximo tokens por fragmento.
        :return: Texto concatenado con fragmentos relevantes, resumido si es muy largo.
        """
        lineas = texto.split('\n')
        fragmentos = []
        buffer = []
        tokens_buffer = 0

        for linea in lineas:
            tokens_linea = self.contar_tokens(linea)
            if tokens_buffer + tokens_linea > max_tokens_fragmento:
                fragmentos.append(" ".join(buffer))
                buffer = [linea]
                tokens_buffer = tokens_linea
            else:
                buffer.append(linea)
                tokens_buffer += tokens_linea
        if buffer:
            fragmentos.append(" ".join(buffer))

        embedding_pregunta = await generar_embedding(pregunta)

        fragmentos_embeddings = []
        for frag in fragmentos:
            emb = await generar_embedding(frag)
            fragmentos_embeddings.append((frag, emb))

        def similitud_coseno(a, b):
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        fragmentos_ordenados = sorted(
            fragmentos_embeddings,
            key=lambda x: similitud_coseno(embedding_pregunta, x[1]),
            reverse=True
        )

        seleccionados = [f[0] for f in fragmentos_ordenados[:max_fragmentos]]

        contexto = "\n".join(seleccionados)
        if self.contar_tokens(contexto) > 1000:
            contexto = await self.resumir_texto_largo(contexto, max_tokens=500)

        return contexto

    async def responder_stream(self, pregunta: str, embedding=None, contexto_adicional: str = ""):
        """
        Responde a una pregunta con streaming real desde OpenRouter.

        Integra búsqueda vectorial en MCP, FAQs y contexto adicional,
        limita contexto y envía fragmentos de respuesta en tiempo real.

        :param pregunta: Pregunta del usuario.
        :param embedding: Embedding de la pregunta (opcional).
        :param contexto_adicional: Texto adicional para contexto (opcional).
        :yield: Fragmentos de texto codificados en utf-8.
        """
        pregunta = sanitizar_texto(pregunta)
        if not self.filtro_basico(pregunta):
            yield "Lo siento, no puedo responder esa pregunta.".encode("utf-8")
            return

        docs = []
        if embedding:
            docs = await self.vector_tool.search(embedding, top_k=5)

        faqs = await obtener_faqs(limit=5)

        contexto_docs = "\n".join([doc['contenido'] for doc in docs])
        contexto_faqs = "\n".join([f"Q: {f['pregunta']} A: {f['respuesta']}" for f in faqs])

        contexto_adicional_filtrado = ""
        if contexto_adicional:
            contexto_adicional_filtrado = await self.fragmentar_y_filtrar_texto(contexto_adicional, pregunta)

        contexto_completo = (
            f"{self.prompt_inicial}\n\n"
            f"Documentos relevantes:\n{contexto_docs}\n\n"
            f"FAQs relevantes:\n{contexto_faqs}\n\n"
            f"Contexto adicional:\n{contexto_adicional_filtrado}"
        )

        if self.contar_tokens(contexto_completo) > 1000:
            contexto_completo = await self.resumir_texto_largo(contexto_completo, max_tokens=700)

        system_prompt = (
            "Eres un asistente municipal que responde solo preguntas relacionadas con "
            "servicios, trámites y normativas municipales. No respondas preguntas sobre noticias, "
            "temas políticos, ni información fuera del contexto municipal."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": contexto_completo},
            {"role": "user", "content": pregunta},
        ]

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        # Leer el contenido del stream y enviarlo como un solo fragmento
                        full_text = await response.aread()
                        text = full_text.decode('utf-8')
                        yield f"Error del servidor: {text}".encode("utf-8")
                        return

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while True:
                            line_end = buffer.find('\n')
                            if line_end == -1:
                                break
                            line = buffer[:line_end].strip()
                            buffer = buffer[line_end + 1:]
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    return
                                try:
                                    data_obj = jsonlib.loads(data)
                                    content = data_obj["choices"][0]["delta"].get("content")
                                    if content:
                                        yield content.encode("utf-8")
                                except jsonlib.JSONDecodeError:
                                    # Ignorar líneas mal formadas
                                    pass
        except Exception as e:
            yield f"Error en la comunicación con el agente: {e}".encode("utf-8")

    async def buscar_en_internet(self, pregunta: str) -> str:
        """
        Realiza búsqueda en internet restringida a Guatemala para evitar contexto erróneo.

        :param pregunta: Pregunta del usuario.
        :return: Texto con resultados resumidos o mensaje de error.
        """
        pregunta_filtrada = f"{pregunta} site:gt OR Guatemala"
        messages = [
            {"role": "system", "content": "Eres un asistente que puede buscar en internet para responder preguntas, "
                                          "pero solo debes usar información relevante de Guatemala."},
            {"role": "user", "content": pregunta_filtrada}
        ]

        try:
            completion = await self.client.chat.completions.acreate(
                model=self.model_id,
                messages=messages,
                tools=[{
                    "name": "Web Search",
                    "description": "Busca información en internet",
                    "parameters": {
                        "query": pregunta_filtrada,
                        "max_results": 3
                    }
                }],
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error buscando en internet: {str(e)}"