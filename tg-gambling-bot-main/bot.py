from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from os import environ
from datetime import datetime
import random
from src.data import (user_chat, developer_HELP, user_data, questions, dead_end_message, \
                      end_message, links_buttons, sentences, end_time, draw_time, gambling_text, parameters)
from src.db.database_postgre import DataBase, create_database

BOT_TOKEN = environ["BOT_TOKEN"]
GROUP_CHAT_ID = environ["GROUP_CHAT_ID"]
OUTER_GROUP_CHAT_ID = environ["OUTER_GROUP_CHAT_ID"]
TOPIC_ID = int(environ["TOPIC_ID"])

bot = TeleBot(BOT_TOKEN)
bot.parse_mode = "HTML"

print(f"Bot started: GROUP_CHAT_ID={GROUP_CHAT_ID}, TOPIC_ID={TOPIC_ID}")


@bot.message_handler(commands=["create_db"])
def create_db(message):
    if message.chat.id == developer_HELP:
        bot.send_message(developer_HELP, f"{create_database()}")


@bot.message_handler(commands=["id"])
def chat_id(message):
    topic_id = message.message_thread_id
    bot.send_message(message.chat.id, f"Chat id: {message.chat.id}, topic ID: {topic_id}",
                     message_thread_id=topic_id)


@bot.message_handler(commands=["help"])
def bot_help(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, text='Команда /topic для того что бы предложить нам тему.\n'
                                               'Команда /new_gambling для того что бы создать новый конкурс\n'
                                               'Команда /view для того что бы посмотреть свои конкурсы')


@bot.message_handler(commands=["topic"])
def topic_survey(message):
    if message.chat.type == 'private':
        try:
            markup = ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add(sentences['answer_pos'], sentences['answer_neg'])
            bot.send_message(message.chat.id, questions[0], reply_markup=markup)
            bot.register_next_step_handler(message, share)
        except Exception as e:
            bot.send_message(developer_HELP, text=e)


def share(message):
    if message.text.lower() == sentences['answer_pos'].lower():
        bot.send_message(message.chat.id, questions[1], reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, ask_name)
    elif message.text.lower() == sentences['answer_neg'].lower():
        markup = InlineKeyboardMarkup()
        markup.add(links_buttons[0])
        markup.add(links_buttons[1])
        markup.add(links_buttons[2])
        bot.send_message(message.chat.id, text=dead_end_message, reply_markup=markup)


def ask_name(message):
    if len(message.text) <= 1 or any(not s.isalnum() for s in message.text.split()) or any(
            s.isdigit() for s in message.text):
        bot.send_message(message.chat.id, text=sentences['issue_name'])
        bot.register_next_step_handler(message, ask_name)
    else:
        user_data['name'] = message.text
        bot.send_message(message.chat.id, text=questions[2])
        bot.register_next_step_handler(message, topic_gambling)


def topic_gambling(message):
    if len(message.text) < 3:
        bot.send_message(message.chat.id, text=sentences['issue_topic'])
        bot.register_next_step_handler(message, topic_gambling)
    else:
        user_data['topic'] = message.text
        markup = ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add("Telegram", "Email")
        bot.send_message(message.chat.id, text=questions[3], reply_markup=markup)
        bot.register_next_step_handler(message, contact_method)


def contact_method(message):
    if message.text.lower() == "telegram":
        bot.send_message(message.chat.id, "Пожалуйста поделитесь своим ником в Telegram",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, handle_telegram)

    else:
        bot.send_message(message.chat.id, "Пожалуйста, поделитесь своей почтой",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, handle_email)


def handle_telegram(message):
    group_message = (f"📝 Новая идея материала\n"
                     f"Автор: <b>{user_data['name']}</b>\n"
                     f"Тема: <i>{user_data['topic']}</i>\n"
                     f"Ник в Telegram: {message.text}")
    bot.send_message(GROUP_CHAT_ID, group_message, message_thread_id=TOPIC_ID)
    bot.send_message(user_chat, group_message, message_thread_id=TOPIC_ID)
    markup = InlineKeyboardMarkup()
    markup.add(links_buttons[0])
    markup.add(links_buttons[1])
    markup.add(links_buttons[2])
    bot.send_message(message.chat.id, text=end_message, reply_markup=markup)


def handle_email(message):
    group_message = (f"📃 Новая идея материала\n"
                     f"Автор: <b>{user_data['name']}</b>\n"
                     f"Тема: <i>{user_data['topic']}</i>\n"
                     f"E-mail: {message.text}")
    bot.send_message(GROUP_CHAT_ID, group_message, message_thread_id=TOPIC_ID)
    bot.send_message(user_chat, group_message, message_thread_id=TOPIC_ID)
    markup = InlineKeyboardMarkup()
    markup.add(links_buttons[0])
    markup.add(links_buttons[1])
    markup.add(links_buttons[2])
    bot.send_message(message.chat.id, text=end_message, reply_markup=markup)


draw_data = {}


@bot.message_handler(commands=["new_gambling"])
def gambling(message):
    try:
        bot.send_message(message.chat.id, gambling_text['name'])
        bot.register_next_step_handler(message, lottery_name)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def lottery_name(message):
    try:
        draw_data['name'] = message.text + '_' + str(message.from_user.id)
        bot.send_message(chat_id=message.chat.id, text=gambling_text['text'])
        bot.register_next_step_handler(message, lottery_text)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def lottery_text(message):
    try:
        draw_data['text'] = message.text
        bot.send_message(chat_id=message.chat.id, text=gambling_text['winners'])
        bot.register_next_step_handler(message, set_winners)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def set_winners(message):
    try:
        draw_data['winners'] = message.text
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        bot.send_message(chat_id=message.chat.id, text=gambling_text['channels'], reply_markup=markup)
        bot.register_next_step_handler(message, req_channels)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def req_channels(message):
    try:
        if message.text.lower() == 'да':
            bot.send_message(chat_id=message.chat.id,
                             text='Write channels to check in format: @somename @somename2'
                                  '\nIMPORTANT bot should be administrator in those channels')
            bot.register_next_step_handler(message, requirements)
        else:
            draw_data['channels'] = None
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('По времени', 'По колличеству участников')
            bot.send_message(chat_id=message.chat.id, text=gambling_text['criteria'], reply_markup=markup)
            bot.register_next_step_handler(message, requirements)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def channels_to_check(message):
    try:
        draw_data['channels'] = message.text.split()
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('По времени', 'По колличеству участников')
        bot.send_message(chat_id=message.chat.id, text=gambling_text['criteria'], reply_markup=markup)
        bot.register_next_step_handler(message, requirements)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def requirements(message):
    try:
        if message.text.lower() == "по времени":
            bot.send_message(chat_id=message.chat.id, text=gambling_text['time'])
            bot.register_next_step_handler(message, set_time)
        elif message.text.lower() == "по колличеству участников":
            bot.send_message(chat_id=message.chat.id, text=gambling_text['participants'])
            bot.register_next_step_handler(message, set_participants)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def set_time(message):
    try:
        draw_data['date'] = datetime.strptime(message.text, '%d.%m.%Y %H:%M')
        if draw_data['date'] <= datetime.now():
            bot.send_message(message.chat.id, gambling_text['invalid_time'])
            return
        bot.send_message(message.chat.id,
                         text=DataBase().append_lottery(draw_data['text'], draw_data['date'], draw_data['winners'],
                                                        None, draw_data['name'],
                                                        creator_tg_id=message.from_user.id,
                                                        subscriptions=draw_data['channels']))
        draw_time[int(draw_data['date'].timestamp())] = {draw_data['name']}
        end_time.append(int(draw_data['date'].timestamp()))
        end_time.sort()
    except ValueError:
        bot.send_message(message.chat.id, gambling_text['invalid_format'])
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def set_participants(message):
    try:
        if int(message.text) > 0:
            draw_data['participants_number'] = int(message.text)
            bot.send_message(message.chat.id,
                             text=DataBase().append_lottery(draw_data['text'], None, draw_data['winners'],
                                                            draw_data['participants_number'], draw_data['name'],
                                                            creator_tg_id=message.from_user.id,
                                                            subscriptions=draw_data['channels']))
    except ValueError:
        bot.send_message(message.chat.id, gambling_text['invalid_number'])
    except Exception as e:
        bot.send_message(developer_HELP, f'Help: {e}')


@bot.message_handler(commands=["view"])
def draw(message):
    try:
        draws_list = DataBase().view_draw(creator_tg_id=message.from_user.id)
        if 'Error' in draws_list:
            bot.send_message(developer_HELP, text=str(draws_list))
            bot.send_message(message.chat.id, 'Произошла ошибка, приносим извинения')
        elif draws_list is []:
            bot.send_message(message.chat.id, gambling_text['view_void'])
        else:
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for draw_ in draws_list:
                markup.add(draw_[0].split('_')[0])
            bot.send_message(message.chat.id, gambling_text['view'], reply_markup=markup)
            bot.register_next_step_handler(message, edit_publish_button)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


user_draw = {}


def edit_publish_button(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Изменить', 'Опубликовать', 'Осмотреть', 'Удалить')
    user_draw[str(message.chat.id) + '_drawname'] = message.text + '_' + str(message.from_user.id)
    bot.send_message(message.chat.id, gambling_text['edit_publish'], reply_markup=markup)
    bot.register_next_step_handler(message, edit_publish)


def edit_publish(message):
    try:
        draw_name = user_draw[str(message.chat.id) + '_drawname']
        if message.text == 'Опубликовать':
            draw_text = DataBase().view_draw(draw_name=draw_name)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Join', callback_data=f"join_{draw_name}"))
            bot.send_message(OUTER_GROUP_CHAT_ID, f'{draw_text[0]}', reply_markup=markup)
        elif message.text == 'Изменить':
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for param in parameters:
                markup.add(param)
            bot.send_message(message.chat.id, f'Что хотите изменить?', reply_markup=markup)
            bot.register_next_step_handler(message, changes)
        elif message.text == 'Осмотреть':
            bot.send_message(message.chat.id, text=DataBase().inspect_draw(draw_name))
        elif message.text == 'Удалить':
            DataBase().delete_draw(draw_name)
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def changes(message):
    user_draw[str(message.chat.id) + '_edit'] = message.text
    bot.send_message(message.chat.id, 'Напишите измененную версию')
    bot.register_next_step_handler(message, edit)


def edit(message):
    try:
        draw_name = user_draw[str(message.chat.id) + '_drawname']
        if user_draw[str(message.chat.id) + '_edit'] == parameters[0]:
            DataBase().edit_draw(draw_name, new_date=message.text)
        elif user_draw[str(message.chat.id) + '_edit'] == parameters[1]:
            DataBase().edit_draw(draw_name, new_num_participants=message.text)
        elif user_draw[str(message.chat.id) + '_edit'] == parameters[2]:
            DataBase().edit_draw(draw_name, new_text=message.text)
        elif user_draw[str(message.chat.id) + '_edit'] == parameters[3]:
            DataBase().edit_draw(draw_name, new_num_winners=message.text)
        elif user_draw[str(message.chat.id) + '_edit'] == parameters[4]:
            DataBase().edit_draw(draw_name, new_sub=message.text)
        bot.send_message(message.chat.id, 'Успешный успех!')
        del user_draw[str(message.chat.id) + '_drawname']
        del user_draw[str(message.chat.id) + '_edit']
    except Exception as e:
        bot.send_message(developer_HELP, text=f'ex: {e}')


def check_subscription(user_id, channels):
    for channel in channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True


def winner(winners_number, participants, draw_name, db_draw_name):
    winners_list = random.sample(participants, winners_number)
    mes = f'Итог конкурса {str(draw_name)}\n'
    if len(winners_list) > 1:
        for i in range(len(winners_list)):
            user_tg = DataBase().view_participants(user_id=winners_list[i], get_tg=True)
            # bot.send_message(chat_id=user_tg, text=f'Вы победили в конкурсе {str(draw_name)}')
            mes += f'{i + 1} место @{bot.get_chat(user_tg).active_usernames[0]}\n'
        mes += 'Поздравляем!'
    else:
        mes += f'Поздравляем с победой @{bot.get_chat(winners_list[0]).active_usernames[0]}'
    bot.send_message(OUTER_GROUP_CHAT_ID, mes)
    DataBase().delete_draw(db_draw_name)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def button(call):
    draw_name = call.data.split('join_')[1]
    participants = DataBase().view_participants(draw_name)

    if participants == 'ended':
        bot.answer_callback_query(call.id, "Конкурс уже закончился")
        return
    if call.from_user.id in participants:
        bot.answer_callback_query(call.id, "Вы уже участвуете!")
        return

    subscriptions = DataBase().view_draw(draw_name=draw_name, check_channels=True)
    participant_number = DataBase().view_draw(draw_name=draw_name, participant_number=True)
    num_winners = DataBase().view_draw(draw_name=draw_name, num_winners=True)

    if subscriptions is not None:
        if subscriptions[0] is not None and not check_subscription(call.from_user.id, subscriptions):
            bot.answer_callback_query(call.id, "Вы должны быть подписаны на каналы")
            return
    try:
        if (len(participants) + 1) == int(participant_number):
            DataBase().append_participant(call.from_user.id, draw_name)
            participants = DataBase().view_participants(draw_name=draw_name)
            winner(num_winners, participants, str(draw_name).split('_')[0], draw_name)
        else:
            bot.answer_callback_query(call.id, text=DataBase().append_participant(call.from_user.id, draw_name))
    except Exception as e:
        bot.send_message(developer_HELP, text=str(e))


@bot.message_handler(content_types=["text"])
def time(message):
    for times in end_time:
        if times >= message.date:
            draw_name = []
            [draw_name.append(x) for x in draw_time[times]]
            participants = DataBase().view_participants(draw_name[0])
            participant_number = DataBase().view_draw(draw_name=draw_name, participant_number=True)
            winner(participant_number, participants, draw_name)


bot.infinity_polling()
