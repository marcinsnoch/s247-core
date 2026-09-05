# s247 Core — Backend REST API

Serwis centralny platformy **s247**, odpowiedzialny za obsługę zgłoszeń serwisowych (ticketów), telemetrii, urządzeń oraz uwierzytelnianie użytkowników i maszyn.

Zbudowany w języku **Python 3.11** z wykorzystaniem frameworka **FastAPI** oraz asynchronicznego ORM **SQLAlchemy 2.0** w architekturze modułowej (*Modular Monolith*).

---

## Architektura modułowa (app/modules)

Kod zorganizowany jest wokół domen biznesowych (feature-based modules):

```text
app/
├── core/                       # Globalna konfiguracja, security, middleware, lifespan
├── database/                   # Połączenie z bazą, sesje, modele zbiorcze (models.py)
├── shared/                     # Wspólne wyjątki (BaseAppException) i paginacja
├── modules/
│   ├── auth/                   # Logowanie, tokeny JWT (router, service, schemas)
│   ├── profile/                # Profil zalogowanego użytkownika (/v1/me)
│   ├── users/                  # Zarządzanie użytkownikami (models, repository, service, router)
│   ├── workspaces/             # Obszary robocze / tenanci WS0001 (models, repository, service, router)
│   ├── tickets/                # Zgłoszenia serwisowe (models, repository, service, router)
│   └── devices/                # Urządzenia i diagnostyka (models, repository, service, router)
├── workers/
│   └── consumer.py             # Asynchroniczny worker RabbitMQ (aio_pika)
└── main.py                     # Aplikacja FastAPI, rejestracja modułów i handlerów błędów
```

---

## Główne funkcjonalności

1. **Uwierzytelnianie**:
   - Użytkownicy: JWT podpisany algorytmem symetrycznym HS256.
   - Maszyny/IoT: weryfikacja asymetrycznych tokenów RSA (RS256) z brokera RabbitMQ OAuth2.
2. **Obsługa zgłoszeń (Tickets)**:
   - Rejestracja zgłoszeń serwisowych z automatyczną numeracją (np. `TICK-2026-XXXX`).
   - Cykl życia zgłoszenia: `new` ➔ `in_progress` ➔ `waiting_for_parts` ➔ `resolved` ➔ `closed`.
   - Priorytetyzacja i przypisywanie serwisantów.
3. **Obszary robocze (Workspaces)**:
   - Multi-tenancy powiązane z nazewnictwem vhostów RabbitMQ (`WS0001`, `WS0002`...).
4. **Urządzenia (Devices)**:
   - Katalog maszyn i urządzeń objętych serwisem oraz diagnostyką.

---

## Wymagania

- Python 3.11+
- Zarządca pakietów `uv`
- PostgreSQL 18
- RabbitMQ 4
