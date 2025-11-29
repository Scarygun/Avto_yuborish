import asyncio
from bot import main
from utils import logger

if __name__ == '__main__':
    """Botni ishga tushirish"""
    try:
        logger.info("=" * 50)
        logger.info("Telegram Auto-Messaging Bot")
        logger.info("=" * 50)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nBot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"Kritik xatolik: {str(e)}", exc_info=True)
