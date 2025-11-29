# Batafsil Sozlash Qo'llanmasi

## 1. Python O'rnatish

### Python versiyasini tekshirish

```bash
python3 --version
# Python 3.10 yoki yuqori bo'lishi kerak
```

Agar Python o'rnatilmagan bo'lsa:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

## 2. Loyihani Sozlash

### Virtual environment yaratish

```bash
cd /home/scarygun/Desktop/Loyihalar

# venv yaratish
python3 -m venv venv

# Faollashtirish
source venv/bin/activate

# Faollashganini tekshirish (terminal da (venv) ko'rinadi)
which python
```

### Kutubxonalarni o'rnatish

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### O'rnatilgan kutubxonalarni tekshirish

```bash
pip list
```

Quyidagilar ko'rinishi kerak:
- telethon
- apscheduler
- python-dotenv

## 3. Telegram API Credentials

### API ID va API Hash olish

1. **Telegram ga kirish**: https://my.telegram.org
2. **Login**: Telefon raqamingizni kiriting
3. **API development tools**: Menyudan tanlang
4. **Create new application**:
   - App title: `Auto Messaging Bot`
   - Short name: `automsg`
   - Platform: `Other`
5. **Credentials nusxalash**:
   - `api_id` (raqam)
   - `api_hash` (string)

### Bot Token olish

1. **BotFather ochish**: Telegram da [@BotFather](https://t.me/BotFather)
2. **Yangi bot yaratish**: `/newbot`
3. **Bot nomi**: `My Auto Messaging Bot`
4. **Bot username**: `my_automsg_bot` (noyob bo'lishi kerak)
5. **Token nusxalash**: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## 4. Environment Variables Sozlash

### .env fayl yaratish

```bash
cd /home/scarygun/Desktop/Loyihalar
cp .env.example .env
nano .env
```

### .env faylini to'ldirish

```env
# Telegram API (https://my.telegram.org dan)
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

# Bot Token (BotFather dan)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Sozlamalar
MESSAGE_INTERVAL_MINUTES=5
LOG_LEVEL=INFO

# Admin (ixtiyoriy)
ADMIN_USER_ID=123456789
```

**Muhim:**
- `API_ID` - raqam (qo'shtirnoqsiz)
- `API_HASH` - string (qo'shtirnoqsiz)
- `BOT_TOKEN` - to'liq token

### .env faylini saqlash

`Ctrl + O` -> `Enter` -> `Ctrl + X`

## 5. Birinchi Ishga Tushirish

### Botni ishga tushirish

```bash
source venv/bin/activate
python main.py
```

Muvaffaqiyatli bo'lsa:

```
==================================================
Telegram Auto-Messaging Bot
==================================================
INFO - Bot ishga tushirilmoqda...
INFO - JSON ma'lumotlar bazasi yaratildi
INFO - Scheduler ishga tushirildi
INFO - 0 ta vazifa yuklandi
INFO - Bot ishga tushdi!
```

## 6. Botni Test Qilish

### Telegram da botni topish

1. Telegram ni oching
2. Bot username ni qidiring (masalan: `@my_automsg_bot`)
3. `/start` ni bosing

### Ro'yxatdan o'tish

1. `/register` buyrug'ini yuboring
2. Telefon raqamingizni kiriting: `+998901234567`
3. Telegram ga kod keladi
4. Kodni kiriting

### Guruh qo'shish

1. `/add_group` buyrug'ini yuboring
2. Ro'yxatdan guruh tanlang
3. Guruh qo'shiladi

### Test xabar yuborish

1. `/send_message` buyrug'ini yuboring
2. Xabar matnini kiriting: `Test xabar`
3. Xabar yuboriladi

## 7. Background da Ishlatish (Production)

### systemd service yaratish

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Quyidagini kiriting:

```ini
[Unit]
Description=Telegram Auto-Messaging Bot
After=network.target

[Service]
Type=simple
User=scarygun
WorkingDirectory=/home/scarygun/Desktop/Loyihalar
Environment="PATH=/home/scarygun/Desktop/Loyihalar/venv/bin"
ExecStart=/home/scarygun/Desktop/Loyihalar/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Service ni yoqish

```bash
# Reload systemd
sudo systemctl daemon-reload

# Service ni yoqish
sudo systemctl enable telegram-bot

# Ishga tushirish
sudo systemctl start telegram-bot

# Holatini tekshirish
sudo systemctl status telegram-bot

# Loglarni ko'rish
sudo journalctl -u telegram-bot -f
```

### Service ni boshqarish

```bash
# To'xtatish
sudo systemctl stop telegram-bot

# Qayta ishga tushirish
sudo systemctl restart telegram-bot

# O'chirish
sudo systemctl disable telegram-bot
```

## 8. Muammolarni Hal Qilish

### Python import xatoliklari

```bash
# Virtual environment faollashtirilganini tekshirish
which python  # /home/scarygun/Desktop/Loyihalar/venv/bin/python bo'lishi kerak

# Kutubxonalarni qayta o'rnatish
pip install -r requirements.txt --force-reinstall
```

### Telegram API xatoliklari

- API_ID va API_HASH to'g'riligini tekshiring
- Bot token to'g'riligini tekshiring
- Internet ulanishini tekshiring

### Session xatoliklari

```bash
# Session papkasini tozalash
rm -rf sessions/*

# Qayta ro'yxatdan o'tish
# Bot da /register buyrug'ini bajaring
```

### JSON fayl xatoliklari

```bash
# Ma'lumotlar bazasini tozalash
rm database.json

# Botni qayta ishga tushirish
python main.py
```

## 9. Xavfsizlik

### .env faylini himoyalash

```bash
chmod 600 .env
```

### Firewall sozlash (ixtiyoriy)

```bash
# Faqat kerakli portlarni ochish
sudo ufw enable
sudo ufw allow ssh
```

## 10. Backup

### Ma'lumotlar bazasi backup

```bash
# Backup yaratish
cp database.json backup_$(date +%Y%m%d).json

# Restore qilish
cp backup_20251129.json database.json
```

### Avtomatik backup (cron)

```bash
crontab -e
```

Quyidagini qo'shing:

```
0 2 * * * cp /home/scarygun/Desktop/Loyihalar/database.json /home/scarygun/backups/database_$(date +\%Y\%m\%d).json
```

Har kuni soat 2:00 da backup yaratadi.

## Tayyor!

Bot endi to'liq ishga tayyor. JSON fayl bilan ishlaydi - PostgreSQL o'rnatish shart emas! 🚀

Savollar bo'lsa, README.md ni o'qing yoki admin bilan bog'laning.
