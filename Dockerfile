FROM python:3.11-slim

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend and build it
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build

# Copy backend source
COPY api_sqlite.py .
COPY create_sqlite_db.py .
COPY rule_configs/ ./rule_configs/
COPY rules_engine/ ./rules_engine/
COPY protocol_definition.json .
COPY synthetic_data_part1.json .
COPY synthetic_data_part2.json .
COPY synthetic_data_part3.json .
COPY schema.sql .

# Startup script: seed DB if it doesn't exist, then launch API
RUN printf '#!/bin/bash\nset -e\nif [ ! -f /app/clinical_trial.db ]; then\n  echo "First run — seeding database..."\n  python /app/create_sqlite_db.py\n  echo "Database ready."\nfi\nexec uvicorn api_sqlite:app --host 0.0.0.0 --port ${PORT:-8000}\n' > /app/start.sh \
  && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
