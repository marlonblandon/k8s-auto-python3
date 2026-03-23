#este script te prepara el worker para poder unirlo al master de Kubernetes

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
    # Pedir al usuario el nombre del worker
    server_name = input("Ingrese el nombre que desea asignar al worker: ").strip()
    run_cmd(["sudo", "hostnamectl", "set-hostname", server_name])
    run_cmd("sudo sed -i '/127.0.1.1/d' /etc/hosts", shell=True)
    run_cmd(f"echo '127.0.1.1   {server_name}' | sudo tee -a /etc/hosts", shell=True)

    # Desactivar swap
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
    run_cmd("curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key -o /tmp/kubernetes.key", shell=True)
    run_cmd("sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg /tmp/kubernetes.key", shell=True)
    run_cmd("echo \"deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /\" | sudo tee /etc/apt/sources.list.d/kubernetes.list", shell=True)
    run_cmd(["sudo", "apt-get", "update"])
    run_cmd(["sudo", "apt-get", "install", "-y", "kubelet", "kubeadm", "kubectl"])
    run_cmd(["sudo", "apt-mark", "hold", "kubelet", "kubeadm", "kubectl"])

    print("\n✅ Worker configurado correctamente.")
    print("👉 Ahora ejecuta en este nodo el comando de unión que te dio el master (kubeadm join ...).")

except Exception as e:
    print(f"\n❌ Error: {e}")

# ejecuta este comando en el master copia el resultado usando sudo y pegalo en el worker para unirlo.
# kubeadm token create --print-join-command
