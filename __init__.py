import os
import re
import telebot
from dotenv import load_dotenv
from bot.database import session, Chat, User
from telebot.apihelper import ApiTelegramException as TgException

load_dotenv()
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


def extract_arg(text):
    try:
        return text.split()[1]
    except IndexError:
        return None


@bot.message_handler(commands=['start'])
def command_start_handler(message):
    if message.chat.type == 'private':
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


@bot.message_handler(commands=['p', 'profile', 'stats', 'п', 'профіль'])
def command_stats_handler(message):
    if message.chat.type == 'supergroup':
        user = session.query(User).filter_by(user_id=message.from_user.id, chat_id=message.chat.id).first()
        if not user:
            return bot.send_message(message.chat.id, 'Статистика пуста. Напишіть хоча б одне повідомлення.')

        firstname = bot.get_chat_member(user.chat_id, user.user_id).user.first_name
        joined = user.created_at
        words = user.word_count
        chars = user.ch_count

        return bot.send_message(
            message.chat.id,
            f'''
🧑‍💻 User: <b>{firstname}</b>
🗓️ Joined: <b>{joined}</b>
🔤 Words: <b>{words}</b>
🔣 Characters: <b>{chars}</b>
            ''',
            parse_mode='HTML'
        )


@bot.message_handler(commands=['chats', 'чати'])
def command_chats_handler(message):
    if message.chat.type == 'private':
        users = session.query(User).filter(User.user_id == message.from_user.id).all()

        if not users:
            return bot.send_message(message.chat.id, 'Ви ще не зареєстровані ні в одному чаті.')

        chats = []
        for user in users:
            chats.append(bot.get_chat(user.chat_id))

        if not chats:
            return bot.send_message(message.chat.id, 'Ви ще не зареєстровані ні в одному чаті.1')

        arg = extract_arg(message.text)

        if not arg.isnumeric():
            return bot.send_message(message.chat.id, "Потрібно ввести число.")

        if not arg:

            msg = "<b>Чати:</b>\n\n"
            for chat_id, chat in enumerate(chats):
                msg += f"{chat_id+1}. {chat.title}\n"

            msg += "\nЩоб переглянути статистику певного чату - напишіть /chats номер_чату. Приклад: /chats 1"

            return bot.send_message(message.chat.id, msg, parse_mode='HTML')

        try:
            chat = chats[int(arg)-1]
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

        return bot.send_message(
            message.chat.id,
            f'''
💬 Chat: <b>{name}</b>
            
🧑‍💻 User: <b>{firstname}</b>
🗓️ Joined: <b>{joined}</b>
🔤 Words: <b>{words}</b>
🔣 Characters: <b>{chars}</b>
                    ''',
            parse_mode='HTML'
        )


@bot.message_handler()
def message_handler(message):
    if message.chat.type == 'supergroup':
        chat_id = message.chat.id
        user_id = message.from_user.id

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

        words = re.findall(r'\b\w+\b', message.text)
        characters = len(message.text)

        chat.words_count += len(words)
        chat.ch_count += characters
        user.word_count += len(words)
        user.ch_count += characters

        session.commit()


if __name__ == '__main__':
    bot.polling(none_stop=True)


# TODO: Global leaderboard
# TODO: Local(group) leaderboard
# TODO: Statistics graph (daily) (monthly)
# TODO: Deleting data from database
# TODO: Another media type logging
