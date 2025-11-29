from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from models import User, ScheduledTask
from message_sender import message_sender
from utils import logger
import uuid

class TaskScheduler:
    """Vazifalarni rejalashtirish tizimi"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("Scheduler ishga tushirildi")
    
    async def add_scheduled_task(self, telegram_id, message_text, interval_hours):
        """Rejalashtirilgan vazifa qo'shish"""
        try:
            # Foydalanuvchini topish
            user = User.get_by_telegram_id(telegram_id)
            if not user:
                return False, "Avval ro'yxatdan o'ting: /register"
            
            # Keyingi yuborish vaqti
            next_run = datetime.utcnow() + timedelta(hours=interval_hours)
            
            # Job ID yaratish
            job_id = f"task_{user['id']}_{uuid.uuid4().hex[:8]}"
            
            # Ma'lumotlar bazasiga saqlash
            task = ScheduledTask.create(
                user_id=user['id'],
                message_text=message_text,
                interval_hours=interval_hours,
                next_run=next_run,
                job_id=job_id
            )
            task_id = task['id']
            
            # Scheduler ga qo'shish
            self.scheduler.add_job(
                self._execute_scheduled_task,
                trigger=IntervalTrigger(hours=interval_hours),
                args=[task_id],
                id=job_id,
                next_run_time=next_run,
                replace_existing=True
            )
            
            logger.info(f"Rejalashtirilgan vazifa qo'shildi: {job_id}")
            return True, f"✅ Vazifa rejalashtirildi! Keyingi yuborish: {next_run.strftime('%Y-%m-%d %H:%M')} UTC"
        
        except Exception as e:
            logger.error(f"Vazifa qo'shishda xatolik: {str(e)}")
            return False, f"Xatolik: {str(e)}"
    
    async def _execute_scheduled_task(self, task_id):
        """Rejalashtirilgan vazifani bajarish"""
        try:
            task = ScheduledTask.get_by_id(task_id)
            if not task or not task['is_active']:
                logger.warning(f"Vazifa topilmadi yoki faol emas: {task_id}")
                return
            
            user = User.get_by_telegram_id(task['user_id'])
            if not user:
                logger.warning(f"Foydalanuvchi topilmadi: {task['user_id']}")
                return
            
            # Xabar yuborish
            logger.info(f"Rejalashtirilgan vazifa bajarilmoqda: {task['job_id']}")
            results, error = await message_sender.send_to_multiple_groups(
                user['telegram_id'],
                task['message_text']
            )
            
            # Oxirgi yuborish vaqtini yangilash
            next_run = datetime.utcnow() + timedelta(hours=task['interval_hours'])
            ScheduledTask.update(
                task_id,
                last_run=datetime.utcnow(),
                next_run=next_run
            )
            
            if results:
                logger.info(f"Rejalashtirilgan xabar yuborildi: {results['success']}/{results['total']}")
        
        except Exception as e:
            logger.error(f"Rejalashtirilgan vazifani bajarishda xatolik: {str(e)}")
    
    async def get_user_tasks(self, telegram_id):
        """Foydalanuvchi vazifalarini olish"""
        try:
            user = User.get_by_telegram_id(telegram_id)
            if not user:
                return None, "Avval ro'yxatdan o'ting"
            
            tasks = ScheduledTask.get_by_user_id(user['id'], active_only=True)
            return tasks, None
        
        except Exception as e:
            logger.error(f"Vazifalarni olishda xatolik: {str(e)}")
            return None, str(e)
    
    async def cancel_task(self, telegram_id, task_id):
        """Vazifani bekor qilish"""
        try:
            user = User.get_by_telegram_id(telegram_id)
            if not user:
                return False, "Avval ro'yxatdan o'ting"
            
            task = ScheduledTask.get_by_id(task_id)
            if not task or task['user_id'] != user['id']:
                return False, "Vazifa topilmadi"
            
            # Scheduler dan o'chirish
            if task['job_id'] and self.scheduler.get_job(task['job_id']):
                self.scheduler.remove_job(task['job_id'])
            
            # Ma'lumotlar bazasida faolsizlantirish
            ScheduledTask.update(task_id, is_active=False)
            
            logger.info(f"Vazifa bekor qilindi: {task['job_id']}")
            return True, "✅ Vazifa bekor qilindi"
        
        except Exception as e:
            logger.error(f"Vazifani bekor qilishda xatolik: {str(e)}")
            return False, f"Xatolik: {str(e)}"
    
    async def load_existing_tasks(self):
        """Mavjud vazifalarni yuklash (restart da)"""
        try:
            tasks = ScheduledTask.get_all_active()
            
            for task in tasks:
                # Eski vazifalarni yangilash
                next_run_str = task['next_run']
                if isinstance(next_run_str, str):
                    next_run = datetime.fromisoformat(next_run_str)
                else:
                    next_run = next_run_str
                
                if next_run < datetime.utcnow():
                    next_run = datetime.utcnow() + timedelta(hours=task['interval_hours'])
                    ScheduledTask.update(task['id'], next_run=next_run)
                
                # Scheduler ga qo'shish
                self.scheduler.add_job(
                    self._execute_scheduled_task,
                    trigger=IntervalTrigger(hours=task['interval_hours']),
                    args=[task['id']],
                    id=task['job_id'],
                    next_run_time=next_run,
                    replace_existing=True
                )
            
            logger.info(f"{len(tasks)} ta vazifa yuklandi")
        
        except Exception as e:
            logger.error(f"Vazifalarni yuklashda xatolik: {str(e)}")
    
    def shutdown(self):
        """Scheduler ni to'xtatish"""
        self.scheduler.shutdown()
        logger.info("Scheduler to'xtatildi")

# Global scheduler
task_scheduler = TaskScheduler()
