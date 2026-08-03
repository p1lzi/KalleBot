# Minecraft Struktur/Biom/Farm-Finder Bot - Docker Image
FROM python:3.11-slim

WORKDIR /app

# Abhängigkeiten zuerst kopieren und installieren, damit Docker diesen Layer
# cachen kann, solange sich requirements.txt nicht ändert.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Restlichen Code kopieren
COPY . .

ENV PYTHONUNBUFFERED=1

# Hinweis: Der Discord-Token wird zur Laufzeit über eine .env-Datei oder
# Umgebungsvariablen übergeben (siehe README), nicht ins Image eingebaut.
CMD ["python", "bot.py"]