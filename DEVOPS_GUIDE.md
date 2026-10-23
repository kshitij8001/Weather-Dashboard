# AWS EC2 & DevOps Infrastructure Setup Guide
**TYCSE Cloud Computing & DevOps – CCA 2 Deployment Guide**

This guide provides the exact commands and configurations required to set up an **AWS EC2 Ubuntu Instance** running **Docker**, **Jenkins**, **Minikube**, and **Kubectl**.

---

## 1. AWS EC2 Instance Provisioning

### Recommended Specifications:
- **AMI:** Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
- **Instance Type:** `t3.medium` or `t3.large` *(Minikube requires at least 2 vCPUs and 4 GB RAM)*
- **Storage:** 25 GB - 30 GB gp3 root volume
- **Security Group Inbound Rules:**
  | Type | Port Range | Source | Purpose |
  |---|---|---|---|
  | SSH | 22 | My IP / 0.0.0.0/0 | SSH remote access |
  | Custom TCP | 8080 | 0.0.0.0/0 | Jenkins Web UI |
  | Custom TCP | 30080 | 0.0.0.0/0 | Weather Dashboard NodePort |
  | HTTP | 80 | 0.0.0.0/0 | Web traffic (optional) |
  | Custom TCP | 5000 | 0.0.0.0/0 | Flask local testing |

---

## 2. Server Installation Commands (Run on EC2)

Connect via SSH to your EC2 instance and run the following setup script:

```bash
# Update package lists
sudo apt-get update && sudo apt-get upgrade -y

# 1. Install Java 17 (Required by Jenkins)
sudo apt-get install -y openjdk-17-jdk git curl wget apt-transport-https ca-certificates gnupg lsb-release

# 2. Install Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# 3. Install Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt-get update
sudo apt-get install -y jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins

# 4. Install Kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 5. Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# 6. Install Python & Build Tools
sudo apt-get install -y python3 python3-pip python3-venv
```

---

## 3. Configuring Permissions for Jenkins

Jenkins runs as the `jenkins` user. It needs permission to use Docker and communicate with Minikube:

```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins

# Give Jenkins sudo access for Minikube/Kubectl without password prompt (if needed)
echo "jenkins ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/jenkins

# Restart Jenkins and Docker to apply group changes
sudo systemctl restart docker
sudo systemctl restart jenkins
```

---

## 4. Starting Minikube on EC2

Run Minikube as the `ubuntu` user with the docker driver:

```bash
# Start Minikube with 2 CPUs and 3GB memory
minikube start --driver=docker --cpus=2 --memory=3072

# Verify cluster status
minikube status
kubectl cluster-info
kubectl get nodes
```

### Exposing Minikube Kubeconfig to Jenkins:
To allow the Jenkins user to use `kubectl`:

```bash
# Copy kubeconfig to jenkins user's home
sudo mkdir -p /var/lib/jenkins/.kube
sudo cp -r /home/ubuntu/.kube/config /var/lib/jenkins/.kube/config
sudo cp -r /home/ubuntu/.minikube /var/lib/jenkins/.minikube
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube
sudo chown -R jenkins:jenkins /var/lib/jenkins/.minikube

# Update client certificate paths in /var/lib/jenkins/.kube/config:
sudo sed -i 's|/home/ubuntu/|/var/lib/jenkins/|g' /var/lib/jenkins/.kube/config

# Test kubectl as jenkins user
sudo -u jenkins kubectl get nodes
```

---

## 5. Setting up Jenkins Web UI

1. Open your browser and navigate to:
   ```
   http://<EC2-PUBLIC-IP>:8080
   ```
2. Retrieve the initial admin password from EC2:
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
3. Click **"Install suggested plugins"**.
4. Create your Admin user.
5. Install Additional Plugins (Navigate to `Dashboard > Manage Jenkins > Plugins > Available plugins`):
   - **Credentials Binding Plugin** (usually preinstalled)
   - **Docker Pipeline**
   - **Pipeline Stage View**
   - **JUnit Plugin**

---

## 6. Configuring Docker Hub Credentials in Jenkins

1. Go to: **Dashboard > Manage Jenkins > Credentials > System > Global credentials (unrestricted)**.
2. Click **+ Add Credentials**.
3. Fill in:
   - **Kind:** `Username with password`
   - **Scope:** `Global`
   - **Username:** Your Docker Hub username (e.g., `kshitij8001`)
   - **Password:** Your Docker Hub password or Personal Access Token
   - **ID:** `dockerhub-credentials` *(Must match `DOCKER_CREDS_ID` in Jenkinsfile)*
   - **Description:** `Docker Hub Registry Credentials`
4. Click **Create**.

---

## 7. Creating the Jenkins Pipeline Job

1. Go to Jenkins Home, click **"New Item"**.
2. Enter item name: `Weather-Dashboard-Pipeline`.
3. Select **"Pipeline"** and click **OK**.
4. Scroll to the **Pipeline** section:
   - **Definition:** `Pipeline script from SCM`
   - **SCM:** `Git`
   - **Repository URL:** `https://github.com/<your-username>/Weather-Dashboard.git`
   - **Branch Specifier:** `*/main`
   - **Script Path:** `Jenkinsfile`
5. Click **Save**.
6. Click **"Build Now"** to execute your first pipeline run!

---

## 8. Accessing the Application from Browser

When the pipeline completes Step 6 and Step 7:
1. Minikube exposes the service on NodePort `30080`.
2. To route traffic from EC2 public IP to Minikube's internal IP:
   ```bash
   # Run in background on EC2
   kubectl port-forward --address 0.0.0.0 service/weather-dashboard-service 30080:80 &
   ```
   *(Or using minikube service tunnel)*:
   ```bash
   minikube service weather-dashboard-service --url
   ```
3. Open in your web browser:
   ```
   http://<EC2-PUBLIC-IP>:30080
   ```
4. Verify endpoints:
   - UI: `http://<EC2-PUBLIC-IP>:30080/`
   - Health check: `http://<EC2-PUBLIC-IP>:30080/health`
   - Weather API: `http://<EC2-PUBLIC-IP>:30080/api/weather?city=Pune`
   - System Info: `http://<EC2-PUBLIC-IP>:30080/api/info`

---

## 9. Demonstrating Code Change (Step 9 of Student Guide)

To demonstrate the source-code redeployment during evaluation:
1. In `app.py`, update:
   ```python
   APP_VERSION = "2.0.0"
   ```
2. Commit and push:
   ```bash
   git commit -am "chore: bump release to v2.0.0 for pipeline redeployment demo"
   git push origin main
   ```
3. Trigger or watch Jenkins run Build #2.
4. Refresh browser at `http://<EC2-PUBLIC-IP>:30080` to show the updated `v2.0.0` badge live!
