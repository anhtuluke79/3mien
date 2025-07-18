# utils/ai_rf/__init__.py

from .rf_db import train_rf_db, predict_rf_xsmb
from .rf_lo import train_rf_lo_mb, predict_rf_lo_mb

def train_all_ai():
    ok_db = train_rf_db()
    ok_lo = train_rf_lo_mb()
    return ok_db and ok_lo
