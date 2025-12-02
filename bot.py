import os
from telethon import TelegramClient, events, Button
from telethon.tl.types import Channel, Chat
import config
from database import init_db
from models import User, Group, Message
from telegram_client import telegram_manager
from message_sender import message_sender

from utils import logger, validate_phone, validate_message_text, format_stats, load_configured_groups, check_group_membership
from user_client import start_user_client, send_message_to_chat
import asyncio

# Bot client (global variable, will be initialized in main)
bot = None

# Foydalanuvchi holatlari (conversation state)
user_states = {}

async def start_handler(event):
    """Start buyrug'i"""
    from telethon.tl.types import ReplyKeyboardHide
    
    telegram_id = event.sender_id
    logger.info(f"Start command received from: {telegram_id}")
    
    # Foydalanuvchini yaratish yoki yangilash
    user = User.get_by_telegram_id(telegram_id)
    if not user:
        User.create(telegram_id=telegram_id)
        logger.info(f"Yangi foydalanuvchi yaratildi: {telegram_id}")
    
    welcome_message = (
        f"Xush kelibsiz! Bu bot orqali siz bir nechta guruhga avtomatik xabar yuborishingiz mumkin.\n\n"
        f"Yangi ishlash tartibi:\n"
        f"1. Botni o'z guruhlaringizga qo'shing (admin qilib).\n"
        f"2. Bot avtomatik ravishda guruhni bazaga qo'shadi.\n"
        f"3. /send_message orqali xabar yuboring.\n\n"
        f"Asosiy buyruqlar:\n"
        f"/send_message - Darhol xabar yuborish\n"
        f"/help - Yordam"
    )
    
    # Klaviatura tugmalarini olib tashlash
    await event.respond(welcome_message, buttons=ReplyKeyboardHide())

async def debug_handler(event):
    """Debug handler to log all incoming messages"""
    logger.info(f"Received message: {event.text} from {event.sender_id}")

async def help_handler(event):
    """Yordam"""
    telegram_id = event.sender_id
    if not config.is_user_allowed(telegram_id):
        return
    
    await event.respond(
        "📚 **Yordam**\n\n"
        "**1. Guruh qo'shish:**\n"
        "Botni o'z guruhingizga qo'shing. U avtomatik ravishda ro'yxatga olinadi.\n\n"
        "**2. Xabar yuborish:**\n"
        "/send_message - Xabar matnini kiriting\n"
        "Barcha guruhlarga 5 minut interval bilan yuboriladi\n\n"
        "**3. Tarix va statistika:**\n"
        "/history - Yuborilgan xabarlar\n"
        "/stats - Muvaffaqiyatli/muvaffaqiyatsiz xabarlar\n\n"
        "Savollar bo'lsa, admin bilan bog'laning."
    )

async def add_group_handler(event):
    """Guruh qo'shish bo'yicha qo'llanma"""
    await event.respond(
        "ℹ️ **Guruh qo'shish uchun:**\n\n"
        "1. Telegramda guruhingizga kiring.\n"
        "2. Guruh sozlamalariga o'tib, **'Add Member'** (Qatnashchi qo'shish) ni bosing.\n"
        "3. Botni qidirib toping (@bot_username) va guruhga qo'shing.\n"
        "4. Botni **Admin** qilib tayinlang.\n\n"
        "Shunda bot avtomatik ravishda guruhni o'z ro'yxatiga qo'shadi.\n"
        "Tekshirish uchun: /list_groups"
    )

async def group_action_handler(event):
    """Guruhga qo'shilganda yoki chiqarilganda"""
    if event.user_added or event.user_joined:
        # Agar bot qo'shilgan bo'lsa
        me = await event.client.get_me()
        if event.user_id == me.id:
            chat = await event.get_chat()
            logger.info(f"Bot guruhga qo'shildi: {chat.title} ({chat.id})")
            
            # Kim qo'shganini aniqlash
            adder_id = None
            if event.added_by:
                adder_id = event.added_by.id
            elif event.action_message:
                adder_id = event.action_message.from_id.user_id if event.action_message.from_id else None
            
            if not adder_id:
                logger.warning("Botni kim qo'shgani aniqlanmadi.")
                # Fallback: use first allowed user as owner of the group
                if config.ALLOWED_USER_IDS:
                    adder_id = config.ALLOWED_USER_IDS[0]
                else:
                    await event.respond("⚠️ Bot guruhga qo'shildi, lekin kim qo'shganini aniqlay olmadim. Iltimos, botga /start bosing va qaytadan urinib ko'ring.")
                    return

            # Userni bazadan olish
            user = User.get_by_telegram_id(adder_id)
            if not user:
                # Agar user bazada bo'lmasa, demak u /start bosmagan
                # Lekin agar u ALLOWED_USER_IDS da bo'lsa, avtomatik yaratamiz
                if config.is_user_allowed(adder_id):
                    User.create(telegram_id=adder_id)
                    user = User.get_by_telegram_id(adder_id)
                else:
                    await event.respond(f"❌ Siz ({adder_id}) botdan foydalanish huquqiga ega emassiz.")
                    await event.client.kick_participant(chat.id, 'me') # Bot guruhdan chiqib ketadi
                    return

            # Allaqachon bormi?
            existing_groups = Group.get_by_user_id(user['id'], active_only=False)
            existing = None
            for g in existing_groups:
                if g['group_id'] == chat.id:
                    existing = g
                    break
            
            if existing:
                Group.update(existing['id'], is_active=True, group_name=chat.title)
            else:
                Group.create(
                    user_id=user['id'],
                    group_id=chat.id,
                    group_name=chat.title,
                    group_username=getattr(chat, 'username', None)
                )
            
            await event.respond(f"✅ Guruh muvaffaqiyatli qo'shildi!\nEga: {adder_id}")

async def list_groups_handler(event):
    """Guruhlar ro'yxati"""
    telegram_id = event.sender_id
    
    user = User.get_by_telegram_id(telegram_id)
    if not user:
        # Avtomatik yaratish
        User.create(telegram_id=telegram_id)
        user = User.get_by_telegram_id(telegram_id)
    
    groups = Group.get_by_user_id(user['id'], active_only=True)
    
    if not groups:
        await event.respond("❌ Guruhlar yo'q. Botni guruhlaringizga qo'shing.")
        return
    
    text = "📋 **Sizning guruhlaringiz:**\n\n"
    for i, group in enumerate(groups, 1):
        text += f"{i}. {group['group_name']} (ID: {group['id']})\n"
    
    await event.respond(text)

async def remove_group_handler(event):
    """Guruh o'chirish"""
    telegram_id = event.sender_id
    
    user = User.get_by_telegram_id(telegram_id)
    if not user:
        await event.respond("❌ Foydalanuvchi topilmadi.")
        return
    
    groups = Group.get_by_user_id(user['id'], active_only=True)
    
    if not groups:
        await event.respond("❌ Guruhlar yo'q.")
        return
    
    # Inline tugmalar
    buttons = []
    for group in groups:
        buttons.append([Button.inline(
            f"🗑 {group['group_name'][:30]}",
            data=f"remove_group:{group['id']}"
        )])
    
    await event.respond(
        "O'chirmoqchi bo'lgan guruhni tanlang:",
        buttons=buttons
    )

async def remove_group_callback(event):
    """Guruh o'chirish callback"""
    telegram_id = event.sender_id
    data = event.data.decode('utf-8')
    _, group_id = data.split(':')
    group_id = int(group_id)
    
    user = User.get_by_telegram_id(telegram_id)
    group = Group.get_by_id(group_id)
    
    if group and group['user_id'] == user['id']:
        Group.update(group_id, is_active=False)
        group_name = group['group_name']
        await event.answer("✅ Guruh o'chirildi!")
        await event.respond(f"✅ Guruh o'chirildi: {group_name}")
    else:
        await event.answer("❌ Guruh topilmadi")

async def send_message_handler(event):
    """Darhol xabar yuborish"""
    telegram_id = event.sender_id
    
    # Foydalanuvchini tekshirish
    user = User.get_by_telegram_id(telegram_id)
    if not user:
        User.create(telegram_id=telegram_id)
        user = User.get_by_telegram_id(telegram_id)
    
    groups = Group.get_by_user_id(user['id'], active_only=True)
    cfg_groups = load_configured_groups()
    
    if not groups and not cfg_groups:
        await event.respond("❌ Guruhlar yo'q. Botni guruhlaringizga qo'shing yoki groups.json faylini tekshiring.")
        return
    
    await event.respond(
        "📝 Yubormoqchi bo'lgan xabar matnini kiriting:\n"
        "(Emoji va formatlash ishlatishingiz mumkin)"
    )
    user_states[telegram_id] = {'state': 'waiting_message_text'}

async def history_handler(event):
    """Yuborilgan xabarlar tarixi"""
    telegram_id = event.sender_id
    
    user = User.get_by_telegram_id(telegram_id)
    if not user:
        await event.respond("❌ Foydalanuvchi topilmadi.")
        return
    
    messages = Message.get_by_user_id(user['id'], limit=20)
    
    if not messages:
        await event.respond("❌ Hali xabar yuborilmagan.")
        return
    
    text = "📜 **Yuborilgan xabarlar (oxirgi 20 ta):**\n\n"
    for msg in messages:
        group = Group.get_by_id(msg['group_id'])
        status_icon = "✅" if msg['status'] == 'success' else "❌"
        
        sent_at = msg['sent_at']
        if isinstance(sent_at, str):
            from datetime import datetime
            sent_at = datetime.fromisoformat(sent_at)
        
        text += (
            f"{status_icon} {group['group_name'] if group else 'Unknown'}\n"
            f"   Vaqt: {sent_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"   Matn: {msg['message_text'][:30]}...\n"
        )
        if msg.get('error_message'):
            text += f"   Xatolik: {msg['error_message'][:50]}\n"
        text += "\n"
    
    await event.respond(text)

async def stats_handler(event):
    """Statistika"""
    telegram_id = event.sender_id
    
    user = User.get_by_telegram_id(telegram_id)
    if not user:
        await event.respond("❌ Foydalanuvchi topilmadi.")
        return
    
    stats = Message.get_stats(user['id'])
    stats_text = format_stats(stats['total'], stats['success'], stats['failed'])
    await event.respond(stats_text)

async def send_type_callback(event):
    """Xabar yuborish turini tanlash callback"""
    telegram_id = event.sender_id
    data = event.data.decode('utf-8')
    
    # Xabarni o'chirish (tugmalarni)
    await event.delete()
    
    # Holatni tekshirish
    state_data = user_states.get(telegram_id)
    if not state_data or state_data.get('state') != 'waiting_send_type_callback':
        await event.respond("❌ Sessiya eskirgan. Qaytadan /send_message buyrug'ini bering.")
        return
    
    message_text = state_data.get('message_text')
    
    if data == 'send_once':
        # Bir martalik yuborish
        await event.respond(
            f"⏳ Xabar yuborilmoqda...\n"
            f"Guruhlar orasida {config.MESSAGE_INTERVAL_MINUTES} minut interval bo'ladi."
        )
        
        # Foydalanuvchini olish
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            User.create(telegram_id=telegram_id)
            user = User.get_by_telegram_id(telegram_id)
        
        # Guruhlar ro'yxatini groups.json dan olish va a'zolikni tekshirish
        cfg_groups = load_configured_groups()
        if not cfg_groups:
            await event.respond("❌ groups.json faylida guruhlar topilmadi.")
            user_states.pop(telegram_id, None)
            return
        
        await event.respond(f"🔍 {len(cfg_groups)} ta guruhda a'zolik tekshirilmoqda...")
        
        # User client'ni olish
        import user_client as uc_module
        
        # Faqat a'zo bo'lgan guruhlarni filtrlash
        verified_groups = []
        for g in cfg_groups:
            group_link = g.get('link')
            group_name = g.get('name', 'Unnamed')
            
            if not group_link:
                logger.warning(f"Guruh '{group_name}' uchun link topilmadi")
                continue
            
            is_member, chat_id, error = await check_group_membership(uc_module.user_client, group_link)
            
            if is_member and chat_id:
                verified_groups.append({
                    'group_id': chat_id,
                    'group_name': group_name,
                    'link': group_link
                })
                logger.info(f"✅ A'zo: {group_name} (ID: {chat_id})")
                
                # Guruhni bazaga saqlash (agar yo'q bo'lsa)
                existing_groups = Group.get_by_user_id(user['id'], active_only=False)
                existing = None
                for g in existing_groups:
                    if g['group_id'] == chat_id:
                        existing = g
                        break
                
                if existing:
                    if not existing['is_active']:
                        Group.update(existing['id'], is_active=True, group_name=group_name)
                else:
                    Group.create(
                        user_id=user['id'],
                        group_id=chat_id,
                        group_name=group_name,
                        group_username=group_link.split('/')[-1] if 't.me/' in group_link else None
                    )
            else:
                logger.warning(f"❌ A'zo emas: {group_name} - {error}")
        
        if not verified_groups:
            await event.respond(
                "❌ Siz hech bir guruhda a'zo emassiz!\n\n"
                "groups.json faylidagi guruhlarga qo'shiling va qaytadan urinib ko'ring."
            )
            user_states.pop(telegram_id, None)
            return
        
        await event.respond(f"✅ {len(verified_groups)} ta guruhda a'zosiz. Xabar yuborilmoqda...")

        total = len(verified_groups)
        success = 0
        failed = 0
        details = []
        
        for g in verified_groups:
            ok, err = await send_message_to_chat(g['group_id'], message_text)
            if ok:
                success += 1
                details.append(f"✅ {g.get('group_name', 'Unnamed')}")
            else:
                failed += 1
                details.append(f"❌ {g.get('group_name', 'Unnamed')}: {err}")
        
        summary = (
            f"✅ Yuborish tugadi!\n\n"
            f"Jami guruhlar: {total}\n"
            f"Muvaffaqiyatli: {success}\n"
            f"Muvaffaqiyatsiz: {failed}\n\n"
            f"Batafsil:\n" + "\n".join(details[:10])
        )
        await event.respond(summary)
        user_states.pop(telegram_id, None)

# Oddiy xabarlarni qayta ishlash (conversation state)
async def message_handler(event):
    """Oddiy xabarlarni qayta ishlash"""
    if event.message.text.startswith('/'):
        return  # Buyruqlarni o'tkazib yuborish
    
    telegram_id = event.sender_id
    state = user_states.get(telegram_id, {}).get('state')
    
    if state == 'waiting_message_text':
        # Xabar matnini tekshirish
        valid, result = validate_message_text(event.message.text)
        if not valid:
            await event.respond(f"❌ {result}")
            return
        
        message_text = result
        # Xabarni saqlab, tanlash holatiga o'tish
        user_states[telegram_id] = {
            'state': 'waiting_send_type_callback',
            'message_text': message_text
        }
        
        from telethon import Button
        
        buttons = [
            [Button.inline("🚀 Yuborish", data=b'send_once')]
        ]
        
        await event.respond(
            "🔄 **Xabarni yuborishni tasdiqlaysizmi?**",
            buttons=buttons
        )
        return

async def main():
    """Asosiy funksiya"""
    global bot
    
    logger.info("Bot ishga tushirilmoqda...")
    
    # Bot clientni yaratish
    bot = TelegramClient('bot', config.API_ID, config.API_HASH)
    await bot.start(bot_token=config.BOT_TOKEN)
    
    # Bot buyruqlarini o'rnatish (Menu)
    from telethon.tl.functions.bots import SetBotCommandsRequest
    from telethon.tl.types import BotCommand, BotCommandScopeDefault
    
    commands = [
        BotCommand(command='start', description='Botni ishga tushirish'),
        BotCommand(command='help', description='Yordam'),
        BotCommand(command='send_message', description='Xabar yuborish'),
    ]
    
    await bot(SetBotCommandsRequest(
        scope=BotCommandScopeDefault(),
        lang_code='',
        commands=commands
    ))
    logger.info("Bot commands o'rnatildi")
    
    await start_user_client()
    
    # Bot clientni managerga berish
    telegram_manager.set_bot(bot)
    
    # Ma'lumotlar bazasini yaratish
    init_db()
    
    # Ma'lumotlar bazasini yaratish

    
    logger.info("Bot ishga tushdi!")
    
    # Event handlerlarni qayta ro'yxatdan o'tkazish
    setup_handlers()
    
    try:
        await bot.run_until_disconnected()
    finally:
        # Graceful shutdown – bot va user client sessiyalarini yopish
        try:
            await bot.disconnect()
        except Exception as e:
            logger.error(f"Bot disconnect xatolik: {e}")
        try:
            from user_client import user_client
            await user_client.disconnect()
        except Exception as e:
            logger.error(f"User client disconnect xatolik: {e}")


def setup_handlers():
    """Event handlerlarni sozlash"""
    logger.info("Setting up event handlers...")
    
    # Debug handler (log all incoming messages)
    bot.add_event_handler(debug_handler, events.NewMessage)
    
    # Chat action handler (guruhga qo'shilish)
    bot.add_event_handler(group_action_handler, events.ChatAction)
    
    bot.add_event_handler(start_handler, events.NewMessage(pattern='/start'))
    bot.add_event_handler(help_handler, events.NewMessage(pattern='/help'))
    bot.add_event_handler(add_group_handler, events.NewMessage(pattern='/add_group'))
    bot.add_event_handler(list_groups_handler, events.NewMessage(pattern='/list_groups'))
    bot.add_event_handler(remove_group_handler, events.NewMessage(pattern='/remove_group'))
    bot.add_event_handler(remove_group_callback, events.CallbackQuery(pattern=b'remove_group:'))
    bot.add_event_handler(send_message_handler, events.NewMessage(pattern='/send_message'))
    bot.add_event_handler(history_handler, events.NewMessage(pattern='/history'))
    bot.add_event_handler(stats_handler, events.NewMessage(pattern='/stats'))
    
    # Callback handlers
    bot.add_event_handler(send_type_callback, events.CallbackQuery(pattern=b'send_once'))
    
    # Note: message_handler is also a NewMessage handler. Telethon executes handlers in order.
    # If debug_handler is first, it runs first.
    # message_handler should be last as it is a catch-all for text (except commands if checked)
    bot.add_event_handler(message_handler, events.NewMessage)

if __name__ == '__main__':
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Bot to'xtatilmoqda...")
        # Bot va user client sessiyalarini yopish (agar hali yopilmagan bo'lsa)
        try:
            asyncio.run(bot.disconnect())
        except Exception as e:
            logger.error(f"Bot disconnect xatolik: {e}")
        try:
            from user_client import user_client
            asyncio.run(user_client.disconnect())
        except Exception as e:
            logger.error(f"User client disconnect xatolik: {e}")
    except Exception as e:
        logger.error(f"Kritik xatolik: {str(e)}", exc_info=True)
