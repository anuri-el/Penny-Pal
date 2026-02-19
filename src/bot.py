import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime
import calendar


API_TOKEN = '8357243424:AAGNiv1eiIpu9nSpsT55sEnF9MxtzCtlVao'
# API_TOKEN = os.getenv('API_TOKEN')
BOT_USERNAME = '@penny_pal_bot'


conn = sqlite3.connect('pennypal.db')
c = conn.cursor()


def main():
    print('starting bot...')
    app = Application.builder().token(API_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('set_category', set_category_command))
    app.add_handler(CommandHandler('get_categories', get_categories_command))
    app.add_handler(CommandHandler('update_category', update_category_command))
    app.add_handler(CommandHandler('delete_category', delete_category_command))
    app.add_handler(CommandHandler('add', add_command))
    app.add_handler(CommandHandler('set_budget', set_budget_command))
    app.add_handler(CommandHandler('get_budgets', get_budgets_command))
    app.add_handler(CommandHandler('update_budget', update_budget_command))
    app.add_handler(CommandHandler('summary', summary_command))
    # app.add_handler(CommandHandler('report', set_category_command))
    # app.add_handler(CommandHandler('report_all', set_category_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('polling...')
    app.run_polling(poll_interval=3)


# commands

# /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        telegram_id = user.id
        username = user.username or ''
        first_name = user.first_name
        last_name = user.last_name or ''

        c.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id, ))
        existing_user = c.fetchone()

        if not existing_user:
            c.execute("""INSERT INTO users(telegram_id, telegram_username, first_name, last_name)
                                    VALUES(?, ?, ?, ?)""", (telegram_id, username, first_name, last_name))
            conn.commit()
            await update.message.reply_text('welcome new user')
        else:
            await update.message.reply_text('welcome back')

    except Exception as e:
        await update.message.reply_text(str(e))


# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Here’s how I can help you manage your finances. just press "/"')


# /set_category name
async def set_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        command = text.split()

        user = update.effective_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)

        if len(command) == 2:
            category_name = command[1]

            c.execute("SELECT * FROM categories WHERE user_id = ? AND category_name = ?", (user_id, category_name))
            existing_category = c.fetchone()

            if existing_category:
                await update.message.reply_text(f'the category already exists')
            else:
                c.execute("INSERT INTO categories(user_id, category_name) VALUES(?, ?)", (user_id, category_name))
                conn.commit()
                await update.message.reply_text(f'success! new category added')

        else:
            await update.message.reply_text('wrong amount of arguments')
    except Exception as e:
            await update.message.reply_text(str(e))


# /get_categories
async def get_categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)
        catgs = get_categories(c, user_id)
        if len(catgs) > 0:
            await update.message.reply_text(catgs)
        else:
            await update.message.reply_text('no catgs')

    except Exception as e:
        await update.messsage.reply_text(str(e))


# /update_category current new
async def update_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        telegram_id = user.id

        text = update.message.text
        command = text.split()

        user_id = get_user_id(c, telegram_id)
        catgs = get_categories(c, user_id)

        if len(command) == 3:
            current_category = command[1]
            new_category = command[2]

            if current_category in catgs:
                c.execute("UPDATE categories SET category_name = ? WHERE category_name = ? AND user_id = ?", (new_category, current_category, user_id))
                conn.commit()
                await update.message.reply_text(f'success! new category name: {new_category}')
            else:
                await update.message.reply_text('category doesnt exist')

        else:
            await update.message.reply_text('wrong amount of arguments')
    except Exception as e:
            await update.message.reply_text(srt(e))


# /delete_category name
async def delete_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)

        text = update.message.text
        command = text.split()

        if len(command) == 2:
            category_name = command[1]

            catgs = get_categories(c, user_id)

            if category_name in catgs:
                c.execute("DELETE FROM categories WHERE user_id = ? AND category_name = ?", (user_id, category_name))
                conn.commit()
                await update.message.reply_text('success! category was deleted')
            else:
                await update.message.reply_text('category doesnt exist to begin with')

        else:
            await update.message.reply_text('wrong amount of arguments')
    except Exception as e:
            await update.message.reply_text(str(e))


# /add category transaction amount [type]
# type enum('expense', 'income'). default == 'expense'
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)

        text = update.message.text
        command = text.split()

        if len(command) == 5 or len(command) == 4:
            types = ['income', 'expense']
            transaction_name = command[2]

            catgs = get_categories(c, user_id)

            category_name = command[1]
            category_id = get_category_id(c, user_id, category_name)
            if category_name in catgs:
                category_id = get_category_id(c, user_id, category_name)
            else:
                return await update.message.reply_text('category does not exist')

            amount = command[3]

            if not is_numeric_string(amount):
                return await update.message.reply_text('nono amount')
            else:
                amount = float(amount)
        else:
            return await update.message.reply_text('wrong amount of arguments')

        if len(command) == 5:
            type = command[4]

            if type in types:
                c.execute("INSERT INTO transactions(user_id, category_id, transaction_name, amount, type) VALUES(?, ?, ?, ?, ?)", (user_id, category_id, transaction_name, amount, type))
                conn.commit()
                await update.message.reply_text('success')
            else:
                await update.message.reply_text('type nono')

        elif len(command) == 4:
            type = 'expense'
            c.execute("INSERT INTO transactions(user_id, category_id, transaction_name, amount, type) VALUES(?, ?, ?, ?, ?)", (user_id, category_id, transaction_name, amount, type))
            conn.commit()
            await update.message.reply_text('success')
        else:
            await update.message.reply_text('wrong amount of arguments')

    except Exception as e:
        await update.message.reply_text(str(e))


# /set_budget category amount [month]
# month enum. default == month from timestamp
async def set_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        command = text.split()
        # return await update.message.reply_text(command)

        user = update.effective_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)
        catgs = get_categories(c, user_id)

        months = { 'january': '01', 'february' : '02' }


        if len(command) not in (3, 4):
            return await update.message.reply_text('Usage: /set_budget category amount [month]')


        category_name = command[1]

        if category_name in catgs:
            category_id = get_category_id(c, user_id, category_name)
        else:
            return await update.message.reply_text('category does not exist')

        amount = command[2]

        if is_numeric_string(amount):
            amount = float(amount)
        else:
            return await update.message.reply_text('amount nono')

        if len(command) == 4:
            month_str = command[3]
            month_year = parse_month(month_str)
            c.execute("INSERT INTO budgets(user_id, category_id, amount, month_year) VALUES (?, ?, ?, ?)", (user_id, category_id, amount, month_year))
            conn.commit()
            await update.message.reply_text('success')

        else:
            c.execute("INSERT INTO budgets(user_id, category_id, amount) VALUES (?, ?, ?)", (user_id, category_id, amount))
            conn.commit()
            await update.message.reply_text('success')

    except Exception as e:
        await update.message.reply_text(str(e))



# /get_budgets [month]
# month enum. default == month from timestamp
async def get_budgets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effecient_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)
        c.execute('SELECT * FROM budgets WHERE user_id = ?', (user_id))
        budgets = c.fetchall()
        if budgets:
            return await update.message.reply_text(budgets)
        return await update.message.reply_text('no budgets')
    except Exception as e:
        await update.message.reply_text(str(e))


# /update_budget category amount new_amount [month]
# month >= current
async def update_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass



# /summary [day]
# day == datestamp default
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        command = text.split()

        user = update.effecient_user
        telegram_id = user.id

        user_id = get_user_id(c, telegram_id)

        if command.lenght() == 2:
            date = command[1]

            c.execute('SELECT * FROM transactions WHERE user_id = ? AND date_time = ?', (user_id, date_time))
            trans_date = c.fetchall()
            await update.message.reply_text('day')
        elif command.lenght() == 1:
            # date_time =
            # day from timestamp
            c.execute('SELECT * FROM transactions WHERE user_id = ? AND date_time = ?', (user_id, date_time))
            trans_today = c.fetchall()

            await update.message.reply_text(trans_today)
        else:
            await update.message.reply_text('wrong amount of arguments')
    except Exception as e:
        await update.message.reply_text(str(e))


# /report category type [month]
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        command = text.split()
        if command.lenght() == 4:
            category = command[1]
            type = command[2]
            month = command[3]
                # get category_id
                # db
            await update.message.reply_text('success')
        elif command.lenght() == 3:
            category = command[1]
            type = command[2]
                # month = timestamp
                # db
            await update.message.reply_text('success')
        else:
            await update.message.reply_text('wrong amount of arguments')
    except Exception as e:
        await update.message.reply_text(e)


# /report_all type [month]
async def report_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        command = text.lower().split()
        if command.lenght() == 3:
            type = command[1]
            month = command[2]
                # get category_id
                # db
            await update.message.reply_text('success')
        elif command.lenght() == 2:
            type = command[1]
                # month = timestamp
                # db
            await update.message.reply_text('success')
        else:
            await update.message.reply_text('wrong amount of arguments')
    except Exception as e:
        await update.message.reply_text(e)




async def set_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def update_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def delete_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass











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











def is_numeric_string(s):
    try:
        float(s)
        return True
    except Exception:
        return False



def get_user_id(c, telegram_id):
    try:
        c.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id, ))
        user_id = c.fetchone()[0]
        return user_id
    except Exception as e:
        return str(e)


def get_categories(c, user_id):
    try:
        c.execute("SELECT category_name FROM categories WHERE user_id = ?", (user_id, ))
        categories = c.fetchall()

        catgs = []
        for category in categories:
            category = category[0]
            catgs.append(category)
        return catgs
    except Exception as e:
        return str(e)


def get_category_id(c, user_id, category_name):
    try:
        catgs = get_categories(c, user_id)
        if category_name in catgs:
            c.execute("SELECT id FROM categories WHERE user_id = ? AND category_name = ?", (user_id, category_name))
            category_id = c.fetchone()[0]
            return category_id
        else:
            return 'category does not exist'
    except Exception as e:
        return str(e)


def parse_month(month_input):
    now = datetime.now()
    m = month_input.strip().lower()

    if m.isdigit():
        m_num = int(m)
        if 1 <= m_num <= 12:
            return f'{now.year}-{m_num:02d}'

    months_map = {
        month.lower() : idx
        for idx, month in enumerate(calendar.month_name)
        if month
    }
    abbr_map = {
        month.lower() : idx
        for idx, month in enumerate(calendar.month_abbr)
        if month
    }
    if m in months_map:
        return f'{now.year}-{months_map[m]:02d}'

    if m in abbr_map:
        return f'{now.year}-{abbr_map[m]:02d}'

    return None


if __name__=="__main__":
    main()