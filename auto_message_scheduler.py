import asyncio
from datetime import datetime, timedelta
from utils import logger, load_configured_groups, check_group_membership
import user_client as uc_module
import json
import os

class AutoMessageScheduler:
    """Avtomatik xabar yuborish tizimi"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'auto_message.json')
        self.is_running = False
        self.task = None
    
    def load_config(self):
        """auto_message.json dan konfiguratsiyani yuklash"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning("auto_message.json topilmadi")
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            logger.error(f"auto_message.json o'qishda xatolik: {e}")
            return None
    
    async def send_auto_message(self):
        """Avtomatik xabar yuborish"""
        try:
            config = self.load_config()
            if not config or not config.get('enabled', False):
                logger.info("Avtomatik xabar o'chirilgan")
                return
            
            message_text = config.get('message', '')
            if not message_text:
                logger.warning("Xabar matni bo'sh")
                return
            
            # Guruhlarni yuklash va a'zolikni tekshirish
            cfg_groups = load_configured_groups()
            if not cfg_groups:
                logger.warning("groups.json da guruhlar yo'q")
                return
            
            logger.info(f"🔍 {len(cfg_groups)} ta guruhda a'zolik tekshirilmoqda...")
            
            # Faqat a'zo bo'lgan guruhlarni filtrlash
            verified_groups = []
            for g in cfg_groups:
                group_link = g.get('link')
                group_name = g.get('name', 'Unnamed')
                
                if not group_link:
                    continue
                
                is_member, chat_id, error = await check_group_membership(uc_module.user_client, group_link)
                
                if is_member and chat_id:
                    verified_groups.append({
                        'group_id': chat_id,
                        'group_name': group_name,
                        'link': group_link
                    })
                    logger.info(f"✅ A'zo: {group_name} (ID: {chat_id})")
            
            if not verified_groups:
                logger.warning("Hech bir guruhda a'zo emas")
                return
            
            logger.info(f"📤 {len(verified_groups)} ta guruhga xabar yuborilmoqda...")
            
            # Xabar yuborish
            success = 0
            failed = 0
            for g in verified_groups:
                ok, err = await uc_module.send_message_to_chat(g['group_id'], message_text)
                if ok:
                    success += 1
                    logger.info(f"✅ Yuborildi: {g['group_name']}")
                else:
                    failed += 1
                    logger.error(f"❌ Xatolik: {g['group_name']} - {err}")
            
            logger.info(f"✅ Avtomatik xabar yuborish tugadi. Muvaffaqiyatli: {success}, Xatolik: {failed}")
            
        except Exception as e:
            logger.error(f"Avtomatik xabar yuborishda xatolik: {e}", exc_info=True)
    
    async def run_scheduler(self):
        """Scheduler'ni ishga tushirish"""
        logger.info("🤖 Avtomatik xabar yuborish tizimi ishga tushdi")
        
        while self.is_running:
            try:
                config = self.load_config()
                if not config or not config.get('enabled', False):
                    logger.info("Avtomatik xabar o'chirilgan, 5 daqiqa kutilmoqda...")
                    await asyncio.sleep(300)  # 5 minut kutish
                    continue
                
                interval_minutes = config.get('interval_minutes', 60)
                
                # Xabar yuborish
                await self.send_auto_message()
                
                # Keyingi yuborishgacha kutish
                wait_seconds = interval_minutes * 60
                next_run = datetime.now() + timedelta(seconds=wait_seconds)
                logger.info(f"⏰ Keyingi xabar: {next_run.strftime('%Y-%m-%d %H:%M:%S')} ({interval_minutes} daqiqadan keyin)")
                
                await asyncio.sleep(wait_seconds)
                
            except Exception as e:
                logger.error(f"Scheduler xatolik: {e}", exc_info=True)
                await asyncio.sleep(60)  # 1 minut kutish
    
    async def start(self):
        """Scheduler'ni boshlash"""
        if self.is_running:
            logger.warning("Scheduler allaqachon ishlayapti")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self.run_scheduler())
        logger.info("✅ Avtomatik xabar yuborish boshlandi")
    
    async def stop(self):
        """Scheduler'ni to'xtatish"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Avtomatik xabar yuborish to'xtatildi")

# Global instance
auto_scheduler = AutoMessageScheduler()
