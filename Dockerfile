# Usa un'immagine Python slim per velocità e dimensioni ridotte
FROM python:3.10-slim

# Copia lo script nel container
COPY vibeguard.py /vibeguard.py

# Esegui lo script quando parte il container
ENTRYPOINT ["python", "/vibeguard.py"]
