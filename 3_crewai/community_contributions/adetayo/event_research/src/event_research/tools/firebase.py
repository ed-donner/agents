import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

_db = None

def get_db():
    global _db

    if _db:
        return _db

    config = json.loads(os.getenv("FIREBASE_CONFIG_JSON"))
    cred = credentials.Certificate(config)
    firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db