#Como configurar K8s-master usando Python
#metes todo este script en el servidor K8s-master como un archivo .py
#asegurate de tener instaldo python3 en ese servidor
#cambia el archivo para que sea ejecutable con   chmod +x <nombre del archivo .py>   
  #nota: si el archivo se ejecuta con el comando python3 autok8s-master.py "no necesitara los permisos +x"
#ten presente la ip del servidor y el nombre que le pondras(te lo pedira en el momento de la ejecución)
#2 formas de ejecutar el comando   1:  ./nombredelarchivo.py     2:  python3 nombredelarchvo.py

#Si lo quieres correr desde Github prueba este metodo
#git clone https://github.com/marlonblandon/autok8s.git && cd autok8s && chmod +x autok8s-master.py && ./autok8s-master.py


#!/usr/bin/env python3
import subprocess

def run_cmd(cmd, shell=False):
    print(f"\n>>> Ejecutando: {cmd if shell else ' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=shell)
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise Exception(f"Error en comando: {cmd if shell else ' '.join(cmd)}")

try:
    # Pedir al usuario el nombre del servidor
    server_name = input("Ingrese el nombre que desea asignar al servidor: ").strip()
    run_cmd(["sudo", "hostnamectl", "set-hostname", server_name])

    # Swap
    run_cmd(["sudo", "swapoff", "-a"])
    run_cmd(["sudo", "sed", "-i", "/ swap / s/^/#/", "/etc/fstab"])

    # Módulos kernel
    run_cmd("cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf\noverlay\nbr_netfilter\nEOF", shell=True)
    run_cmd(["sudo", "modprobe", "overlay"])
    run_cmd(["sudo", "modprobe", "br_netfilter"])

    # Sysctl
    run_cmd("cat <<EOF | sudo tee /etc/sysctl.d/kubernetes.conf\nnet.bridge.bridge-nf-call-iptables = 1\nnet.ipv4.ip_forward = 1\nnet.bridge.bridge-nf-call-ip6tables = 1\nEOF", shell=True)
    run_cmd(["sudo", "sysctl", "--system"])

    # Instalar containerd
    run_cmd(["sudo", "apt-get", "update"])
    run_cmd(["sudo", "apt-get", "install", "-y", "containerd"])
    run_cmd(["sudo", "mkdir", "-p", "/etc/containerd"])
    run_cmd("sudo containerd config default | sudo tee /etc/containerd/config.toml > /dev/null", shell=True)
    run_cmd(["sudo", "sed", "-i", "s/SystemdCgroup = false/SystemdCgroup = true/", "/etc/containerd/config.toml"])
    run_cmd(["sudo", "systemctl", "restart", "containerd"])
    run_cmd(["sudo", "systemctl", "enable", "containerd"])

    # Instalar kubelet, kubeadm, kubectl
    run_cmd(["sudo", "apt-get", "install", "-y", "apt-transport-https", "ca-certificates", "curl"])
    run_cmd("sudo mkdir -p /etc/apt/keyrings", shell=True)
    run_cmd("sudo curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg", shell=True)
    run_cmd("echo \"deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /\" | sudo tee /etc/apt/sources.list.d/kubernetes.list", shell=True)
    run_cmd(["sudo", "apt-get", "update"])
    run_cmd(["sudo", "apt-get", "install", "-y", "kubelet", "kubeadm", "kubectl"])
    run_cmd(["sudo", "apt-mark", "hold", "kubelet", "kubeadm", "kubectl"])

    # 🔥 Limpieza completa de intentos previos
    run_cmd(["sudo", "kubeadm", "reset", "-f"])
    run_cmd(["sudo", "systemctl", "stop", "kubelet"])
    run_cmd(["sudo", "systemctl", "stop", "containerd"])
    run_cmd("for port in 6443 10259 10257 10250 2379 2380; do pid=$(sudo lsof -ti :$port); if [ -n \"$pid\" ]; then sudo kill -9 $pid; fi; done", shell=True)
    run_cmd(["sudo", "rm", "-rf", "/etc/kubernetes", "/var/lib/etcd", "/var/lib/kubelet", "/etc/cni/net.d"])
    run_cmd(["sudo", "systemctl", "start", "containerd"])
    run_cmd(["sudo", "systemctl", "start", "kubelet"])

    # Pedir la IP al usuario
    ip_address = input("Ingrese la IP que usará el master (apiserver-advertise-address): ").strip()

    # Inicializar cluster con la IP elegida
    run_cmd([
        "sudo", "kubeadm", "init",
        f"--apiserver-advertise-address={ip_address}",
        "--pod-network-cidr=10.244.0.0/16"
    ])

    # Configurar kubectl para el usuario actual
    run_cmd("mkdir -p $HOME/.kube && sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config", shell=True)

    # Instalar Calico
    run_cmd(["curl", "-O", "https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/calico.yaml"])
    run_cmd(["kubectl", "apply", "-f", "calico.yaml"])

    print("\n✅ Master configurado correctamente")

except Exception as e:
    print(f"\n❌ Error: {e}")


"""
Como unir los workers al master

1. Obtener el comando de unión desde el master
kubeadm token create --print-join-command

2. Preparar cada worker
# Desactivar swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Cargar módulos necesarios
cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Configurar parámetros de red
cat <<EOF | sudo tee /etc/sysctl.d/kubernetes.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system

sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

3. Instalar kubelet, kubeadm y kubectl
sudo apt-get install -y apt-transport-https ca-certificates curl
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key -o /tmp/kubernetes.key
sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg /tmp/kubernetes.key

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" \
| sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

4. Unir el worker al clúster
kubeadm token create --print-join-command

ej: 
sudo kubeadm join 192.168.1.100:6443 --token abcdef.0123456789abcdef \
    --discovery-token-ca-cert-hash sha256:1234567890abcdef...

5. una vez tengas el token metes en el worker el comando


"""
