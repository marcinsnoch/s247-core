# Dziennik zmian — s247 Core

Wszystkie istotne zmiany w serwisie backendowym `s247-core` są dokumentowane w tym pliku.

Format oparty jest o zasady [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

## [1.1.0] - 2026-09-06

### Dodano
- Wdrożenie standardu Auth Design wg **wariantu pragmatycznego 1.2**:
  - Endpoint wydawania tokenów `POST /v1/auth/token` obsługujący granty `password` oraz `refresh_token` z parametrami `username`/`email` i `password`.
  - Endpoint odświeżania tokenów `POST /v1/auth/token/refresh` z mechanizmem natychmiastowej rotacji (Refresh Token Rotation - RTR).
  - Model bazy danych `RefreshToken` (`refresh_tokens`) do śledzenia i bezpiecznego unieważniania tokenów odświeżających w bazie.
  - Endpointy unieważnienia sesji / wylogowania: `DELETE /v1/auth/token`, `POST /v1/auth/token/revoke` oraz `POST /v1/auth/logout`.
  - Rejestracja użytkownika `POST /v1/auth/register`.
  - Procedura resetu hasła: `POST /v1/auth/password/forgot` oraz `POST /v1/auth/password/reset`.
  - Zwracanie standardowego nagłówka `WWW-Authenticate: Bearer error="invalid_token"` przy błędach `401 Unauthorized`.
  - Zachowanie kompatybilności wstecznej dla aliasów `/v1/auth/login` i `/v1/auth/refresh`.

### Zmieniono
- Skrócono czas życia tokenu dostępowego do 15 minut (`ACCESS_TOKEN_EXPIRE_MINUTES = 15`), dodano `REFRESH_TOKEN_EXPIRE_DAYS = 7`.
- Uelastyczniono walidację adresów e-mail, aby poprawnie obsługiwać domeny lokalne (np. `.local`).

## [1.0.0] - 2026-09-05

### Dodano
- Fundament aplikacji FastAPI z obsługą lifespan, konfiguracją CORS i monitorowaniem stanu pod `/health`.
- Architektura trójwarstwowa: routery (`app/routers/`), serwisy (`app/services/`), repozytoria (`app/repositories/`).
- Asynchroniczna konfiguracja ORM SQLAlchemy 2.0 (`asyncpg`) z automatycznym tworzeniem schematu bazy.
- Modele domenowe w `app/models/`: `Workspace`, `User` (role: admin, technician, client), `Ticket` (statusy, priorytety), `Device`.
- Schematy walidacji wejścia/wyjścia Pydantic v2 w `app/schemas/`.
- Bezpieczeństwo i uwierzytelnianie: haszowanie bcrypt, generowanie tokenów JWT (HS256) oraz obsługa dekodowania kluczy RSA (RS256 dla urządzeń/RabbitMQ).
- Wstrzykiwanie zależności autoryzacyjnych (`get_current_user`, `require_admin`, `require_staff`).
- Punkty końcowe REST API dla modułów:
  - Uwierzytelnianie (`/v1/auth/login`, alias `/auth/login`),
  - Użytkownicy (`/v1/users`, `/v1/users/me`),
  - Zgłoszenia serwisowe (`/v1/tickets`).
- Konsument RabbitMQ `app/workers/consumer.py` wykorzystujący `aio_pika`.
- Konfiguracja projektu `pyproject.toml` pod menedżer `uv` oraz `Dockerfile` bazujący na Python 3.11-slim.
- Zestaw testów jednostkowych w `tests/` wykorzystujący silnik w pamięci SQLite (`aiosqlite`).
- Dokumentacja `README.md` oraz `DEVELOPER.md`.
