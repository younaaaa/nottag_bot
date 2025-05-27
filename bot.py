from telegram.ext import Application
import os
from config import Config

async def post_init(app):
    await app.bot.set_webhook(f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}")

def main():
    application = Application.builder() \
        .token(Config.BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # پورت اجباری برای Render.com
    port = int(os.environ.get('PORT', 10000))
    
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}",
        secret_token='WEBHOOK_SECRET'  # اختیاری برای امنیت بیشتر
    )

if __name__ == '__main__':
    main()