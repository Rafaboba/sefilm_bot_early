import requests
from telegram import Update,  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater,  ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CallbackContext
import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute("""
create table if not exists actions
    (user_id longint,
    issearching_by_name bool,
    issearching_by_filters bool
    )
""")
conn.commit()
async def start(update, context) -> None:
    user_id = update.message.from_user.id
    keyboard = [
        [InlineKeyboardButton("Поиск по названию", callback_data='button1')],
        #[InlineKeyboardButton("Поиск по фильтру", callback_data='button2')],
    ]
    reply_markup= InlineKeyboardMarkup(keyboard)
    cursor.execute(f'''
                       select * from actions where user_id={user_id}
                       ''')
    actions = cursor.fetchone()
    if actions is None:
        cursor.execute(f'''
            insert into actions (user_id) values ({user_id})
            ''')
        conn.commit()
    await update.message.reply_text("Выберите кнопку:", reply_markup=reply_markup)


async def button(update, context) -> None:
    user_id = update.callback_query.from_user.id
    query = update.callback_query
    await query.answer()
    if query.data == 'button1':
        cursor.execute(f'''
                update actions set issearching_by_name=true where user_id={user_id}
                ''')
        conn.commit()
        await update.callback_query.message.reply_text("Введите название фильма:")
    if query.data == 'button2':
        cursor.execute(f'''
                       update actions set issearching_by_filters=true where user_id={user_id}
                       ''')
        conn.commit()

def search_movie(api_key, query):
    # Формируем URL для поиска
    url = f'https://api.kinopoisk.dev/v1.3/movie?name={query}&token={api_key}'

    # Отправляем GET-запрос
    response = requests.get(url)

    # Проверяем успешность запроса
    if response.status_code != 200:
        print("Ошибка при выполнении запроса:", response.status_code)
        return

    # Получаем данные в формате JSON
    data = response.json()
    print(data)

    # Проверяем, есть ли результаты
    if 'docs' in data and data['docs']:
        movie = data['docs'][0]
        movie_link = f"https://www.kinopoisk.ru/film/{movie['id']}/"
            # Заменяем домен в ссылке
        modified_url = movie_link.replace("kinopoisk.ru", "kinopoisk.cx")
        print(f'Приятного просмотра: {modified_url}')
        return modified_url
    else:
        print("Фильмы не найдены.")

# Пример использования
api_key = '0FT91X0-R25MYEH-KVP0JP8-WB9H59H'  # Замените на ваш API-ключ
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_message = update.message.text  # Получаем текст сообщения от пользователя
    cursor.execute(f'''
                   select * from actions where user_id={user_id}
                   ''')
    actions = cursor.fetchone()
    print(actions)
    if int(actions[1]) == 1:
        cursor.execute(f'''
                        update actions set issearching_by_name=false where user_id={user_id}
                        ''')
        conn.commit()
        movie_url = search_movie(api_key,user_message)
        await update.message.reply_text(movie_url)  # Отвечаем пользователю
app = ApplicationBuilder().token("7933889026:AAGXRiGLo1f0t2L99TXJ354-mlZmFbBw69Q").build()
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
app.run_polling()