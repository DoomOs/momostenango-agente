"""
Módulo de conexión a la base de datos PostgreSQL usando asyncpg y pgvector.

Establece un pool de conexiones para uso eficiente y registra la extensión pgvector
para manejar tipos vectoriales en consultas.
"""

import asyncpg
from pgvector.asyncpg import register_vector
from app.config import DATABASE_URL

class Database:
    """
    Clase para manejar el pool de conexiones a PostgreSQL.
    """

    def __init__(self):
        self.pool = None

    async def connect(self):
        """
        Inicializa el pool de conexiones y registra la extensión vector.
        """
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        async with self.pool.acquire() as conn:
            await register_vector(conn)

    async def close(self):
        """
        Cierra el pool de conexiones.
        """
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, *args):
        """
        Ejecuta una consulta SELECT y devuelve resultados.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """
        Ejecuta una consulta SELECT y devuelve una fila.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        """
        Ejecuta una consulta que no devuelve resultados (INSERT, UPDATE, DELETE).
        """
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

# Instancia global para usar en la app
db = Database()