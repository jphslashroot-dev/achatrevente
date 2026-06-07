FROM python:3.12-slim

# Empêche Python de bufferiser stdout/stderr (logs en temps réel)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Installation des dépendances (cache optimisé)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif
COPY app.py .
COPY static/ static/
COPY templates/ templates/

# Création des répertoires persistants
RUN mkdir -p static/uploads

EXPOSE 9096

# Serveur de production gunicorn
# 'app:app' = objet Flask nommé 'app' dans app.py
CMD ["gunicorn", "--bind", "0.0.0.0:9096", "--workers", "2", "--timeout", "120", "app:app"]
