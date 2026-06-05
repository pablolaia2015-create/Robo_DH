# 1. SISTEMA OPERATIVO: Usa uma base oficial do Python super leve
FROM python:3.10-slim

# 2. CONFIGURAÇÕES GERAIS
# Impede que o Python crie ficheiros temporários inúteis (.pyc)
ENV PYTHONDONTWRITEBYTECODE=1
# Força os logs a aparecerem imediatamente no painel do Google Cloud (sem atrasos)
ENV PYTHONUNBUFFERED=1

# 3. INSTALAÇÃO DO CHROME E DO "ECRÃ INVISÍVEL" (Xvfb)
# O Google Cloud não tem monitor. O Xvfb simula um ecrã para o Fato Mecânico não quebrar.
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

# 4. PASTA DE TRABALHO: Cria a pasta principal dentro da nossa "caixa"
WORKDIR /app

# 5. DEPENDÊNCIAS: Copia a lista de compras e instala tudo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. CÓDIGO FONTE: Copia o resto do teu robô para dentro da caixa
COPY . .

# 7. PORTA DE COMUNICAÇÃO
# Expor a porta 5000 é útil para testes locais. No Google Cloud, o servidor irá ignorar isto 
# e injetar a sua própria porta dinamicamente no api_server.py.
EXPOSE 5000

# 8. O MOTOR DE ARRANQUE
# Liga o ecrã invisível (Xvfb) na porta :99 com resolução 1920x1080, e arranca o servidor API
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && python api_server.py"]