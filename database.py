import json
import os
from contextlib import contextmanager
from threading import RLock
from datetime import datetime
import config
from utils import logger

# JSON fayl yo'li
DB_FILE = os.path.join(os.path.dirname(__file__), 'database.json')

# Thread-safe lock
db_lock = RLock()

# Ma'lumotlar bazasi strukturasi
DEFAULT_DB = {
    'users': [],
    'groups': [],
    'messages': [],
    'scheduled_tasks': []
}

class JSONDatabase:
    """JSON fayl bilan ishlash uchun class"""
    
    @staticmethod
    def _read_db():
        """JSON faylni o'qish"""
        if not os.path.exists(DB_FILE):
            return DEFAULT_DB.copy()
        
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON o'qishda xatolik: {str(e)}")
            return DEFAULT_DB.copy()
    
    @staticmethod
    def _write_db(data):
        """JSON faylga yozish"""
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"JSON yozishda xatolik: {str(e)}")
            raise
    
    @staticmethod
    def get_next_id(collection_name):
        """Keyingi ID ni olish"""
        with db_lock:
            db = JSONDatabase._read_db()
            collection = db.get(collection_name, [])
            if not collection:
                return 1
            return max([item.get('id', 0) for item in collection]) + 1

# Context manager for database operations
@contextmanager
def get_db():
    """Database context manager"""
    with db_lock:
        db = JSONDatabase._read_db()
        try:
            yield db
            JSONDatabase._write_db(db)
        except Exception as e:
            logger.error(f"Database xatolik: {str(e)}")
            raise

# Database yaratish
def init_db():
    """Ma'lumotlar bazasini yaratish"""
    try:
        if not os.path.exists(DB_FILE):
            JSONDatabase._write_db(DEFAULT_DB)
            logger.info("JSON ma'lumotlar bazasi yaratildi")
        else:
            logger.info("JSON ma'lumotlar bazasi mavjud")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasi yaratishda xatolik: {str(e)}")
        raise

# Database tozalash (test uchun)
def clear_db():
    """Barcha ma'lumotlarni o'chirish (EHTIYOT!)"""
    JSONDatabase._write_db(DEFAULT_DB)
    logger.warning("Barcha ma'lumotlar o'chirildi!")
