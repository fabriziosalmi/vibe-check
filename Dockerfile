# Usa un'immagine Python slim per velocità e dimensioni ridotte
FROM python:3.10-slim

# Install git for commit history analysis
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copia lo script nel container
COPY vibeguard.py /vibeguard.py

# Esegui lo script quando parte il container
ENTRYPOINT ["python", "/vibeguard.py"]
