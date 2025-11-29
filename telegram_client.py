import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
import config
from utils import logger

class TelegramClientManager:
    """Telegram client boshqaruvi (Bot Mode)"""
    
    def __init__(self):
        self.bot = None
    
    def set_bot(self, bot_client):
        """Bot clientini o'rnatish"""
        self.bot = bot_client
    
    async def send_message_to_group(self, telegram_id, group_id, message_text):
        """Guruhga xabar yuborish"""
        try:
            if not self.bot:
                return False, "Bot ishga tushmagan"
            
            # Xabar yuborish
            await self.bot.send_message(group_id, message_text)
            logger.info(f"Xabar yuborildi: {group_id}")
            
            return True, None
        
        except Exception as e:
            logger.error(f"Xabar yuborishda xatolik: {str(e)}")
            return False, str(e)
    
    async def get_group_info(self, group_id):
        """Guruh haqida ma'lumot olish"""
        try:
            if not self.bot:
                return None
            
            entity = await self.bot.get_entity(group_id)
            if isinstance(entity, (Channel, Chat)):
                return {
                    'id': entity.id,
                    'name': entity.title,
                    'username': getattr(entity, 'username', None)
                }
            return None
        except Exception as e:
            logger.error(f"Guruh ma'lumotlarini olishda xatolik: {str(e)}")
            return None

# Global client manager
telegram_manager = TelegramClientManager()
