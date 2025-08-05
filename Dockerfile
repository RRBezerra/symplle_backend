# =============================================================================
# DOCKERFILE - symplle-enterprise/Dockerfile
# =============================================================================

# Multi-stage build para otimização
FROM python:3.9-slim as base

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash symplle

# Set working directory
WORKDIR /app

# Copiar requirements primeiro (para cache)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM base as production

# Copiar código da aplicação
COPY src/ ./src/
COPY scripts/ ./scripts/

# Mudar ownership para usuário symplle
RUN chown -R symplle:symplle /app
USER symplle

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Command to run
CMD ["python", "src/main.py"]

# =============================================================================
# DEVELOPMENT STAGE  
# =============================================================================
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir pytest flask-testing

# Copy source code
COPY . .

# Set environment
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Expose port
EXPOSE 5000

# Run in development mode
CMD ["python", "src/main.py"]