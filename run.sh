#!/bin/bash

# Configuration du port
PORT=9096

# Fonction pour libérer le port si occupé
liberer_port() {
    PID=$(lsof -t -i:$PORT)
    if [ ! -z "$PID" ]; then
        echo "[+] Libération du port $PORT (Processus PID $PID en cours d'arrêt)..."
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
}

# Assurer le nettoyage lors de la fermeture du script (Ctrl+C, fermeture, etc.)
cleanup() {
    echo ""
    echo "[+] Nettoyage : Libération du port $PORT..."
    liberer_port
}
trap cleanup INT TERM

# Libérer le port au démarrage s'il est déjà occupé par une instance précédente
liberer_port

echo "============================================="
echo "   GESTIONNAIRE D'ACHAT-REVENTE - STARTUP   "
echo "============================================="

# 1. Détection/Création de l'environnement virtuel venv
if [ ! -d "venv" ]; then
    echo "[+] Création de l'environnement virtuel (venv)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[!] Erreur : Impossible de créer l'environnement virtuel. Assurez-vous que python3 est installé."
        exit 1
    fi
else
    echo "[~] Environnement virtuel venv existant détecté."
fi

# 2. Activation du venv
echo "[+] Activation de l'environnement virtuel..."
source venv/bin/activate

# 3. Installation/Mise à jour des dépendances
echo "[+] Installation des dépendances (Flask, Flask-SQLAlchemy)..."
pip install --upgrade pip
pip install Flask Flask-SQLAlchemy Werkzeug

# 4. Création des dossiers requis si manquants
echo "[+] Vérification et création des répertoires statiques..."
mkdir -p static/uploads templates

# 5. Démarrage de l'application Flask
echo "[+] Lancement de l'application sur le port $PORT..."
python app.py
