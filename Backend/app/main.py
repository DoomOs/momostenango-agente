from blacksheep import Application
from blacksheep.server.responses import text, Response
from app.db.connection import db
from app.api.routes import chat, login, limpiar_conversacion, upload
import uvicorn

app = Application()

async def cors_middleware(request, handler):
    """
    Middleware para manejar CORS (Cross-Origin Resource Sharing).

    Intercepta todas las solicitudes y añade cabeceras CORS necesarias para permitir
    solicitudes desde el origen http://localhost:3000. Responde directamente a solicitudes OPTIONS
    con los headers adecuados para evitar bloqueos en navegadores.

    Args:
        request (Request): Objeto de la solicitud entrante.
        handler (Callable): Siguiente manejador en la cadena de middlewares.

    Returns:
        Response: Respuesta HTTP con cabeceras CORS apropiadas.
    """
    if request.method == "OPTIONS":
        response = text("")
        response.add_header(b"Access-Control-Allow-Origin", b"http://localhost:3000")
        response.add_header(b"Access-Control-Allow-Methods", b"POST, GET, OPTIONS")
        response.add_header(b"Access-Control-Allow-Headers", b"Content-Type, Authorization")
        return response

    response = await handler(request)
    if response is None:
        response = text("Not Found")
        response.status_code = 404

    response.add_header(b"Access-Control-Allow-Origin", b"http://localhost:3000")
    response.add_header(b"Access-Control-Allow-Methods", b"POST, GET, OPTIONS")
    response.add_header(b"Access-Control-Allow-Headers", b"Content-Type, Authorization")
    return response

# Registrar el middleware CORS para que se ejecute en todas las solicitudes
app.middlewares.append(cors_middleware)

async def options_handler(request):
    """
    Manejador global para solicitudes HTTP OPTIONS.

    Esta función responde a cualquier solicitud OPTIONS con las cabeceras CORS necesarias,
    permitiendo que los navegadores realicen correctamente las peticiones preflight.

    Args:
        request (Request): Objeto de la solicitud OPTIONS.

    Returns:
        Response: Respuesta HTTP vacía con cabeceras CORS.
    """
    response = text("")
    response.headers[b"Access-Control-Allow-Origin"] = b"http://localhost:3000"
    response.headers[b"Access-Control-Allow-Methods"] = b"POST, GET, OPTIONS"
    response.headers[b"Access-Control-Allow-Headers"] = b"Content-Type, Authorization"
    return response

# Registrar la ruta global para manejar todas las solicitudes OPTIONS
app.router.add_options("/{path:path}", options_handler)

# Registrar rutas POST para la API
app.router.add_post("/chat", chat)
app.router.add_post("/login", login)
app.router.add_post("/limpiar", limpiar_conversacion)
app.router.add_post("/upload", upload)

@app.on_start
async def startup(application: Application):
    """
    Evento que se ejecuta al iniciar la aplicación.

    Se encarga de establecer la conexión con la base de datos para que la aplicación
    pueda operar correctamente.

    Args:
        application (Application): Instancia de la aplicación BlackSheep.
    """
    await db.connect()

@app.on_stop
async def shutdown(application: Application):
    """
    Evento que se ejecuta al detener la aplicación.

    Se encarga de cerrar la conexión con la base de datos para liberar recursos
    y evitar posibles fugas de conexión.

    Args:
        application (Application): Instancia de la aplicación BlackSheep.
    """
    await db.close()

if __name__ == "__main__":
    """
    Punto de entrada principal para ejecutar la aplicación.

    Ejecuta el servidor Uvicorn con recarga automática habilitada para desarrollo,
    escuchando en todas las interfaces de red en el puerto 8000.
    """
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)