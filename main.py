import matplotlib
matplotlib.use('Agg')
import os
import re
import telebot
import warnings
import datetime
from uuid import uuid4
from dotenv import load_dotenv
from stats import Record, Group
import matplotlib.pyplot as plt
from stats import session as stats
from database import session, Chat, User, Value
from telebot.apihelper import ApiTelegramException as TgException

load_dotenv()
warnings.filterwarnings('ignore')  # Matplotlib UserWarning disable
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


# ======================================= Functions ======================================= #
def extract_arg(text):
    try:
        return text.split()[1]
    except IndexError:
        return None


def get_data(chat_id, user_id):
    chat = session.query(Chat).filter_by(chat_id=chat_id).first()
    if not chat:
        value = Value()
        session.add(value)
        session.commit()

        chat = Chat(chat_id=chat_id, values_id=value.id)
        session.add(chat)
        session.commit()

    user = session.query(User).filter_by(user_id=user_id, chat_id=chat_id).first()
    if not user:
        value = Value()
        session.add(value)
        session.commit()

        user = User(user_id=user_id, chat_id=chat_id, values_id=value.id)
        session.add(user)
        session.commit()

    return chat, user


def get_stats(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%d')

    group = stats.query(Group).filter_by(chat_id=chat_id, day=day, hour=hour).first()
    if not group:
        group = Group(
            chat_id=chat_id,
            day=day,
            hour=hour
        )
        stats.add(group)
        stats.commit()

    record = stats.query(Record).filter_by(user_id=user_id, chat_id=chat_id, day=day, hour=hour).first()
    if not record:
        record = Record(
            user_id=user_id,
            chat_id=chat_id,
            day=day,
            hour=hour
        )
        stats.add(record)
        stats.commit()

    return group, record


def get_user_stats(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    day = datetime.datetime.now().strftime('%d')
    return stats.query(Record).filter(Record.user_id == user_id, Record.chat_id == chat_id, Record.day == day).all()


def get_group_stats(message):
    chat_id = message.chat.id
    day = datetime.datetime.now().strftime('%d')
    return stats.query(Group).filter(Group.chat_id == chat_id, Group.day == day).all()


def draw_graph(stats_, title):
    y = [0] * 24

    for stat in stats_:
        y[stat.hour] = stat.count

    '''
    If you want more detailed Y-axis labels, uncomment this part of the code
    '''
    # highest = sorted(y, reverse=True)[0]
    # steps = int(str(highest)[:2]) + 3
    # power = len(str(highest)) - 2
    # step_weight = 1 * 10 ** power

    # step = [step_weight * i for i in range(steps)]

    plt.bar(range(24), y)
    plt.xlabel('Hours')
    plt.ylabel('Characters')
    plt.title(f'{title}\'s graph')
    plt.xticks(range(24))
    # plt.yticks(step)
    idd = str(uuid4())
    plt.savefig(f'{idd}.png')
    plt.close()
    return idd


def user_hours_graph(stats_):
    try:
        username = bot.get_chat_member(stats_[0].chat_id, stats_[0].user_id).user.first_name
    except TgException:
        username = 'Deleted.'

    return draw_graph(stats_, username)


def group_hours_graph(stats_):
    try:
        title = bot.get_chat(stats_[0].chat_id).title
    except TgException:
        title = 'Deleted.'

    return draw_graph(stats_, title)


def initialize(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    return get_data(chat_id, user_id)


def send_stats(chat_id, user, firstname):
    joined = user.created_at
    words = user.values.words_count
    chars = user.values.ch_count
    photo = user.values.photo_count
    video = user.values.video_count
    audio = user.values.audio_count
    sticker = user.values.sticker_count

    return bot.send_message(
        chat_id,
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


# ======================================= Commands handlers ======================================= #
@bot.message_handler(commands=['start'],
                     chat_types=['private'], func=lambda message: not message.from_user.is_bot)
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


@bot.message_handler(commands=['help'],
                     chat_types=['private', 'supergroup'], func=lambda message: not message.from_user.is_bot)
def command_help_private_handler(message):
    msg = '''
<b>Команди</b>

/stats - дізнатись статистику (групи). У відповідь на повідомлення, пише стати-ку цього користувача.
/top - топ-3 самих активних (групи)
/chats - чати з вашою стати-кою (приват)
/chats 1 - стати-ка певного чату (приват)
    '''
    bot.send_message(message.chat.id, msg, parse_mode='HTML')


@bot.message_handler(commands=['p', 'profile', 'stats', 'п', 'профіль'],
                     chat_types=['supergroup'], func=lambda message: not message.reply_to_message)
def command_stats_handler(message):
    user = session.query(User).filter_by(user_id=message.from_user.id, chat_id=message.chat.id).first()
    if not user:
        return bot.send_message(message.chat.id, 'Статистика пуста. Напишіть хоча б одне повідомлення.')

    firstname = bot.get_chat_member(user.chat_id, user.user_id).user.first_name

    send_stats(message.chat.id, user, firstname)


@bot.message_handler(commands=['p', 'profile', 'stats', 'п', 'профіль'],
                     chat_types=['supergroup'],
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

    send_stats(message.chat.id, user, firstname)


@bot.message_handler(commands=['me'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def send_user_graph(message):
    stats_ = get_user_stats(message)
    idd = user_hours_graph(stats_)

    with open(f'{idd}.png', 'rb') as file:
        photo = file.read()
        bot.send_photo(message.chat.id, photo)
    os.system(f'del {idd}.png') if os.name == 'nt' else os.system(f'rm {idd}.png')


@bot.message_handler(commands=['chat'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def send_chat_graph(message):
    stats_ = get_group_stats(message)
    idd = group_hours_graph(stats_)

    with open(f'{idd}.png', 'rb') as file:
        photo = file.read()
        bot.send_photo(message.chat.id, photo)
    os.system(f'del {idd}.png') if os.name == 'nt' else os.system(f'rm {idd}.png')


@bot.message_handler(commands=['chats', 'чати'],
                     chat_types=['private'], func=lambda message: not message.from_user.is_bot)
def command_chats_handler(message):
    users = session.query(User).filter(User.user_id == message.from_user.id).all()

    if not users:
        return bot.send_message(message.chat.id, 'Ви ще не зареєстровані ні в одному чаті.')

    chats = []
    for user in users:
        try:
            chats.append(bot.get_chat(user.chat_id))
        except TgException:
            pass

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

    user = session.query(User).filter_by(user_id=message.from_user.id, chat_id=chat.id).first()
    if not user:
        return bot.send_message(message.chat.id, "На жаль, чат було видалено з бази данних.")

    try:
        name = bot.get_chat(user.chat_id).title
    except TgException:
        name = "Deleted."
    firstname = message.from_user.first_name
    joined = user.created_at
    words = user.values.words_count
    chars = user.values.ch_count
    photo = user.values.photo_count
    video = user.values.video_count
    audio = user.values.audio_count
    sticker = user.values.sticker_count

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


@bot.message_handler(commands=['top', 't', 'топ', 'т'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def command_top_handler(message):
    chat, user_ = initialize(message)

    users = session.query(User).filter(User.chat_id == chat.chat_id).all()

    if not users:
        return bot.send_message(message.chat.id, "Не знайдено користувачів для топа.")

    def compare(obj):
        return obj.values.words_count

    sorted_users = sorted(users, key=compare, reverse=True)
    count = min(3, len(sorted_users))
    top_3 = sorted_users[:count]

    top_v = [user.values.words_count for user in top_3]
    top_names = []

    for index, user in enumerate(top_3):
        try:
            name = bot.get_chat_member(chat.chat_id, user.user_id).user.first_name
        except TgException:
            name = 'Deleted.'
        top_names.append(name)

    medals = ["🥇", "🥈", "🥉"]

    msg = "<b>TOP-3 by words</b>\n\n"

    for index, value in enumerate(top_v):
        msg += f'''{medals[index]} {top_names[index]}: <b>{value}</b>\n'''

    return bot.send_message(message.chat.id, msg, parse_mode='HTML')


# ======================================= Message handlers ======================================= #
@bot.message_handler(content_types=['text'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def message_handler(message):
    chat, user = initialize(message)
    group, record = get_stats(message)

    words = re.findall(r'\b\w+\b', message.text)
    characters = len(message.text)

    chat.values.words_count += len(words)
    chat.values.ch_count += characters
    group.count += characters
    user.values.words_count += len(words)
    user.values.ch_count += characters
    record.count += characters

    session.commit()
    stats.commit()


@bot.message_handler(content_types=['photo'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def photo_handler(message):
    chat, user = initialize(message)

    chat.values.photo_count += 1
    user.values.photo_count += 1

    session.commit()


@bot.message_handler(content_types=['video'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def video_handler(message):
    chat, user = initialize(message)

    chat.values.video_count += 1
    user.values.video_count += 1

    session.commit()


@bot.message_handler(content_types=['audio'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def audio_handler(message):
    chat, user = initialize(message)

    chat.values.audio_count += 1
    user.values.audio_count += 1

    session.commit()


@bot.message_handler(content_types=['sticker'],
                     chat_types=['supergroup'], func=lambda message: not message.from_user.is_bot)
def sticker_handler(message):
    chat, user = initialize(message)

    chat.values.sticker_count += 1
    user.values.sticker_count += 1

    session.commit()


# TODO: Global leaderboard
# TODO: Statistics graph (monthly)
# TODO: Deleting data from database
