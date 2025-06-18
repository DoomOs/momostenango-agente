## Instalacion:

Para instalar este software se debe de tener python 3.x instalado ademas de ello debemos de instalar y activar un entorno virtual (venv) en Python, siguiendo estos pasos:

### Backend con blacksheep
- **1. Instalar**  `venv`
Si estás utilizando Python 3.3 o superior, `venv` ya está incluido, pero si hay problemas, puedes instalarlo con:


```{code-block}
:class: copybutton
pip install virtualenv
```

- **2. Crear un entorno virtual**
Navega a la carpeta donde deseas crear el entorno y ejecuta:

```{code-block}
:class: copybutton
python -m venv nombre_del_entorno
```
Por ejemplo, para un entorno llamado venv:
```{code-block}
:class: copybutton
python -m venv venv
```

- **3. Activar el entorno virtual**
La activación depende de tu sistema operativo:
Windows (cmd o PowerShell):
```{code-block}
:class: copybutton
venv\Scripts\activate
```

- **4. Verificar activación**
Si el entorno se activó correctamente, verás el nombre del entorno entre paréntesis en la terminal, por ejemplo: `(venv)` 

- **5. Desactivar el entorno virtual**
Cuando termines, puedes salir del entorno con:

```{code-block}
:class: copybutton
deactivate
```

Con el entorno virtual activo, debemos de ejecutar la sigueinte intalacion de requerimientos:

```{code-block}
:class: copybutton
pip install numpy==2.3.0
pip install httpx==0.28.1
pip install openai==1.86.0
pip install PyPDF2==3.0.1
pip install blacksheep==2.3.1
pip install asyncpg==0.30.0
pip install pgvector==0.4.1
pip install python-dotenv==1.1.0
pip install uvicorn==0.34.3
pip install requests==2.32.4
pip install Sphinx==8.2.3
pip install sphinx-rtd-theme==3.0.2
pip install sphinxcontrib-applehelp==2.0.0
pip install sphinxcontrib-devhelp==2.0.0
pip install sphinxcontrib-htmlhelp==2.1.0
pip install sphinxcontrib-jquery==4.1
pip install sphinxcontrib-jsmath==1.0.1
pip install sphinxcontrib-qthelp==2.0.0
pip install sphinxcontrib-serializinghtml==2.0.0
pip install beautifulsoup4==4.12.2

```

Dentro de la carpeta de Backend, deberemos de crear un archivo `.env`, y en el debemos de crear las sigueintes variables de entorno

```{code-block}
:class: copybutton

OPENROUTER_API_KEY=tu-api-key


POSTGRES_HOST=localhost
POSTGRES_DB=municipal_agent
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_PORT=5432


```

Con las dependencias instaladas, con el entorno virtual activo y el archivo .env creado, debes de inciar el el backend, te diriges a la carpeta backend y ejecutas el sigueinte comando: 

```{code-block}
:class: copybutton
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Dentro de la carpeta de Backend, deberemos de crear un archivo .env, y en el debemos de crear las sigueintes variables de entorno

```{code-block}
:class: copybutton

OPENROUTER_API_KEY=tu-api-key


POSTGRES_HOST=localhost
POSTGRES_DB=municipal_agent
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_PORT=5432


```

### Docker
Asi mismo, debemos de tener instalado Docker, si tenemos visual Studio Code, es recomendable que instales la extension de Docker para facilitar su uso, ya que este permite ejecutar directamente el contenedor de docker, si no puedes usar este comando en una terminal donde este ubicado tu archivo `docker-compose.yml`: 



```{code-block}
:class: copybutton
docker compose -f 'docker-compose.yml' up -d --build 

```

### Reac

Debemos de dirigirnos a las carpeta de frontend (desde la temrinal),Una vez dentro de la carpeta del proyecto, ejecuta el siguiente comando:

```{code-block}
:class: copybutton
npm install
```

`npm` leerá automáticamente el archivo package.json y descargará todas las dependencias listadas (tanto las de producción como las de desarrollo) en una carpeta llamada node_modules. También creará o actualizará el archivo package-lock.json, que asegura que las versiones de las librerías sean consistentes para todos los desarrolladores.

Al tener instaladas todas las dependencias, debemos de ejecutar el front, esto se hace con el comando:
```{code-block}
:class: copybutton
npm start
```