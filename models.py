from datetime import datetime
from database import get_db, JSONDatabase

class User:
    """Foydalanuvchilar"""
    
    @staticmethod
    def create(telegram_id, phone=None, session_string=None):
        """Yangi foydalanuvchi yaratish"""
        with get_db() as db:
            user_id = JSONDatabase.get_next_id('users')
            user = {
                'id': user_id,
                'telegram_id': telegram_id,
                'phone': phone,
                'session_string': session_string,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            db['users'].append(user)
            return user
    
    @staticmethod
    def get_by_telegram_id(telegram_id):
        """Telegram ID bo'yicha foydalanuvchini topish"""
        with get_db() as db:
            for user in db['users']:
                if user['telegram_id'] == telegram_id:
                    return user
        return None
    
    @staticmethod
    def update(telegram_id, **kwargs):
        """Foydalanuvchini yangilash"""
        with get_db() as db:
            for user in db['users']:
                if user['telegram_id'] == telegram_id:
                    user.update(kwargs)
                    user['updated_at'] = datetime.utcnow().isoformat()
                    return user
        return None


class Group:
    """Guruhlar"""
    
    @staticmethod
    def create(user_id, group_id, group_name, group_username=None):
        """Yangi guruh yaratish"""
        with get_db() as db:
            group_obj_id = JSONDatabase.get_next_id('groups')
            group = {
                'id': group_obj_id,
                'user_id': user_id,
                'group_id': group_id,
                'group_name': group_name,
                'group_username': group_username,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            db['groups'].append(group)
            return group
    
    @staticmethod
    def get_by_user_id(user_id, active_only=True):
        """Foydalanuvchi guruhlari"""
        with get_db() as db:
            groups = []
            for group in db['groups']:
                if group['user_id'] == user_id:
                    if not active_only or group['is_active']:
                        groups.append(group)
            return groups
    
    @staticmethod
    def get_by_id(group_id):
        """ID bo'yicha guruhni topish"""
        with get_db() as db:
            for group in db['groups']:
                if group['id'] == group_id:
                    return group
        return None
    
    @staticmethod
    def update(group_id, **kwargs):
        """Guruhni yangilash"""
        with get_db() as db:
            for group in db['groups']:
                if group['id'] == group_id:
                    group.update(kwargs)
                    return group
        return None


class Message:
    """Yuborilgan xabarlar tarixi"""
    
    @staticmethod
    def create(user_id, group_id, message_text, status, error_message=None):
        """Yangi xabar yaratish"""
        with get_db() as db:
            message_id = JSONDatabase.get_next_id('messages')
            message = {
                'id': message_id,
                'user_id': user_id,
                'group_id': group_id,
                'message_text': message_text,
                'status': status,
                'error_message': error_message,
                'sent_at': datetime.utcnow().isoformat()
            }
            db['messages'].append(message)
            return message
    
    @staticmethod
    def get_by_user_id(user_id, limit=20):
        """Foydalanuvchi xabarlari"""
        with get_db() as db:
            messages = []
            for message in db['messages']:
                if message['user_id'] == user_id:
                    messages.append(message)
            # Oxirgi xabarlar birinchi
            messages.sort(key=lambda x: x['sent_at'], reverse=True)
            return messages[:limit]
    
    @staticmethod
    def get_stats(user_id):
        """Statistika"""
        with get_db() as db:
            total = 0
            success = 0
            failed = 0
            for message in db['messages']:
                if message['user_id'] == user_id:
                    total += 1
                    if message['status'] == 'success':
                        success += 1
                    else:
                        failed += 1
            return {'total': total, 'success': success, 'failed': failed}


class ScheduledTask:
    """Rejalashtirilgan vazifalar"""
    
    @staticmethod
    def create(user_id, message_text, interval_hours, next_run, job_id):
        """Yangi vazifa yaratish"""
        with get_db() as db:
            task_id = JSONDatabase.get_next_id('scheduled_tasks')
            task = {
                'id': task_id,
                'user_id': user_id,
                'message_text': message_text,
                'interval_hours': interval_hours,
                'is_active': True,
                'next_run': next_run.isoformat() if hasattr(next_run, 'isoformat') else next_run,
                'last_run': None,
                'created_at': datetime.utcnow().isoformat(),
                'job_id': job_id
            }
            db['scheduled_tasks'].append(task)
            return task
    
    @staticmethod
    def get_by_id(task_id):
        """ID bo'yicha vazifani topish"""
        with get_db() as db:
            for task in db['scheduled_tasks']:
                if task['id'] == task_id:
                    return task
        return None
    
    @staticmethod
    def get_by_user_id(user_id, active_only=True):
        """Foydalanuvchi vazifalari"""
        with get_db() as db:
            tasks = []
            for task in db['scheduled_tasks']:
                if task['user_id'] == user_id:
                    if not active_only or task['is_active']:
                        tasks.append(task)
            return tasks
    
    @staticmethod
    def get_all_active():
        """Barcha faol vazifalar"""
        with get_db() as db:
            tasks = []
            for task in db['scheduled_tasks']:
                if task['is_active']:
                    tasks.append(task)
            return tasks
    
    @staticmethod
    def update(task_id, **kwargs):
        """Vazifani yangilash"""
        with get_db() as db:
            for task in db['scheduled_tasks']:
                if task['id'] == task_id:
                    # datetime ni string ga aylantirish
                    for key, value in kwargs.items():
                        if hasattr(value, 'isoformat'):
                            kwargs[key] = value.isoformat()
                    task.update(kwargs)
                    return task
        return None
