import asyncio
from datetime import datetime
from models import User, Group, Message
from telegram_client import telegram_manager
from utils import logger
import config

class MessageSender:
    """Xabar yuborish tizimi"""
    
    async def send_to_multiple_groups(self, telegram_id, message_text, group_ids=None):
        """Bir nechta guruhga xabar yuborish"""
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
        
        # Guruhlarni olish
        if group_ids:
            groups = [Group.get_by_id(gid) for gid in group_ids if Group.get_by_id(gid)]
            groups = [g for g in groups if g and g['is_active']]
        else:
            groups = Group.get_by_user_id(user['id'], active_only=True)
        
        if not groups:
            return None, "Guruhlar topilmadi. Botni guruhlaringizga qo'shing."
        
        results['total'] = len(groups)
        
        # Har bir guruhga yuborish
        for i, group in enumerate(groups):
            try:
                # Xabar yuborish
                success, error = await telegram_manager.send_message_to_group(
                    telegram_id,
                    group['group_id'],
                    message_text
                )
                
                if success:
                    results['success'] += 1
                    status = 'success'
                    error_msg = None
                    results['details'].append(f"✅ {group['group_name']}")
                else:
                    results['failed'] += 1
                    status = 'failed'
                    error_msg = error
                    results['details'].append(f"❌ {group['group_name']}: {error}")
                
                # Tarixga saqlash
                Message.create(
                    user_id=user['id'],
                    group_id=group['id'],
                    message_text=message_text,
                    status=status,
                    error_message=error_msg
                )
                
                # Interval (oxirgi guruhdan tashqari)
                if i < len(groups) - 1:
                    wait_seconds = config.MESSAGE_INTERVAL_MINUTES * 60
                    logger.info(f"Keyingi guruhgacha {config.MESSAGE_INTERVAL_MINUTES} minut kutilmoqda...")
                    await asyncio.sleep(wait_seconds)
            
            except Exception as e:
                logger.error(f"Guruhga yuborishda xatolik {group['group_name']}: {str(e)}")
                results['failed'] += 1
                results['details'].append(f"❌ {group['group_name']}: {str(e)}")
                
                # Xatolikni saqlash
                Message.create(
                    user_id=user['id'],
                    group_id=group['id'],
                    message_text=message_text,
                    status='failed',
                    error_message=str(e)
                )
        
        return results, None
    
    async def send_immediate(self, telegram_id, message_text, group_ids=None):
        """Darhol xabar yuborish"""
        logger.info(f"Darhol xabar yuborilmoqda: {telegram_id}")
        return await self.send_to_multiple_groups(telegram_id, message_text, group_ids)

# Global message sender
message_sender = MessageSender()
