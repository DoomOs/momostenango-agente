"""
Módulo de rutas API para el backend municipal_agent.

Contiene endpoints para:
- Registro e inicio de sesión de ciudadanos (/login).
- Interacción con el agente inteligente (/chat).
- Limpieza de la conversación para continuar tras derivación a humano (/limpiar).

Incluye validación, saneamiento de datos, manejo de sesiones y simulación de derivación a humano.
"""

from blacksheep import Response, Request
from blacksheep.server.responses import json
from app.db.crud import (
    crear_sesion,
    guardar_consulta_respuesta,
    obtener_ciudadano_por_email,
    crear_ciudadano,
    obtener_sesion_por_token,
)
from app.agents.agno_agent import AgnoMunicipalAgent
from app.utils.helpers import generar_embedding, sanitizar_texto
import asyncio
import uuid
import PyPDF2
import io 
agent_instance = AgnoMunicipalAgent()


conversaciones_derivadas = set()


async def generate_token_stream(response_text: str):
    """
    Generador asíncrono que simula el streaming token a token de la respuesta.

    :param response_text: Texto completo de la respuesta.
    :yield: Tokens individuales con un pequeño retardo para simular streaming.
    """
    for token in response_text.split():
        yield token + " "
        await asyncio.sleep(0.05)


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


async def chat(request: Request) -> Response:
    """
    Endpoint POST /chat para interactuar con el agente inteligente municipal.

    JSON esperado:
    {
        "pregunta": "Texto de la pregunta",
        "ciudadano_id": 123,
        "token_sesion": "token-uuid"
    }

    Respuesta:
    Streaming token a token con la respuesta generada por el agente.

    Si la conversación está derivada a humano, se envía un mensaje especial y el agente no responde.
    Se valida que la sesión exista y pertenezca al ciudadano para mayor seguridad.
    """
    try:
        data = await request.json()
    except Exception:
        return Response(400, text="JSON inválido.")

    pregunta = data.get("pregunta")
    ciudadano_id = data.get("ciudadano_id")
    token_sesion = data.get("token_sesion")

    if not pregunta or not ciudadano_id or not token_sesion:
        return Response(400, text="Faltan parámetros obligatorios.")

    # Validar que la sesión existe y pertenece al ciudadano
    sesion = await obtener_sesion_por_token(token_sesion)
    if not sesion or sesion['ciudadano_id'] != ciudadano_id:
        return Response(401, text="Sesión inválida o expirada.")

    # Sanitizar la pregunta para evitar inyección
    pregunta = sanitizar_texto(pregunta)

    key = (ciudadano_id, token_sesion)
    if key in conversaciones_derivadas:
        mensaje = "Uno de nuestros colaboradores se pondrá en contacto en breve, por favor espere."
        async def stream_msg():
            yield mensaje
        return Response(text_stream(stream_msg()), content_type="text/plain")

    # Generar embedding de la pregunta
    embedding = await generar_embedding(pregunta)

    # Obtener respuesta del agente
    resultado = await agent_instance.responder(pregunta, embedding)

    # Si la confianza es baja, marcar la conversación como derivada a humano
    if resultado["derivar_humano"]:
        conversaciones_derivadas.add(key)

    # Guardar consulta y respuesta en la base de datos
    await guardar_consulta_respuesta(sesion['id'], pregunta, resultado["respuesta"], resultado["confianza"])

    # Stream de tokens para la respuesta
    
    async def stream_response():
        async for token in generate_token_stream(resultado["respuesta"]):
            yield token

    return Response(stream_response(), content_type="text/plain")


async def limpiar_conversacion(request: Request) -> Response:
    """
    Endpoint POST /limpiar para limpiar la conversación y permitir continuar tras derivación a humano.

    JSON esperado:
    {
        "ciudadano_id": 123,
        "token_sesion": "token-uuid"
    }

    Respuesta JSON:
    {
        "mensaje": "Conversación limpiada, puede continuar."
    }
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

    return Response(200, json={"mensaje": "Conversación limpiada, puede continuar."})



async def upload(request: Request) -> Response:
    """
    Endpoint POST /upload para recibir un archivo y una pregunta,
    extraer texto del archivo y responder usando el agente con contexto adicional.

    Recibe multipart/form-data con:
    - archivo: archivo a procesar (PDF soportado)
    - pregunta: texto de la pregunta
    - ciudadano_id: id del ciudadano (para validación si se desea)
    - token_sesion: token de sesión (para validación si se desea)

    No guarda el archivo, solo lo procesa en memoria.
    """
    form = await request.form()
    archivo = form.get("archivo")
    pregunta = form.get("pregunta")
    ciudadano_id = form.get("ciudadano_id")
    token_sesion = form.get("token_sesion")

    if not archivo or not pregunta or not ciudadano_id or not token_sesion:
        return Response(400, text="Faltan parámetros obligatorios.")

    pregunta = sanitizar_texto(pregunta)

    contenido_texto = ""

    if archivo.content_type == "application/pdf":
        contenido_bytes = await archivo.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contenido_bytes))
        textos = [page.extract_text() or "" for page in pdf_reader.pages]
        contenido_texto = "\n".join(textos)
    else:
        return Response(400, text="Tipo de archivo no soportado. Solo PDF.")

    # Llamar al agente con contexto adicional
    resultado = await agent_instance.responder(pregunta, contexto_adicional=contenido_texto)

    return Response(200, json={"respuesta": resultado["respuesta"], "confianza": resultado["confianza"]})