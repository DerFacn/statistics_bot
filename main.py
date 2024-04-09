import os
import re
import telebot
from dotenv import load_dotenv
from database import session, Chat, User
from telebot.apihelper import ApiTelegramException as TgException

load_dotenv()
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


def extract_arg(text):
    try:
        return text.split()[1]
    except IndexError:
        return None


def get_data(chat_id, user_id):
    chat = session.query(Chat).filter_by(chat_id=chat_id).first()
    if not chat:
        chat = Chat(chat_id=chat_id)
        session.add(chat)
        session.commit()

    user = session.query(User).filter_by(user_id=user_id, chat_id=chat_id).first()
    if not user:
        user = User(user_id=user_id, chat_id=chat_id)
        session.add(user)
        session.commit()

    return chat, user


def initialize(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    return get_data(chat_id, user_id)


@bot.message_handler(commands=['start'], chat_types=['private'])
def command_start_handler(message):
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if not user:
        return bot.send_message(
            message.chat.id,
            f'''
Привіт, <b>{message.from_user.first_name}</b>!

Як бачу, ти вперше звертаєшся до мене, так як тебе немає в моїй базі даних.\n
Якщо ти ще не знаєш, я бот статистики - збираю статистику повідомлень з чатів і записую в бд.\n
⚠️ Я не використовую жодної конфіденційної інформації окрім айді!
Воно використовується лише для логування під певним користувачем.\n
Що б почати використовувати мене, просто додайте мене в свою групу,
де в мене мають бути адмін права.
            ''',
            parse_mode='HTML')
    bot.send_message(
        message.chat.id,
        f'''
Привіт, <b>{message.from_user.first_name}</b>!

Ваш айді є в моїй базі даних, ви можете переглянути скільки
повідомлень всього написали за весь час, для цього напишіть команду /chats\n
Що б почати використовувати мене, просто додайте мене в свою групу,
де в мене мають бути адмін права.
        ''',
        parse_mode='HTML'
    )


@bot.message_handler(commands=['p', 'profile', 'stats', 'п', 'профіль'], chat_types=['supergroup'],
                     func=lambda message: not message.reply_to_message)
def command_stats_handler(message):
    user = session.query(User).filter_by(user_id=message.from_user.id, chat_id=message.chat.id).first()
    if not user:
        return bot.send_message(message.chat.id, 'Статистика пуста. Напишіть хоча б одне повідомлення.')

    firstname = bot.get_chat_member(user.chat_id, user.user_id).user.first_name
    joined = user.created_at
    words = user.word_count
    chars = user.ch_count
    photo = user.photo_count
    video = user.video_count
    audio = user.audio_count
    sticker = user.sticker_count

    return bot.send_message(
        message.chat.id,
        f'''
🧑‍💻 User: <b>{firstname}</b>
🗓️ Joined: <b>{joined}</b>
🔤 Words: <b>{words}</b>
🔣 Characters: <b>{chars}</b>
🖼️ Photo: <b>{photo}</b>
📹 Video: <b>{video}</b>
🎵 Audio: <b>{audio}</b>
✨ Sticker: <b>{sticker}</b>
        ''',
        parse_mode='HTML'
    )


@bot.message_handler(chat_types=['supergroup'], content_types=['text'],
                     commands=['p', 'profile', 'stats', 'п', 'профіль'],
                     func=lambda message: not message.from_user.is_bot and message.reply_to_message)
def get_user_stats_by_reply(message):
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    chat, user = get_data(chat_id, user_id)

    if not chat:
        return bot.send_message(chat_id, "Чат не знайдено в базі даних. Можливо, ніхто нічого ще не написав в нього.")

    if not user:
        return bot.send_message(chat_id, "Користувача не знайдено в базі даних. Схоже, він видалив свої дані.")

    firstname = message.reply_to_message.from_user.first_name
    joined = user.created_at
    words = user.word_count
    chars = user.ch_count
    photo = user.photo_count
    video = user.video_count
    audio = user.audio_count
    sticker = user.sticker_count

    return bot.send_message(
        message.chat.id,
        f'''
🧑‍💻 User: <b>{firstname}</b>
🗓️ Joined: <b>{joined}</b>
🔤 Words: <b>{words}</b>
🔣 Characters: <b>{chars}</b>
🖼️ Photo: <b>{photo}</b>
📹 Video: <b>{video}</b>
🎵 Audio: <b>{audio}</b>
✨ Sticker: <b>{sticker}</b>
            ''',
        parse_mode='HTML'
    )


@bot.message_handler(commands=['chats', 'чати'], chat_types=['private'])
def command_chats_handler(message):
    users = session.query(User).filter(User.user_id == message.from_user.id).all()

    if not users:
        return bot.send_message(message.chat.id, 'Ви ще не зареєстровані ні в одному чаті.')

    chats = []
    for user in users:
        chats.append(bot.get_chat(user.chat_id))

    if not chats:
        return bot.send_message(message.chat.id, 'Ви ще не зареєстровані ні в одному чаті.1')

    arg = extract_arg(message.text)

    if not arg:

        msg = "<b>Чати:</b>\n\n"
        for chat_id, chat in enumerate(chats):
            msg += f"{chat_id + 1}. {chat.title}\n"

        msg += "\nЩоб переглянути статистику певного чату - напишіть /chats номер_чату. Приклад: /chats 1"

        return bot.send_message(message.chat.id, msg, parse_mode='HTML')

    if not arg.isnumeric():
        return bot.send_message(message.chat.id, "Потрібно ввести число.")

    try:
        chat = chats[int(arg) - 1]
    except IndexError:
        return bot.send_message(message.chat.id, "Ви обрали невірний айді.")

    user_obj = session.query(User).filter_by(user_id=message.from_user.id, chat_id=chat.id).first()
    if not user_obj:
        return bot.send_message(message.chat.id, "На жаль, чат було видалено з бази данних.")

    try:
        name = bot.get_chat(user_obj.chat_id).title
    except TgException:
        name = "Deleted."
    firstname = message.from_user.first_name
    joined = user_obj.created_at
    words = user_obj.word_count
    chars = user_obj.ch_count
    photo = user_obj.photo_count
    video = user_obj.video_count
    audio = user_obj.audio_count
    sticker = user_obj.sticker_count

    return bot.send_message(
        message.chat.id,
        f'''
💬 Chat: <b>{name}</b>

🧑‍💻 User: <b>{firstname}</b>
🗓️ Joined: <b>{joined}</b>
🔤 Words: <b>{words}</b>
🔣 Characters: <b>{chars}</b>
🖼️ Photo: <b>{photo}</b>
📹 Video: <b>{video}</b>
🎵 Audio: <b>{audio}</b>
✨ Sticker: <b>{sticker}</b>
        ''',
        parse_mode='HTML'
    )


@bot.message_handler(chat_types=['supergroup'], content_types=['text'],
                     func=lambda message: not message.from_user.is_bot)
def message_handler(message):
    chat, user = initialize(message)

    words = re.findall(r'\b\w+\b', message.text)
    characters = len(message.text)

    chat.words_count += len(words)
    chat.ch_count += characters
    user.word_count += len(words)
    user.ch_count += characters

    session.commit()


@bot.message_handler(chat_types=['supergroup'], content_types=['photo'],
                     func=lambda message: not message.from_user.is_bot)
def photo_handler(message):
    chat, user = initialize(message)

    chat.photo_count += 1
    user.photo_count += 1

    session.commit()


@bot.message_handler(chat_types=['supergroup'], content_types=['video'],
                     func=lambda message: not message.from_user.is_bot)
def video_handler(message):
    chat, user = initialize(message)

    chat.video_count += 1
    user.video_count += 1

    session.commit()


@bot.message_handler(chat_types=['supergroup'], content_types=['audio'],
                     func=lambda message: not message.from_user.is_bot)
def audio_handler(message):
    chat, user = initialize(message)

    chat.audio_count += 1
    user.audio_count += 1

    session.commit()


@bot.message_handler(chat_types=['supergroup'], content_types=['sticker'],
                     func=lambda message: not message.from_user.is_bot)
def sticker_handler(message):
    chat, user = initialize(message)

    chat.sticker_count += 1
    user.sticker_count += 1

    session.commit()


# TODO: Global leaderboard
# TODO: Local(group) leaderboard
# TODO: Statistics graph (daily) (monthly)
# TODO: Deleting data from database
