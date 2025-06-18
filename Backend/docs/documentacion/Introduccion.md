## Descripción General del Proyecto

**Agno Municipal Agent** es una aplicación backend desarrollada para mejorar la interacción entre los ciudadanos y el gobierno local de Momostenango, Guatemala. Implementada con el framework asincrónico BlackSheep (Python), esta solución ofrece una interfaz conversacional capaz de proporcionar información municipal sobre trámites, servicios y normativas de forma eficiente.

---

## Arquitectura del Sistema

### 1. API Backend (BlackSheep)
El núcleo del sistema es una API desarrollada con BlackSheep. Esta API gestiona las solicitudes entrantes, conecta con el modelo de lenguaje y la base de datos, y entrega respuestas en tiempo real.

### 2. Modelo de Lenguaje (LLM) - OpenRouter
El sistema utiliza un modelo de lenguaje a través de la plataforma OpenRouter. Este modelo responde a las consultas de los usuarios bajo un prompt inicial que lo define como asistente municipal especializado en temas de Momostenango.

### 3. Base de Datos - PostgreSQL + pgvector (Docker)
Toda la información relevante (documentos, preguntas frecuentes, etc.) se almacena en una base de datos PostgreSQL. Se emplea la extensión `pgvector` para realizar búsquedas semánticas eficientes basadas en embeddings.

### 4. Búsqueda en Internet (No funcional)
El agente puede complementar sus respuestas mediante búsquedas web restringidas geográficamente a Guatemala, en caso de que la base de datos no contenga la información requerida.

### 5. Gestión de Sesiones
Cada conversación se gestiona mediante sesiones lo que tener una trazabilidad de que ciudadanos dan mas uso al agente.


---

## Funcionalidades Principales

- **Autenticación de Usuarios:** Registro e inicio de sesión para acceso personalizado.
- **Interfaz Conversacional:** Chat con el agente municipal.
- **Búsqueda Vectorial:** Recuperación de documentos relevantes mediante `pgvector`.
- **Conversacion con el Agente:** Este agente estará disponible para responder preguntas sobre temas exclusivamente del ámbito municipal.

---

## Tecnologías Utilizadas

- **Lenguaje:** Python
- **Framework:** BlackSheep (ASGI)
- **Modelo de Lenguaje:** OpenRouter (con acceso a modelos como OpenAI o similares)
- **Base de Datos:** PostgreSQL
- **Extensión Vectorial:** pgvector
- **Cliente HTTP:** httpx
- **Servidor:** uvicorn
- **Procesamiento de PDF:** pdfjs-dist
- **Scraping:** Beutifulsoap
- **Documentacion:** Sphinx

---

## El MCP 

El **MCP** representa la fuente centralizada de información oficial de la municipalidad, proporcionando el contexto necesario para que el agente responda de forma precisa, (si la pregunta realizada no esta en el contexto, puede errar en su respuesta)

### Componentes del MCP

- **Documentos oficiales:** Reglamentos, normativas, procedimientos y servicios almacenados en la base de datos.
- **FAQs:** Preguntas frecuentes para resolver inquietudes comunes de forma inmediata.

### Rol del MCP en el Agente

1. **Recuperación de Información Precisa:** Mediante búsqueda vectorial semántica.
2. **Limitación del Alcance del Modelo:** El agente responde exclusivamente a temas municipales.
3. **Mejora de Respuestas:** Combinación de documentos, FAQs y contexto adicional.

### Implementación Técnica

- **Búsqueda Semántica:** Uso de embeddings sobre documentos municipales almacenados en PostgreSQL.
- **Integración con el Prompt:** La información extraída se incorpora al prompt del modelo para mejorar la precisión de las respuestas.

---

## Script para Descarga de PDFs desde Página Web

### Propósito

Este script automatiza la descarga de todos los archivos PDF enlazados en una página web específica. Se ha diseñado para obtener los documentos públicos disponibles en:

[https://municipalidaddemomostenango.com/mayo-2025/](https://municipalidaddemomostenango.com/mayo-2025/)

### Funcionamiento

1. **Obtención del HTML:** Se realiza una solicitud `GET` simulando un navegador mediante headers personalizados.
2. **Análisis del HTML:** Se utiliza BeautifulSoup para buscar enlaces a archivos PDF.
3. **Construcción de URLs:** Se genera la URL completa usando `urljoin` para cada archivo.
4. **Descarga:** Cada PDF se descarga mediante una nueva solicitud HTTP.
5. **Almacenamiento:** Los archivos se guardan localmente en una carpeta llamada `pdfs_mayo_2025`.

### Estructura del Script

- **Librerías utilizadas:**
  - `os`: Manejo de carpetas y archivos
  - `requests`: Solicitudes HTTP
  - `BeautifulSoup`: Análisis del contenido HTML
  - `urljoin`: Construcción de URLs absolutas

- **Variables principales:**
  - `url`: URL de la página a scrapear
  - `output_folder`: Carpeta donde se guardarán los PDFs

- **Proceso general:**
  - Solicitud de la página web
  - Análisis y extracción de enlaces `.pdf`
  - Descarga y almacenamiento en la carpeta definida

---

## Objetivo General del Proyecto

El principal objetivo de Agno Municipal Agent es facilitar el acceso a la información y servicios municipales a través de una interfaz conversacional intuitiva. Este sistema busca reducir la carga operativa del personal municipal y mejorar significativamente la experiencia del ciudadano al interactuar con la administración pública.
