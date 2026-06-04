# Usa uma base oficial do Python super leve
FROM python:3.10-slim

# Impede que o Python crie ficheiros temporários inúteis
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala o Google Chrome real e o Xvfb (MÉTODO MODERNO SEM APT-KEY)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    libxi6 \
    libgbm1 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Cria a pasta de trabalho dentro da caixa
WORKDIR /app

# Copia a lista de compras e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do teu robô para dentro da caixa
COPY . .

# Abre a porta 5000 para o n8n poder falar com ele
EXPOSE 5000

# O Motor de Arranque: Liga o ecrã invisível e arranca o servidor API
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && python api_server.py"]