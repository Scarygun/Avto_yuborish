import logging
from functools import wraps
from datetime import datetime
import config

# Logging sozlash
def setup_logging():
    """Logging tizimini sozlash"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Xatoliklarni qayta ishlash dekoratori
def handle_errors(func):
    """Xatoliklarni qayta ishlash uchun dekorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Xatolik {func.__name__} da: {str(e)}", exc_info=True)
            raise
    return wrapper

# Vaqtni formatlash
def format_datetime(dt):
    """Datetime ni o'qilishi oson formatga o'tkazish"""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Telefon raqamni tekshirish
def validate_phone(phone):
    """Telefon raqamni tekshirish"""
    # Faqat raqamlar va + belgisi
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned

# Interval soatlarni tekshirish
def validate_interval_hours(hours):
    """Interval soatlarni tekshirish"""
    try:
        h = int(hours)
        if h < 1 or h > 168:  # 1 soatdan 1 haftagacha
            return None
        return h
    except (ValueError, TypeError):
        return None

# Xabar matnini tekshirish
def validate_message_text(text):
    """Xabar matnini tekshirish"""
    if not text or len(text.strip()) == 0:
        return False, "Xabar matni bo'sh bo'lishi mumkin emas"
    if len(text) > 4096:  # Telegram limit
        return False, "Xabar matni 4096 belgidan oshmasligi kerak"
    return True, text.strip()

# Pagination uchun
def paginate_list(items, page=1, per_page=10):
    """Ro'yxatni sahifalash"""
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(items) + per_page - 1) // per_page
    return items[start:end], total_pages

# Statistika formatlash
def format_stats(total, success, failed):
    """Statistikani formatlash"""
    if total == 0:
        return "Hali xabar yuborilmagan"
    
    success_rate = (success / total) * 100
    return (
        f"📊 Statistika:\n"
        f"Jami: {total}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Muvaffaqiyatsiz: {failed}\n"
        f"📈 Muvaffaqiyat darajasi: {success_rate:.1f}%"
    )

# Guruhlar ro'yxatini groups.json faylidan yuklash
def load_configured_groups():
    """groups.json faylidan guruh ro'yxatini o'qiydi.
    
    Qo'llab-quvvatlanadigan formatlar:
    1. Array of strings: ["https://t.me/group1", "https://t.me/group2"]
    2. Array of objects: [{"link": "...", "name": "..."}, ...]
    3. Object with groups key: {"groups": [...]}
    """
    import json, os
    groups_path = os.path.join(os.path.dirname(__file__), "groups.json")
    if not os.path.exists(groups_path):
        logger.warning("groups.json topilmadi, bo'sh guruh ro'yxati qaytarildi.")
        return []
    try:
        with open(groups_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Format 1: Array of strings
            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                return [{'link': link, 'name': link.split('/')[-1]} for link in data]
            
            # Format 2: Array of objects
            elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                return data
            
            # Format 3: Object with 'groups' key
            elif isinstance(data, dict) and 'groups' in data:
                groups = data.get("groups", [])
                # Check if groups is array of strings
                if all(isinstance(item, str) for item in groups):
                    return [{'link': link, 'name': link.split('/')[-1]} for link in groups]
                return groups
            
            logger.warning("groups.json noto'g'ri formatda")
            return []
    except Exception as e:
        logger.error(f"groups.json o'qishda xatolik: {e}")
        return []

# Guruhda a'zolikni tekshirish
async def check_group_membership(user_client, group_link):
    """Shaxsiy akkaunt guruhda a'zo ekanligini tekshiradi.
    
    Args:
        user_client: TelegramClient instance (shaxsiy akkaunt)
        group_link: Guruh linki (https://t.me/... yoki @username)
    
    Returns:
        tuple: (is_member: bool, chat_id: int or None, error: str or None)
    """
    try:
        # Link'dan username yoki invite hash'ni ajratib olish
        if 'joinchat/' in group_link or '+' in group_link:
            # Private group invite link
            logger.warning(f"Private invite link: {group_link} - qo'llab-quvvatlanmaydi")
            return False, None, "Private invite link qo'llab-quvvatlanmaydi"
        
        # Public group: https://t.me/username yoki @username
        username = group_link.replace('https://t.me/', '').replace('@', '').strip()
        
        # Guruhni topish
        try:
            entity = await user_client.get_entity(username)
        except Exception as e:
            logger.error(f"Guruhni topishda xatolik ({username}): {e}")
            return False, None, f"Guruh topilmadi: {str(e)}"
        
        # A'zolikni tekshirish - get_permissions orqali
        try:
            participant = await user_client.get_permissions(entity)
            
            # Agar permissions olinsak, demak a'zomiz
            # is_banned ni to'g'ri tekshirish
            if hasattr(participant, 'is_banned') and participant.is_banned:
                return False, entity.id, "Guruhda ban qilingan"
            
            # Agar participant mavjud bo'lsa va ban bo'lmasa, demak a'zo
            return True, entity.id, None
            
        except Exception as perm_error:
            # Agar permissions olishda xatolik bo'lsa, a'zo emasligimizni anglatadi
            logger.warning(f"Permissions xatolik ({username}): {perm_error}")
            return False, entity.id if 'entity' in locals() else None, "Guruhda a'zo emassiz"
        
    except Exception as e:
        logger.error(f"Guruh a'zoligini tekshirishda xatolik ({group_link}): {e}")
        return False, None, str(e)
