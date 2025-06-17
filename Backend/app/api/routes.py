import os
import re
import io
import uuid
import asyncio
import PyPDF2

from blacksheep import Response, Request, StreamedContent
from blacksheep.server.responses import json, text
from app.db.crud import (
    crear_sesion,
    guardar_consulta_respuesta,
    obtener_ciudadano_por_email,
    crear_ciudadano,
    obtener_sesion_por_token,
)
from app.utils.helpers import generar_embedding, sanitizar_texto
from app.agents.agno_agent import AgnoMunicipalAgent

import logging
logger = logging.getLogger("upload")
# Variable global para la instancia del agente, se inicializa en startup
agent_instance = None

# Variable temporal para almacenar el texto del PDF
pdf_text_temp = ""

# Estado simple en memoria para simular bloqueo por derivación a humano
conversaciones_derivadas = set()

async def init_agent():
    """
    Inicializa la instancia global del agente AgnoMunicipalAgent.
    """
    global agent_instance
    from app.db.connection import db

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise RuntimeError("La variable de entorno OPENROUTER_API_KEY no está configurada")

    agent_instance = AgnoMunicipalAgent(db.pool, OPENROUTER_API_KEY)


async def parse_confianza(respuesta: str) -> float:
    """
    Extrae un valor de confianza numérico de la respuesta del agente.

    :param respuesta: Texto de la respuesta.
    :return: Valor de confianza entre 0 y 1.
    """
    match = re.search(r"Confianza[:\s]+(\d+(\.\d+)?)(%)?", respuesta, re.IGNORECASE)
    if match:
        valor = float(match.group(1))
        if match.group(3) == '%':
            return valor / 100
        return valor
    return 0.8


async def chat(request: Request) -> Response:
    """
    Endpoint POST /chat para interactuar con el agente municipal.

    Recibe JSON con pregunta, ciudadano_id y token_sesion.
    Valida sesión, filtra preguntas, genera embedding, y responde con streaming real.
    Maneja derivación a humano si la confianza es baja.

    :param request: Objeto Request con JSON.
    :return: Response con streaming de texto.
    """
    global agent_instance
    global pdf_text_temp

    if agent_instance is None:
        return Response(text="Servicio no disponible. Intente más tarde.", status=503)

    print("[Chat] Petición recibida")
    try:
        data = await request.json()
    except Exception:
        return Response(text="JSON inválido.", status=400)

    pregunta = data.get("pregunta")
    ciudadano_id = data.get("ciudadano_id")
    token_sesion = data.get("token_sesion")
    print(f"[Chat] Pregunta recibida: {pregunta}")
    if not pregunta or not ciudadano_id or not token_sesion:
        return Response(text="Faltan parámetros obligatorios.", status=400)

    sesion = await obtener_sesion_por_token(token_sesion)
    if not sesion or sesion['ciudadano_id'] != ciudadano_id:
        return Response(text="Sesión inválida o expirada.", status=401)

    pregunta = sanitizar_texto(pregunta)

    key = (ciudadano_id, token_sesion)
    if key in conversaciones_derivadas:
        mensaje = "Uno de nuestros colaboradores se pondrá en contacto en breve, por favor espere."

        async def stream_msg():
            yield mensaje.encode("utf-8")

        return Response(
            200,
            content=StreamedContent(b"text/plain", stream_msg)
        )

    embedding = await generar_embedding(pregunta)

    # Agregar el texto del PDF al contexto
    contexto_adicional = pdf_text_temp
    # Limpiar la variable temporal
    pdf_text_temp = ""

    try:
        async def stream_response():
            async for fragmento in agent_instance.responder_stream(pregunta, embedding, contexto_adicional):
                print(f"[Agente] Respuesta parcial: {fragmento.decode('utf-8')}")
                yield fragmento

        return Response(
            200,
            content=StreamedContent(b"text/plain", stream_response)
        )
    except Exception:
        # Fallback a búsqueda en internet si falla streaming
        resultado = await agent_instance.buscar_en_internet(pregunta)
        confianza = await parse_confianza(resultado)
        if confianza < 0.6:
            conversaciones_derivadas.add(key)
            mensaje = "No estoy seguro de la respuesta. En breve lo atenderá un ser humano."

            async def stream_msg():
                yield mensaje.encode("utf-8")

            return Response(
                200,
                content=StreamedContent(b"text/plain", stream_msg)
            )

        await guardar_consulta_respuesta(sesion['id'], pregunta, resultado, confianza)

        async def stream_response():
            for token in resultado.split():
                yield (token + " ").encode("utf-8")
                await asyncio.sleep(0.05)

        return Response(
            200,
            content=StreamedContent(b"text/plain", stream_response)
        )



async def limpiar_conversacion(request: Request) -> Response:
    """
    Endpoint POST /limpiar para limpiar la conversación y permitir continuar tras derivación a humano.

    :param request: Objeto Request con JSON.
    :return: JSON con mensaje de confirmación.
    """
    try:
        data = await request.json()
    except Exception:
        return Response(400, text="JSON inválido.")

    ciudadano_id = data.get("ciudadano_id")
    token_sesion = data.get("token_sesion")

    if not ciudadano_id or not token_sesion:
        return Response(400, text="Faltan parámetros obligatorios.")

    key = (ciudadano_id, token_sesion)
    conversaciones_derivadas.discard(key)

    return json({"mensaje": "Conversación limpiada, puede continuar."}, status=200)


async def login(request: Request) -> Response:
    """
    Endpoint POST /login para registrar o identificar un ciudadano y crear una sesión nueva.

    JSON esperado:
    {
        "nombre": "Nombre completo",
        "email": "correo@ejemplo.com",
        "telefono": "123456789" (opcional)
    }

    Respuesta JSON:
    {
        "ciudadano_id": int,
        "token_sesion": str
    }

    Si el correo ya existe, se reutiliza el ciudadano y se crea una nueva sesión.
    """
    try:
        data = await request.json()
    except Exception:
        return Response(400, text="JSON inválido.")

    nombre = data.get("nombre")
    email = data.get("email")
    telefono = data.get("telefono", None)

    if not nombre or not email:
        return Response(400, text="Nombre y email son obligatorios.")

    # Sanitizar entradas para evitar inyección y caracteres no deseados
    email = sanitizar_texto(email)
    nombre = sanitizar_texto(nombre)
    if telefono:
        telefono = sanitizar_texto(telefono)

    ciudadano = await obtener_ciudadano_por_email(email)
    if ciudadano:
        ciudadano_id = ciudadano['id']
    else:
        ciudadano_id = await crear_ciudadano(nombre, email, telefono)

    # Crear una nueva sesión con token único
    token_sesion = str(uuid.uuid4())
    await crear_sesion(ciudadano_id, token_sesion)

    return json({"ciudadano_id": ciudadano_id, "token_sesion": token_sesion}, status=200)


async def upload(request: Request):
    """
    Actualmente no funciona
    POST /upload — Subir un único PDF y extraer su texto usando FormPart.content_type y .content.

    1. Comprueba que el servicio está listo.
    2. await request.form(), imprime keys para debug.
    3. Toma form['archivo'] (lista de FormPart) y coge el primero.
    4. Lee content_type desde part.content_type y decodifica si es bytes.
    5. Valida 'application/pdf'; si falla → 400.
    6. Lee contenido_bytes = part.content.
    7. Extrae texto con PyPDF2 y guarda en pdf_text_temp.
    8. Devuelve JSON de éxito.
    """
    global agent_instance, pdf_text_temp

    # 1) Servicio disponible?
    if agent_instance is None:
        return text("Servicio no disponible. Intente más tarde.", status=503)

    # 2) Leer multipart completo
    form = await request.form()
    print("DEBUG: keys en form()", list(form.keys()))

    # 3) Sacar lista de FormPart bajo 'archivo'
    archivos = form.get("archivo")
    if not archivos or not isinstance(archivos, list):
        print("DEBUG: form['archivo'] no es lista o está vacío:", archivos)
        return text("Falta el archivo PDF.", status=400)

    part = archivos[0]
    print("DEBUG: primer elemento de archivos:", type(part), repr(part))

    # 4) Leer y decodificar content_type
    raw_ct = part.content_type
    if isinstance(raw_ct, (bytes, bytearray)):
        content_type = raw_ct.decode("latin1").split(";", 1)[0].strip().lower()
    else:
        content_type = raw_ct.split(";", 1)[0].strip().lower()
    print("DEBUG: content_type detectado:", content_type)

    # 5) Validar PDF
    if content_type != "application/pdf":
        print("DEBUG: MIME no es PDF")
        return text("Tipo de archivo no soportado. Solo PDF.", status=400)

    # 6) Leer bytes desde part.content
    contenido_bytes = part.content
    if not isinstance(contenido_bytes, (bytes, bytearray)):
        print("DEBUG: part.content no es bytes:", type(contenido_bytes))
        return text("Error al leer el contenido del archivo.", status=400)
    print("DEBUG: bytes leídos:", len(contenido_bytes))

    # 7) Extraer texto con PyPDF2
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(contenido_bytes))
    except Exception as e:
        print("DEBUG: fallo PyPDF2.PdfReader:", e)
        return text("Error al leer el PDF.", status=400)

    paginas = [page.extract_text() or "" for page in reader.pages]
    texto_completo = "\n".join(paginas)
    print("DEBUG: caracteres extraídos:", len(texto_completo))

    pdf_text_temp = texto_completo

    # 8) Responder éxito
    return json({"mensaje": "Texto del PDF guardado."}, status=200)