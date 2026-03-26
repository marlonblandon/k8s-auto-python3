import subprocess

# URLs de los archivos
url_master = "https://raw.githubusercontent.com/marlonblandon/k8s-auto-python3/master/k8s-master-auto.py"
url_worker = "https://raw.githubusercontent.com/marlonblandon/k8s-auto-python3/master/k8s-worker-auto.py"

# Pedir datos de conexión
ip = input("👉 Ingresa la IP del servidor: ").strip()
usuario = input("👤 Ingresa el usuario SSH: ").strip()

# Elegir archivo
opcion = input("📂 Escribe 'master' o 'worker' para elegir el archivo: ").strip().lower()
if opcion == "master":
    url = url_master
    nombre = "k8s-master-auto.py"
elif opcion == "worker":
    url = url_worker
    nombre = "k8s-worker-auto.py"
else:
    print("❌ Opción inválida.")
    exit(1)

# Comando remoto: descargar y ejecutar
comando_remoto = f"wget -O {nombre} {url} && python3 {nombre}"

print(f"🔌 Conectando a {usuario}@{ip} y ejecutando: {comando_remoto}")
# -t fuerza sesión interactiva, así te quedas dentro del servidor después
subprocess.call(["ssh", "-t", f"{usuario}@{ip}", comando_remoto])
