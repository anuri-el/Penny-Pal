import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
BOT_USERNAME = '@penny_pal_bot'

def main():
    print('starting bot...')
    app = Application.builder().token(API_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('polling...')
    app.run_polling(poll_interval=3)


# commands

# /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text('Welcome to Penny Pal Bot!')
    except Exception as e:
        print(str(e))


# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Here’s how I can help you manage your finances. just press "/"')


# responses
def handle_response(text):
    text = text.lower()

    if 'hello' in text:
        return 'hi'
    return 'dunno'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text

    print(f'user ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            text = text.replace(BOT_USERNAME, '').strip()
            response = handle_response(text)
        return
    response = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__=="__main__":
    main()
