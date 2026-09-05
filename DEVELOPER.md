# Instrukcje deweloperskie — s247 Core

Przewodnik dla programistów rozwijających backend `s247-core`.

---

## 1. Instalacja środowiska lokalnego z `uv`

```bash
cd s247-core

# Utworzenie wirtualnego środowiska
uv venv

# Aktywacja środowiska
source .venv/bin/activate

# Instalacja zależności aplikacji wraz z pakietami testowymi
uv pip install -e ".[dev]"
```

---

## 2. Zmienne środowiskowe (.env)

Skopiuj przykładowy plik `.env.example`:

```bash
cp .env.example .env
```

Dla uruchamiania bezpośrednio na maszynie hosta (poza Dockerem), gdy baza PostgreSQL działa na porcie `5433`:
```dotenv
DATABASE_URL=postgresql+asyncpg://db_admin:SuperBezpieczneHasloPostgres123!@localhost:5433/s247_database
RABBITMQ_URL=amqp://core_app:password123@localhost:5673/hub
```

---

## 3. Uruchamianie aplikacji w trybie deweloperskim

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Dokumentacja interaktywna API Swagger:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

Domyślne konto administratora generowane przy pierwszym starcie:
- **Email**: `admin@s247.local`
- **Hasło**: `admin123`

---

## 4. Uruchamianie testów automatycznych

```bash
pytest
```

---

## 5. Uruchamianie konsumenta RabbitMQ

```bash
python app/workers/consumer.py
```

---

## 6. Resetowanie bazy danych (Szybki reset schematu)

Aby wyczyścić wszystkie tabele, relacje, typy enum i zrestartować schemat bazy bez utraty uprawnień czy usuwania wolumenu:

```bash
# Wykonaj czyszczenie schematu public w kontenerze bazy
docker exec -i s247_postgres psql -U db_admin -d s247_database -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Zrestartuj aplikację core (lifespan automatycznie odtworzy tabele i dane startowe)
docker compose -f ../s247-stack/compose.yml restart core_app
```
