# J5DOCK 🐳

Una herramienta moderna y elegante para gestionar contenedores Docker con una interfaz web intuitiva y alias de shell automatizados.

## 📋 Características

✨ **Interfaz Web SPA** - Dashboard intuitivo con diseño moderno (Tailwind CSS + Vue.js)  
🚀 **Gestión de Contenedores** - Inicia, detiene y visualiza todos tus contenedores Docker  
📂 **Proyectos/Agrupaciones** - Agrupa contenedores en proyectos para gestionar múltiples contenedores simultáneamente  
🏷️ **Aliases Personalizados** - Crea alias de shell para control rápido desde la terminal  
⚙️ **Auto-configuración de Shell** - Instalación automática de alias en `.bashrc`, `.zshrc` y `.bash_profile`  
📡 **API REST** - Endpoints completos para todas las operaciones  
🔄 **Sincronización en Tiempo Real** - Datos de contenedores actualizados automáticamente  

## 📦 Requisitos Previos

- **Python 3.7+**
- **Docker** instalado y funcionando
- **Acceso al socket de Docker** (generalmente `/var/run/docker.sock`)

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <tu-repo>
cd PythonLocalScripts
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

Las dependencias principales son:
- `Flask` - Framework web
- `docker` - Cliente Python para Docker

### 3. Dar permisos de ejecución (opcional en Windows)

```bash
chmod +x main.py
```

## 📖 Uso

### 🌐 Interfaz Web

Inicia el servidor web:

```bash
python3 main.py
```

Accede a la interfaz en:
```
http://localhost:5555
```

**Características disponibles en la web:**
- 📦 Lista completa de contenedores (activos e inactivos)
- ▶️ Botones para iniciar/detener contenedores
- 📂 Crear y gestionar proyectos
- 🏷️ Crear alias individuales para contenedores
- 🔄 Actualizar datos en tiempo real

### 💻 Interfaz CLI (Línea de Comandos)

Al ejecutar `python3 main.py` por primera vez, se configuran automáticamente dos alias en tu shell:

**Iniciar un proyecto:**
```bash
j5d <nombre_proyecto>
```

**Detener un proyecto:**
```bash
j5d-stop <nombre_proyecto>
```

Ejemplo:
```bash
j5d miproyecto    # Inicia todos los contenedores del proyecto
j5d-stop miproyecto  # Detiene todos los contenedores del proyecto
```

## 📁 Estructura del Proyecto

```
.
├── main.py              # Aplicación principal (Flask + Vue.js)
├── docker_data.json     # Base de datos local (proyectos, aliases)
├── aliases.json         # Configuración de aliases (legacy)
├── requirements.txt     # Dependencias Python
└── README.MD           # Este archivo
```

### docker_data.json

Estructura de la base de datos:

```json
{
  "aliases": {
    "mi_alias": "nombre_contenedor"
  },
  "projects": {
    "mi_proyecto": ["contenedor1", "contenedor2"]
  }
}
```

## 🔌 API REST Endpoints

### Datos Generales

```
GET /api/data
```
Retorna lista de contenedores y datos (proyectos, aliases)

### Contenedores

```
POST /api/container/start/<nombre>
POST /api/container/stop/<nombre>
```

### Alias

```
POST /api/alias/add
Body: { "alias": "nombre_alias", "container": "nombre_contenedor" }

POST /api/alias/start/<alias>
POST /api/alias/stop/<alias>
POST /api/alias/delete/<alias>
```

### Proyectos

```
POST /api/project/add
Body: { "project": "nombre_proyecto", "container": "nombre_contenedor" }

POST /api/project/start/<proyecto>
POST /api/project/stop/<proyecto>
POST /api/project/delete/<proyecto>
```

## ⚙️ Configuración

### Puerto del servidor

Por defecto, J5DOCK corre en `http://0.0.0.0:5555`. 

Para cambiar el puerto, edita la última línea de `main.py`:

```python
app.run(host="0.0.0.0", port=5555)  # Cambiar 5555 por tu puerto
```

### Auto-refresh de datos

En la interfaz web, los datos se actualizan automáticamente cada 10 segundos. Para modificar este intervalo, busca esta línea en el código Vue:

```javascript
setInterval(fetchData, 10000);  // 10000ms = 10 segundos
```

## 🛠️ Troubleshooting

### Error: "Permission denied" con Docker

Asegúrate de que tu usuario tiene permisos para acceder a Docker:

```bash
sudo usermod -aG docker $USER
# Luego reinicia tu sesión o ejecuta:
newgrp docker
```

### Los alias no funcionan

Después de ejecutar `python3 main.py`, recarga tu shell:

```bash
# Para bash:
source ~/.bashrc

# Para zsh:
source ~/.zshrc
```

### El servidor no inicia

Verifica que el puerto 5555 esté disponible:

```bash
lsof -i :5555
```

Si está ocupado, cambia el puerto en `main.py`.

## 📝 Ejemplo de Uso Completo

1. **Inicia el servidor:**
   ```bash
   python3 main.py
   ```

2. **Abre en tu navegador:**
   ```
   http://localhost:5555
   ```

3. **Crea un proyecto "dev":**
   - Selecciona un contenedor en la tabla
   - Escribe "dev" en el campo "Añadir a Proyecto"
   - Haz clic en "Añadir"

4. **Inicia todos los contenedores del proyecto desde el CLI:**
   ```bash
   j5d dev
   ```

5. **Detén el proyecto:**
   ```bash
   j5d-stop dev
   ```

## 📄 Licencia

Este proyecto es de código abierto. Úsalo libremente.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Siéntete libre de abrir issues o pull requests.

---

**Creado con ❤️ para facilitar la gestión de Docker**
