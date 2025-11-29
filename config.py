import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Telegram API sozlamalari
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Sozlamalar
MESSAGE_INTERVAL_MINUTES = int(os.getenv('MESSAGE_INTERVAL_MINUTES', 5))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Ruxsat etilgan foydalanuvchilar (Telegram ID lar)
ALLOWED_USER_IDS_STR = os.getenv('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS = []
if ALLOWED_USER_IDS_STR:
    try:
        ALLOWED_USER_IDS = [int(uid.strip()) for uid in ALLOWED_USER_IDS_STR.split(',') if uid.strip()]
    except ValueError:
        print("OGOHLANTIRISH: ALLOWED_USER_IDS noto'g'ri formatda. Faqat raqamlar va vergul ishlatilishi kerak.")

# Session papkasi
SESSION_DIR = os.path.join(os.path.dirname(__file__), 'sessions')
os.makedirs(SESSION_DIR, exist_ok=True)

# Logging sozlamalari
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(os.path.dirname(__file__), 'bot.log')

# Foydalanuvchi ruxsatini tekshirish
def is_user_allowed(telegram_id):
    """Foydalanuvchi ruxsat etilganmi?"""
    if not ALLOWED_USER_IDS:
        return True  # Agar ro'yxat bo'sh bo'lsa, hammaga ruxsat
    return telegram_id in ALLOWED_USER_IDS

# Shaxsiy telefon raqami (user client uchun)
USER_PHONE = os.getenv('USER_PHONE')
