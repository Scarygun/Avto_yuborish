import os
import config
from telethon import TelegramClient
from utils import logger

# User session file (will be created on first run)
SESSION_FILE = os.path.join(os.path.dirname(__file__), "user.session")

# Global client instance (lazy initialization)
user_client = None

async def start_user_client():
    """Start the user client.
    The first run will ask for the phone number and the login code.
    Subsequent runs reuse the saved session file.
    """
    global user_client
    
    if user_client is None:
        user_client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
    
    await user_client.start(phone=config.USER_PHONE)
    logger.info("User client started (personal account)")
    return user_client

async def send_message_to_chat(chat_id: int, text: str):
    """Send a message to a chat (group, channel, or private) using the personal account.
    Returns (True, "msg") on success, (False, error) on failure.
    """
    global user_client
    
    if user_client is None:
        raise RuntimeError("User client not started. Call start_user_client() first.")
    
    try:
        # Chat nomini olish (log uchun)
        try:
            entity = await user_client.get_entity(chat_id)
            title = getattr(entity, 'title', getattr(entity, 'username', str(chat_id)))
        except:
            title = str(chat_id)

        await user_client.send_message(chat_id, text)
        logger.info(f"Message sent to '{title}' ({chat_id}) via user client")
        return True, "Message sent"
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return False, str(e)
