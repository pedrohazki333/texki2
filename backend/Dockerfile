FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
      "fastapi>=0.115" \
      "uvicorn[standard]>=0.32" \
      "sqlalchemy>=2.0" \
      "alembic>=1.13" \
      "psycopg[binary]>=3.2" \
      "pydantic>=2.9" \
      "pydantic-settings>=2.6" \
      "email-validator>=2.2" \
      "bcrypt>=4.2" \
      "pyjwt>=2.10" \
      "pillow>=11.0" \
      "python-multipart>=0.0.20" \
      "pytest>=8.3" \
      "httpx>=0.27"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
