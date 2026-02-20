import os
import sys
import json
import docker
from flask import Flask, jsonify, request

app = Flask(__name__)
client = docker.from_env()

DATA_FILE = "docker_data.json"

# Inicializar archivo de datos si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"aliases": {}, "projects": {}}, f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_container_path(container):
    mounts = container.attrs.get("Mounts", [])
    for m in mounts:
        if m.get("Type") == "bind":
            return m.get("Source")
    return "No bind mount"


def setup_shell_aliases():
    """Autoconfigura los alias j5d y j5d-stop en .bashrc y .zshrc"""
    script_path = os.path.abspath(__file__)
    alias_start = f'alias j5d="python3 {script_path} start"\n'
    alias_stop = f'alias j5d-stop="python3 {script_path} stop"\n'
    marker = "# --- Docker Manager Aliases ---"
    
    configs_to_check = [".bashrc", ".zshrc", ".bash_profile"]
    home_dir = os.path.expanduser("~")
    installed_in = []
    
    for conf in configs_to_check:
        conf_path = os.path.join(home_dir, conf)
        if os.path.exists(conf_path):
            with open(conf_path, "r") as f:
                content = f.read()
            
            if marker not in content:
                with open(conf_path, "a") as f:
                    f.write(f"\n{marker}\n")
                    f.write(alias_start)
                    f.write(alias_stop)
                    f.write("# ------------------------------\n")
                installed_in.append(conf_path)
                
    return installed_in


# Funciones para la Terminal (CLI)
def cli_start_project(project_name):
    data = load_data()
    projects = data.get("projects", {})
    if project_name not in projects:
        print(f"❌ Error: El proyecto '{project_name}' no existe.")
        return
    print(f"🚀 Iniciando proyecto: {project_name}")
    for container_name in projects[project_name]:
        try:
            container = client.containers.get(container_name)
            container.start()
            print(f"  ✅ Contenedor {container_name} iniciado.")
        except Exception as e:
            print(f"  ❌ Error al iniciar {container_name}: {e}")

def cli_stop_project(project_name):
    data = load_data()
    projects = data.get("projects", {})
    if project_name not in projects:
        print(f"❌ Error: El proyecto '{project_name}' no existe.")
        return
    print(f"🛑 Deteniendo proyecto: {project_name}")
    for container_name in projects[project_name]:
        try:
            container = client.containers.get(container_name)
            container.stop()
            print(f"  ✅ Contenedor {container_name} detenido.")
        except Exception as e:
            print(f"  ❌ Error al detener {container_name}: {e}")


# ==========================================
# INTERFAZ WEB (Tailwind CSS + Vue.js)
# ==========================================
# Al usar Vue, la lógica {{ }} es manejada por el cliente, no por Flask.
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker Manager Pro</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Vue 3 -->
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .custom-scroll::-webkit-scrollbar { height: 8px; width: 8px; }
        .custom-scroll::-webkit-scrollbar-track { background: #1e293b; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

<div id="app" class="flex-grow flex flex-col" v-cloak>
    <!-- Navbar -->
    <nav class="bg-slate-900 border-b border-slate-800 shadow-lg px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center gap-3">
            <span class="text-3xl">🐳</span>
            <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                Docker Manager Pro
            </h1>
        </div>
        <button @click="fetchData" class="flex items-center gap-2 text-sm bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg border border-slate-700 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            Refrescar
        </button>
    </nav>

    <div class="container mx-auto px-4 py-8 flex-grow flex flex-col gap-8">
        
        <!-- Notificaciones Toast -->
        <div v-if="notification" class="fixed bottom-4 right-4 bg-emerald-600 text-white px-6 py-3 rounded-lg shadow-xl flex items-center gap-3 z-50 transition-all">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            {{ notification }}
        </div>

        <!-- Sección de Contenedores -->
        <div class="glass-panel rounded-2xl overflow-hidden shadow-2xl flex flex-col">
            <div class="bg-slate-800/50 px-6 py-4 border-b border-slate-700/50">
                <h2 class="text-lg font-semibold flex items-center gap-2">
                    <span class="text-blue-400">📦</span> Contenedores Activos / Disponibles
                </h2>
            </div>
            
            <div class="overflow-x-auto custom-scroll">
                <table class="w-full text-left text-sm whitespace-nowrap">
                    <thead class="bg-slate-900/50 text-slate-400">
                        <tr>
                            <th class="px-6 py-4 font-medium">Nombre</th>
                            <th class="px-6 py-4 font-medium">Estado</th>
                            <th class="px-6 py-4 font-medium">Ruta (Bind)</th>
                            <th class="px-6 py-4 font-medium">Acción</th>
                            <th class="px-6 py-4 font-medium">Añadir a Proyecto</th>
                            <th class="px-6 py-4 font-medium">Crear Alias</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800">
                        <tr v-for="c in containers" :key="c.name" class="hover:bg-slate-800/30 transition-colors">
                            <td class="px-6 py-4 font-mono text-slate-200 font-bold">{{ c.name }}</td>
                            <td class="px-6 py-4">
                                <span v-if="c.status === 'running'" class="inline-flex items-center gap-1.5 py-1 px-3 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Running
                                </span>
                                <span v-else class="inline-flex items-center gap-1.5 py-1 px-3 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
                                    {{ c.status }}
                                </span>
                            </td>
                            <td class="px-6 py-4 font-mono text-xs text-slate-500 truncate max-w-[200px]" :title="c.path">{{ c.path }}</td>
                            <td class="px-6 py-4">
                                <button v-if="c.status === 'running'" @click="apiCall(`/api/container/stop/${c.name}`)" class="bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 px-3 py-1 rounded transition-colors w-20">Stop</button>
                                <button v-else @click="apiCall(`/api/container/start/${c.name}`)" class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 px-3 py-1 rounded transition-colors w-20">Start</button>
                            </td>
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-2">
                                    <input v-model="inputs[c.name + '_project']" type="text" list="projects_list" placeholder="Ej. proyecto2" class="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded focus:ring-blue-500 focus:border-blue-500 block px-2.5 py-1 w-32 placeholder-slate-600 outline-none">
                                    <button @click="addToProject(c.name)" class="bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 px-3 py-1 rounded transition-colors">Añadir</button>
                                </div>
                            </td>
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-2">
                                    <input v-model="inputs[c.name + '_alias']" type="text" placeholder="Nuevo alias" class="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded focus:ring-blue-500 focus:border-blue-500 block px-2.5 py-1 w-32 placeholder-slate-600 outline-none">
                                    <button @click="addAlias(c.name)" class="bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 px-3 py-1 rounded transition-colors">Crear</button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="containers.length === 0">
                            <td colspan="6" class="text-center py-8 text-slate-500">Cargando contenedores...</td>
                        </tr>
                    </tbody>
                </table>
                <datalist id="projects_list">
                    <option v-for="(_, pName) in projects" :value="pName"></option>
                </datalist>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Proyectos -->
            <div class="glass-panel rounded-2xl shadow-xl flex flex-col">
                <div class="bg-amber-500/10 px-6 py-4 border-b border-amber-500/20 rounded-t-2xl">
                    <h2 class="text-lg font-semibold flex items-center gap-2 text-amber-400">
                        📂 Proyectos (Agrupaciones)
                    </h2>
                </div>
                <div class="p-6">
                    <div v-for="(conts, pName) in projects" :key="pName" class="mb-4 bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex flex-col gap-3">
                        <div class="flex justify-between items-center border-b border-slate-700 pb-2">
                            <span class="text-lg font-bold text-slate-200">{{ pName }}</span>
                            <div class="flex gap-2">
                                <button @click="apiCall(`/api/project/start/${pName}`)" class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 px-3 py-1 rounded text-sm transition-colors flex items-center gap-1">
                                    ▶ Start All
                                </button>
                                <button @click="apiCall(`/api/project/stop/${pName}`)" class="bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 px-3 py-1 rounded text-sm transition-colors flex items-center gap-1">
                                    ⏹ Stop All
                                </button>
                                <button @click="apiCall(`/api/project/delete/${pName}`)" class="bg-slate-700 text-slate-300 hover:bg-rose-500 hover:text-white px-3 py-1 rounded text-sm transition-colors">
                                    🗑️
                                </button>
                            </div>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            <span v-for="c in conts" :key="c" class="bg-slate-900 border border-slate-700 px-2 py-1 rounded text-xs font-mono text-slate-400">
                                {{ c }}
                            </span>
                        </div>
                    </div>
                    <div v-if="Object.keys(projects).length === 0" class="text-center py-6 text-slate-500">
                        No hay proyectos configurados.
                    </div>
                </div>
            </div>

            <!-- Alias -->
            <div class="glass-panel rounded-2xl shadow-xl flex flex-col">
                <div class="bg-blue-500/10 px-6 py-4 border-b border-blue-500/20 rounded-t-2xl">
                    <h2 class="text-lg font-semibold flex items-center gap-2 text-blue-400">
                        🏷️ Alias Individuales
                    </h2>
                </div>
                <div class="p-0 overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-900/30 text-slate-400">
                            <tr>
                                <th class="px-6 py-3 font-medium">Alias</th>
                                <th class="px-6 py-3 font-medium">Contenedor</th>
                                <th class="px-6 py-3 font-medium text-right">Acción</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800">
                            <tr v-for="(cName, alias) in aliases" :key="alias" class="hover:bg-slate-800/30 transition-colors">
                                <td class="px-6 py-3 font-bold text-blue-300">{{ alias }}</td>
                                <td class="px-6 py-3 font-mono text-slate-400">{{ cName }}</td>
                                <td class="px-6 py-3 flex justify-end gap-2">
                                    <button @click="apiCall(`/api/alias/start/${alias}`)" class="text-emerald-400 hover:text-emerald-300 px-2 py-1 rounded border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/10 transition-colors">Start</button>
                                    <button @click="apiCall(`/api/alias/stop/${alias}`)" class="text-rose-400 hover:text-rose-300 px-2 py-1 rounded border border-rose-500/20 bg-rose-500/5 hover:bg-rose-500/10 transition-colors">Stop</button>
                                    <button @click="apiCall(`/api/alias/delete/${alias}`)" class="text-slate-400 hover:text-rose-400 px-2 py-1 transition-colors">🗑️</button>
                                </td>
                            </tr>
                            <tr v-if="Object.keys(aliases).length === 0">
                                <td colspan="3" class="text-center py-8 text-slate-500">No hay alias configurados.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>
</div>

<script>
    const { createApp, ref, onMounted } = Vue;

    createApp({
        setup() {
            const containers = ref([]);
            const projects = ref({});
            const aliases = ref({});
            const inputs = ref({});
            const notification = ref(null);

            const showNotification = (msg) => {
                notification.value = msg;
                setTimeout(() => { notification.value = null; }, 3000);
            };

            const fetchData = async () => {
                try {
                    const res = await fetch('/api/data');
                    const json = await res.json();
                    containers.value = json.containers;
                    projects.value = json.data.projects;
                    aliases.value = json.data.aliases;
                } catch (e) {
                    console.error("Error cargando datos", e);
                }
            };

            const apiCall = async (endpoint, method='POST', body=null) => {
                const options = { method };
                if (body) {
                    options.headers = { 'Content-Type': 'application/json' };
                    options.body = JSON.stringify(body);
                }
                
                try {
                    await fetch(endpoint, options);
                    showNotification("✅ Acción ejecutada con éxito");
                    fetchData(); // Refrescar UI sin recargar la página
                } catch (e) {
                    alert("Error en la solicitud.");
                }
            };

            const addToProject = (containerName) => {
                const pName = inputs.value[containerName + '_project'];
                if (!pName) return;
                apiCall('/api/project/add', 'POST', { project: pName.trim(), container: containerName });
                inputs.value[containerName + '_project'] = ''; // Limpiar input
            };

            const addAlias = (containerName) => {
                const aName = inputs.value[containerName + '_alias'];
                if (!aName) return;
                apiCall('/api/alias/add', 'POST', { alias: aName.trim(), container: containerName });
                inputs.value[containerName + '_alias'] = ''; // Limpiar input
            };

            onMounted(() => {
                fetchData();
                // Opcional: auto-refrescar cada 10 segundos
                setInterval(fetchData, 10000); 
            });

            return { 
                containers, projects, aliases, inputs, notification, 
                fetchData, apiCall, addToProject, addAlias 
            };
        }
    }).mount('#app');
</script>
</body>
</html>
"""

# ==========================================
# RUTAS API (Backend para Vue)
# ==========================================

@app.route("/")
def index():
    # Solo entregamos la estructura HTML. Vue se encarga de rellenar los datos.
    return HTML

@app.route("/api/data", methods=["GET"])
def api_data():
    containers = client.containers.list(all=True)
    enriched = []
    for c in containers:
        enriched.append({
            "name": c.name,
            "status": c.status,
            "path": get_container_path(c)
        })
    return jsonify({"containers": enriched, "data": load_data()})

@app.route("/api/container/<action>/<name>", methods=["POST"])
def api_container(action, name):
    try:
        c = client.containers.get(name)
        if action == "start": c.start()
        elif action == "stop": c.stop()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- Rutas API para Alias ---
@app.route("/api/alias/add", methods=["POST"])
def api_alias_add():
    req = request.json
    data = load_data()
    data["aliases"][req["alias"]] = req["container"]
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/alias/<action>/<alias>", methods=["POST"])
def api_alias_action(action, alias):
    data = load_data()
    if alias in data["aliases"]:
        try:
            c = client.containers.get(data["aliases"][alias])
            if action == "start": c.start()
            elif action == "stop": c.stop()
            elif action == "delete":
                del data["aliases"][alias]
                save_data(data)
        except Exception as e:
            pass
    return jsonify({"success": True})


# --- Rutas API para Proyectos ---
@app.route("/api/project/add", methods=["POST"])
def api_project_add():
    req = request.json
    data = load_data()
    p = req["project"]
    c = req["container"]
    
    if p not in data["projects"]:
        data["projects"][p] = []
    if c not in data["projects"][p]:
        data["projects"][p].append(c)
        
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/project/<action>/<project>", methods=["POST"])
def api_project_action(action, project):
    data = load_data()
    if project in data["projects"]:
        if action == "delete":
            del data["projects"][project]
            save_data(data)
        else:
            for c_name in data["projects"][project]:
                try:
                    c = client.containers.get(c_name)
                    if action == "start": c.start()
                    elif action == "stop": c.stop()
                except:
                    pass
    return jsonify({"success": True})


# ==========================================
# INICIO DE LA APLICACIÓN O COMANDO CLI
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "start" and len(sys.argv) == 3:
            cli_start_project(sys.argv[2])
        elif command == "stop" and len(sys.argv) == 3:
            cli_stop_project(sys.argv[2])
        else:
            print("Uso desde terminal:")
            print("  j5d <nombre_proyecto>      (Inicia un proyecto)")
            print("  j5d-stop <nombre_proyecto> (Detiene un proyecto)")
            print("  python docker_manager.py   (Para iniciar el servidor web)")
            sys.exit(1)
    else:
        installed_files = setup_shell_aliases()
        if installed_files:
            print("✨ ¡Se han configurado los alias automáticamente!")
            for f in installed_files:
                print(f"   Añadido en: {f}")
            print("⚠️  IMPORTANTE: Para que los alias funcionen en esta misma ventana, ejecuta:")
            if any("zshrc" in f for f in installed_files):
                print("   source ~/.zshrc")
            else:
                print("   source ~/.bashrc")
            print("-" * 50)

        print("🌐 Iniciando servidor Web SPA en http://0.0.0.0:5555")
        app.run(host="0.0.0.0", port=5555)