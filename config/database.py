from config.settings import settings
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
        self.db = self.client[settings.mongodb_db_name]

    def get_database(self, db_name: str = None):
        if db_name:
            return self.client[db_name]
        return self.db


def ensure_mongo_available() -> None:
    """Verifica che MongoDB sia raggiungibile. Da chiamare in cima a ogni pagina Streamlit.

    Se la connessione fallisce, mostra un messaggio chiaro e ferma il rendering
    della pagina (st.stop). Importato qui dentro per non forzare la dipendenza
    da streamlit nei layer non-UI.
    """
    import streamlit as st
    try:
        # ping forza una connessione effettiva (MongoClient è lazy)
        MongoDBClient().client.admin.command("ping")
    except (ServerSelectionTimeoutError, ConnectionFailure):
        st.error(
            f"⚠️ MongoDB non raggiungibile su `{settings.mongodb_uri}`.\n\n"
            "Avvia il servizio MongoDB (es. `mongod`) o verifica `MONGODB_URI` in `.env`."
        )
        st.stop()
