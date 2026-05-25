# AI Task Manager

Un task manager Kanban potenziato da un assistente AI locale. Gestisci progetti e attività, monitora scadenze e priorità, e interagisci con un LLM (qwen2.5:1.5b-Instruct via Ollama) che può creare, aggiornare ed eliminare task attraverso linguaggio naturale — il tutto **100% offline**, senza API cloud.

## Funzionalità

- **Kanban**: board a tre colonne (Da fare / In corso / Completati) con transizioni rapide
- **Dashboard**: metriche di completamento, task in scadenza e distribuzione per priorità
- **Assistente AI**: chat con un agente ReAct che chiama tool reali su MongoDB (16 tool disponibili)
- **Gestione progetti**: CRUD con cascade delete dei task associati
- **Gestione utenti**: anagrafica con ruoli (user / admin)
- **Allegati**: upload file con archiviazione GridFS
- **Storico modifiche**: ogni cambio di stato, priorità o descrizione è tracciato con timestamp e autore

## Requisiti di sistema

- Python 3.11+
- MongoDB in esecuzione su `localhost:27017`
- [Ollama](https://ollama.com) installato e in esecuzione

## Installazione

```bash
# 1. Clona la repository
git clone https://github.com/LucaM711/ai-task-manager.git
cd ai-task-manager

# 2. Crea e attiva il virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env se necessario (i default funzionano con MongoDB e Ollama in locale)
```

## Scarica il modello LLM

Assicurati che Ollama sia in esecuzione, poi:

```bash
ollama pull qwen2.5:1.5b-Instruct
```

> Il modello occupa circa 1 GB su disco. Puoi usarne uno diverso aggiornando `OLLAMA_MODEL` nel file `.env`.

## Popola il database (opzionale)

Lo script crea utenti, un progetto demo e 10 task con scadenze relative alla data odierna:

```bash
python scripts/seed_data.py
```

È idempotente: puoi ri-eseguirlo senza duplicare utenti o progetti.

## Avvio

```bash
streamlit run app.py
```

L'app si apre automaticamente su [http://localhost:8501](http://localhost:8501).

## Test

```bash
pytest tests/ -v
```

I test di repository richiedono MongoDB attivo su `localhost:27017`. Usano il database `ai_task_manager_test`, separato da quello di produzione.

## Struttura del progetto

```
ai-task-manager/
├── app.py                  # Entry point Streamlit
├── pages/                  # UI (Presentazione)
│   ├── 00_progetti.py
│   ├── 01_kanban.py
│   ├── 02_dashboard.py
│   ├── 03_assistente.py
│   └── 04_utenti.py
├── services/               # Business logic
├── repositories/           # CRUD MongoDB
├── models/                 # Schema Pydantic v2
├── ai/                     # Agent LangGraph + tool LangChain
├── config/                 # Settings e connessione DB
├── tests/                  # Test suite (55 test)
└── scripts/                # Utility (seed data)
```

## Stack

| Componente | Tecnologia |
|---|---|
| UI | Streamlit |
| Database | MongoDB + GridFS |
| AI agent | LangGraph + LangChain |
| LLM locale | Ollama — qwen2.5:1.5b-Instruct |
| Modelli dati | Pydantic v2 |
| Grafici | Plotly |
| Test | pytest |
