"""
Funciones CRUD para las tablas principales:
- ciudadanos
- sesiones
- consultas_respuestas
- documentos
- faqs

Incluye saneamiento básico y validación de datos.
"""

from typing import List, Optional
from app.db.connection import db
from datetime import datetime


async def obtener_sesion_por_token(token_sesion: str) -> Optional[dict]:
    """
    Obtiene la sesión por token.

    :param token_sesion: Token de sesión.
    :return: Diccionario con datos de la sesión o None si no existe.
    """
    query = "SELECT * FROM sesiones WHERE token_sesion = $1;"
    row = await db.fetchrow(query, token_sesion)
    return dict(row) if row else None

async def obtener_ciudadano_por_email(email: str) -> Optional[dict]:
    """
    Busca un ciudadano por su correo electrónico.

    :param email: Correo electrónico.
    :return: Diccionario con datos del ciudadano o None si no existe.
    """
    query = "SELECT * FROM ciudadanos WHERE email = $1;"
    row = await db.fetchrow(query, email)
    return dict(row) if row else None

async def crear_ciudadano(nombre: str, email: str, telefono: Optional[str] = None) -> int:
    """
    Crea un nuevo ciudadano.

    :param nombre: Nombre completo.
    :param email: Correo electrónico único.
    :param telefono: Teléfono opcional.
    :return: ID del ciudadano creado.
    """
    query = """
    INSERT INTO ciudadanos (nombre, email, telefono)
    VALUES ($1, $2, $3)
    RETURNING id;
    """
    row = await db.fetchrow(query, nombre, email, telefono)
    return row['id']


async def crear_sesion(ciudadano_id: int, token_sesion: str) -> int:
    """
    Crea una nueva sesión para un ciudadano.

    :param ciudadano_id: ID del ciudadano.
    :param token_sesion: Token único de sesión.
    :return: ID de la sesión creada.
    """
    query = """
    INSERT INTO sesiones (ciudadano_id, token_sesion)
    VALUES ($1, $2)
    RETURNING id;
    """
    row = await db.fetchrow(query, ciudadano_id, token_sesion)
    return row['id']

async def obtener_faqs(limit: int = 10) -> List[dict]:
    """
    Obtiene una lista de preguntas frecuentes.

    :param limit: Número máximo de FAQs a obtener.
    :return: Lista de diccionarios con preguntas y respuestas.
    """
    query = "SELECT id, pregunta, respuesta FROM faqs ORDER BY fecha_creacion DESC LIMIT $1;"
    rows = await db.fetch(query, limit)
    return [dict(row) for row in rows]

async def guardar_consulta_respuesta(sesion_id: int, pregunta: str, respuesta: str, confianza: float):
    """
    Guarda una consulta y su respuesta en la base de datos.

    :param sesion_id: ID de la sesión.
    :param pregunta: Texto de la pregunta.
    :param respuesta: Texto de la respuesta.
    :param confianza: Nivel de confianza del agente (0 a 1).
    """
    query = """
    INSERT INTO consultas_respuestas (sesion_id, pregunta, respuesta, confianza)
    VALUES ($1, $2, $3, $4);
    """
    await db.execute(query, sesion_id, pregunta, respuesta, confianza)