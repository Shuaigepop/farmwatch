#!/bin/bash
set -e

echo "======================================"
echo " FarmWatch GCP Server Installer"
echo "======================================"

# 1. Update and install prerequisites
echo "[1/4] Updating system and installing dependencies..."
sudo apt-get update
sudo apt-get install -y unzip apt-transport-https ca-certificates curl software-properties-common

# 2. Install Docker
echo "[2/4] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    echo "Docker is already installed."
fi

# 3. Unzip project
echo "[3/4] Preparing project files..."
cd ~
if [ -f "farmwatch-cloud.zip" ]; then
    unzip -q -o farmwatch-cloud.zip -d farmwatch
    cd farmwatch
else
    echo "ERROR: farmwatch-cloud.zip not found in home directory!"
    echo "Please upload the zip file first using the SSH 'Upload file' button."
    exit 1
fi

# 4. Start Docker container
echo "[4/4] Building and starting FarmWatch container..."
sudo docker compose up -d --build

echo "======================================"
echo " Installation Complete!"
echo " FarmWatch is now running on port 80."
echo " You can access it via your GCP External IP."
echo "======================================"
