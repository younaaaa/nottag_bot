import logging
from telegram.ext import Updater
from handlers import setup_handlers
from config import Config
from utils.cache import init_cache

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    init_cache()
    
    application = Application.builder().token("TOKEN").build()

    )
    
    setup_handlers(updater.dispatcher)
    
    application.run_polling()
    logger.info("Bot started successfully")
    updater.idle()

if __name__ == '__main__':
    main()