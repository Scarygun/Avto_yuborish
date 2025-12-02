import asyncio
from datetime import datetime
from models import User, Group, Message
from telegram_client import telegram_manager
from utils import logger, load_configured_groups, check_group_membership
import user_client as uc_module
import config

class MessageSender:
    """Xabar yuborish tizimi"""
    
    async def send_to_multiple_groups(self, telegram_id, message_text, group_ids=None):
        """Bir nechta guruhga xabar yuborish (groups.json bilan sinxronizatsiya)"""
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        # Foydalanuvchini tekshirish (avtomatik yaratish)
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            User.create(telegram_id=telegram_id)
            user = User.get_by_telegram_id(telegram_id)
        
        # Guruhlarni groups.json dan yuklash
        cfg_groups = load_configured_groups()
        if not cfg_groups:
            return None, "groups.json faylida guruhlar topilmadi."
            
        logger.info(f"Sinxronizatsiya boshlanmoqda: {len(cfg_groups)} ta guruh")
        
        # Faqat a'zo bo'lgan guruhlarni filtrlash va bazani yangilash
        verified_groups = []
        valid_group_ids = []
        
        for g in cfg_groups:
            group_link = g.get('link')
            group_name = g.get('name', 'Unnamed')
            
            if not group_link:
                continue
            
            # A'zolikni tekshirish
            is_member, chat_id, error = await check_group_membership(uc_module.user_client, group_link)
            
            if is_member and chat_id:
                verified_groups.append({
                    'group_id': chat_id,
                    'group_name': group_name,
                    'link': group_link
                })
                valid_group_ids.append(chat_id)
                
                # Guruhni bazaga saqlash/yangilash
                existing_groups = Group.get_by_user_id(user['id'], active_only=False)
                existing = None
                for eg in existing_groups:
                    if eg['group_id'] == chat_id:
                        existing = eg
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
                logger.warning(f"Guruhga yuborilmaydi (a'zo emas): {group_name} - {error}")

        # Bazadagi ortiqcha guruhlarni o'chirish (deaktivatsiya)
        all_db_groups = Group.get_by_user_id(user['id'], active_only=True)
        for db_group in all_db_groups:
            if db_group['group_id'] not in valid_group_ids:
                logger.info(f"Guruh deaktivatsiya qilindi (json da yo'q): {db_group['group_name']}")
                Group.update(db_group['id'], is_active=False)

        if not verified_groups:
            return None, "Siz hech bir guruhda a'zo emassiz yoki groups.json bo'sh."
        
        results['total'] = len(verified_groups)
        
        # Har bir guruhga yuborish
        for i, group in enumerate(verified_groups):
            try:
                # Xabar yuborish (user client orqali, chunki bot guruhda bo'lmasligi mumkin)
                # Lekin asl kodda telegram_manager ishlatilgan (bot).
                # Agar user_client ishlatilsa, telegram_manager o'rniga user_client.send_message_to_chat ishlatish kerak.
                # Asl kodda telegram_manager.send_message_to_group ishlatilgan.
                # Lekin biz check_group_membership da user_client ni ishlatdik.
                # Agar bot guruhda admin bo'lsa, telegram_manager ishlaydi.
                # Agar user o'zi yuborayotgan bo'lsa, user_client ishlatish kerak.
                # User talabi: "guruh linkini kurish kerak".
                # Bot mode da bot o'zi yuboradi.
                # Lekin groups.json dagi guruhlarga bot a'zo bo'lmasligi mumkin, user a'zo bo'ladi.
                # Shuning uchun user_client orqali yuborish ishonchliroq agar bu userbot bo'lsa.
                # Lekin bu proyekt "Python_Bot" va telegram_client.py da "Bot Mode" deyilgan.
                # Agar bu oddiy bot bo'lsa, u faqat o'zi a'zo bo'lgan guruhlarga yozadi.
                # check_group_membership user_client ni ishlatadi.
                # Demak bu userbot + bot aralashmasi.
                # Hozircha telegram_manager (bot) ni ishlatamiz, agar u ishlamasa user_client ga o'tamiz.
                # Lekin oldingi kodda telegram_manager ishlatilgan.
                
                # FIX: Bot guruhda bo'lishi shart. Agar bot guruhda bo'lmasa, user_client orqali yuborish kerak.
                # Hozirgi kodda telegram_manager ishlatilgan. Keling, xavfsizlik uchun user_client ni ham qo'shamiz
                # yoki telegram_manager qoldiramiz.
                # Userning muammosi: "o'chirilgan linklar".
                # Demak, biz ro'yxatni yangiladik.
                
                # Xabar yuborish (Bot orqali)
                success, error = await telegram_manager.send_message_to_group(
                    telegram_id,
                    group['group_id'],
                    message_text
                )
                
                # Agar bot orqali o'xshamasa va xatolik bo'lsa, user_client ni sinab ko'rish mumkin
                # Lekin hozircha faqat ro'yxatni to'g'irlashga fokus qilamiz.
                
                if success:
                    results['success'] += 1
                    status = 'success'
                    error_msg = None
                    results['details'].append(f"✅ {group['group_name']}")
                else:
                    # Bot yubora olmasa, user client orqali urinib ko'ramiz
                    try:
                        ok, err = await uc_module.send_message_to_chat(group['group_id'], message_text)
                        if ok:
                            success = True
                            results['success'] += 1
                            status = 'success'
                            error_msg = None
                            results['details'].append(f"✅ {group['group_name']} (User)")
                        else:
                            results['failed'] += 1
                            status = 'failed'
                            error_msg = f"Bot: {error}, User: {err}"
                            results['details'].append(f"❌ {group['group_name']}: {error_msg}")
                    except Exception as e:
                        results['failed'] += 1
                        status = 'failed'
                        error_msg = f"{error} | User client error: {str(e)}"
                        results['details'].append(f"❌ {group['group_name']}: {error_msg}")

                # Database dagi guruh ID sini topish (Message log uchun)
                # Bizda group['group_id'] bor (chat_id), lekin DB dagi ID kerak
                db_group = None
                for dbg in Group.get_by_user_id(user['id'], active_only=False):
                    if dbg['group_id'] == group['group_id']:
                        db_group = dbg
                        break
                
                if db_group:
                    Message.create(
                        user_id=user['id'],
                        group_id=db_group['id'],
                        message_text=message_text,
                        status=status,
                        error_message=error_msg
                    )
                
                # Interval (oxirgi guruhdan tashqari)
                if i < len(verified_groups) - 1:
                    wait_seconds = config.MESSAGE_INTERVAL_MINUTES * 60
                    logger.info(f"Keyingi guruhgacha {config.MESSAGE_INTERVAL_MINUTES} minut kutilmoqda...")
                    await asyncio.sleep(wait_seconds)
            
            except Exception as e:
                logger.error(f"Guruhga yuborishda xatolik {group['group_name']}: {str(e)}")
                results['failed'] += 1
                results['details'].append(f"❌ {group['group_name']}: {str(e)}")
        
        return results, None
    
    async def send_immediate(self, telegram_id, message_text, group_ids=None):
        """Darhol xabar yuborish"""
        logger.info(f"Darhol xabar yuborilmoqda: {telegram_id}")
        return await self.send_to_multiple_groups(telegram_id, message_text, group_ids)

# Global message sender
message_sender = MessageSender()
