# Telegram Auto-Messaging Bot

Telegram orqali bir nechta guruhlarga avtomatik xabar yuborish tizimi.

## Xususiyatlar

✅ Ko'p foydalanuvchilar tizimi  
✅ Shaxsiy Telegram hisob orqali ishlash  
✅ Bir nechta guruhga avtomatik yuborish  
✅ 5 minut interval guruhlar orasida  
✅ Xabar rejalashtirish (har X soatda)  
✅ Yuborilgan xabarlar tarixi  
✅ Statistika (muvaffaqiyatli/muvaffaqiyatsiz)  
✅ **JSON fayl ma'lumotlar bazasi** (PostgreSQL shart emas!)  

## Texnologiyalar

- Python 3.10+
- Telethon (Telegram API)
- JSON (ma'lumotlar bazasi)
- APScheduler

## O'rnatish

### 1. Talablar

```bash
# Python 3.10+ o'rnatilganligini tekshirish
python3 --version
```

### 2. Virtual environment yaratish

```bash
cd /home/scarygun/Desktop/Loyihalar
python3 -m venv venv
source venv/bin/activate
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. Environment variables sozlash

```bash
# .env faylini yaratish
cp .env.example .env

# .env faylini tahrirlash
nano .env
```

`.env` faylida quyidagilarni to'ldiring:

```env
# Telegram API Credentials (https://my.telegram.org)
API_ID=your_api_id
API_HASH=your_api_hash

# Bot Token (BotFather dan oling)
BOT_TOKEN=your_bot_token

# Sozlamalar
MESSAGE_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

### 5. Telegram API Credentials olish

1. https://my.telegram.org ga kiring
2. "API development tools" ga o'ting
3. Yangi app yarating
4. `api_id` va `api_hash` ni nusxalang

### 6. Bot Token olish

1. Telegram da [@BotFather](https://t.me/BotFather) ni oching
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username kiriting
4. Token ni nusxalang

## Ishga tushirish

```bash
# Virtual environment ni faollashtirish
source venv/bin/activate

# Botni ishga tushirish
python main.py
```

## Foydalanish

### 1. Ro'yxatdan o'tish

```
/start - Botni boshlash
/register - Telefon raqamingizni kiriting (+998901234567)
```

Telefon raqamingizga kod yuboriladi. Kodni kiriting.

### 2. Guruh qo'shish

```
/add_group - Guruhlar ro'yxatidan tanlang
/list_groups - Qo'shilgan guruhlar ro'yxati
/remove_group - Guruhni o'chirish
```

### 3. Xabar yuborish

**Darhol yuborish:**
```
/send_message - Xabar matnini kiriting
```

Barcha guruhlarga 5 minut interval bilan yuboriladi.

**Rejalashtirish:**
```
/schedule_message - Xabar va interval (soat) kiriting
```

Masalan: har 2 soatda bir marta avtomatik yuborish.

### 4. Boshqarish

```
/my_schedules - Rejalashtirilgan vazifalar
/cancel_schedule - Vazifani bekor qilish
/history - Yuborilgan xabarlar tarixi
/stats - Statistika
/help - Yordam
```

## Loyiha tuzilmasi

```
Loyihalar/
├── main.py                 # Entry point
├── bot.py                  # Bot komandalar
├── config.py               # Konfiguratsiya
├── database.py             # JSON database boshqaruvi
├── models.py               # Ma'lumotlar modellari
├── telegram_client.py      # Telegram client boshqaruvi
├── message_sender.py       # Xabar yuborish
├── scheduler.py            # Vazifalarni rejalashtirish
├── utils.py                # Yordamchi funksiyalar
├── requirements.txt        # Python kutubxonalari
├── .env                    # Environment variables
├── .env.example            # Environment namunasi
├── database.json           # Ma'lumotlar bazasi (avtomatik yaratiladi)
├── sessions/               # Telegram session fayllari
└── bot.log                 # Log fayl
```

## Ma'lumotlar Bazasi

Bot **JSON fayl** ishlatadi (`database.json`). PostgreSQL o'rnatish shart emas!

Ma'lumotlar bazasi avtomatik yaratiladi va quyidagi ma'lumotlarni saqlaydi:
- Foydalanuvchilar
- Guruhlar
- Yuborilgan xabarlar tarixi
- Rejalashtirilgan vazifalar

## Xavfsizlik

⚠️ **Muhim:**
- `.env` faylini hech qachon GitHub ga yuklamang
- Session fayllarini xavfsiz saqlang
- Telegram spam qoidalariga rioya qiling
- Ko'p guruhga yuborish hisob bloklashiga olib kelishi mumkin

## Muammolarni hal qilish

### Telegram autentifikatsiya xatoligi

- API_ID va API_HASH to'g'riligini tekshiring
- Telefon raqam xalqaro formatda bo'lishi kerak (+998...)
- 2FA yoqilgan bo'lsa, parolni kiriting

### Spam bloklash

- Guruhlar orasida intervalini oshiring (config.py da)
- Bir vaqtda ko'p guruhga yubormaslik
- Telegram spam qoidalariga rioya qiling

### JSON fayl xatoligi

- `database.json` faylini o'chirish va qayta ishga tushirish
- Fayl ruxsatlarini tekshirish

## Litsenziya

MIT License

## Muallif

Telegram Auto-Messaging Bot

## Yordam

Savollar bo'lsa, issue oching yoki admin bilan bog'laning.
# Avto_yuborish
# Avto_yuborish
