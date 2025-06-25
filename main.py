import telebot
import os
from telebot import types

API_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_GROUP = int(os.getenv("ALLOWED_GROUP"))
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = telebot.TeleBot(API_TOKEN)

user_states = {}
quiz_data = {}
scores = {}

DEFAULT_OPTIONS = ['A', 'B', 'C', 'D']

def is_allowed(chat_id):
    return chat_id == ALLOWED_GROUP

@bot.message_handler(commands=['start'])
def start(message):
    if not is_allowed(message.chat.id):
        return
    welcome_text = (
        "Hᴇʏ ɢᴜʏ's ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ XD ʙᴏᴛ ᴘʟᴀᴛғᴏʀᴍ 💖\n\n"
        "🌲 Sᴇɴᴅ ⚡ /quiz\n"
        "🌴 Sᴇɴᴅ ǫᴜɪᴢ ᴘʜᴏᴛᴏ ᴡɪᴛʜ ᴏᴘᴛɪᴏɴs A-D\n"
        "🌴 Gɪᴠᴇ ɴᴜᴍʙᴇʀ ғᴏʀ ᴄᴏʀʀᴇᴄᴛ ᴀɴsᴡᴇʀ (A=1, B=2, C=3, D=4)"
    )
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['quiz'])
def quiz_command(message):
    if not is_allowed(message.chat.id):
        return
    sent = bot.send_message(message.chat.id, "Send the question photo.")
    user_states[message.from_user.id] = 'waiting_for_photo'
    quiz_data[message.from_user.id] = {'send_prompt_msg_id': sent.message_id}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if not is_allowed(message.chat.id):
        return
    if user_states.get(message.from_user.id) == 'waiting_for_photo':
        file_id = message.photo[-1].file_id
        quiz_data[message.from_user.id]['photo_id'] = file_id
        quiz_data[message.from_user.id]['photo_msg_id'] = message.message_id
        quiz_data[message.from_user.id]['options'] = DEFAULT_OPTIONS

        try:
            bot.delete_message(message.chat.id, quiz_data[message.from_user.id]['send_prompt_msg_id'])
        except: pass

        msg = bot.send_message(
            message.chat.id,
            f"Options automatically set: {', '.join(DEFAULT_OPTIONS)}\nNow send the correct option number (1-4):"
        )
        quiz_data[message.from_user.id]['option_prompt_msg_id'] = msg.message_id
        user_states[message.from_user.id] = 'waiting_for_correct_option'

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_for_correct_option')
def handle_correct_option(message):
    try:
        correct_option = int(message.text) - 1
        if correct_option < 0 or correct_option >= len(DEFAULT_OPTIONS):
            raise ValueError
        quiz_data[message.from_user.id]['correct_option_id'] = correct_option
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input. Send a number between 1 and 4.")
        return

    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    try: bot.delete_message(message.chat.id, quiz_data[message.from_user.id]['photo_msg_id'])
    except: pass
    try: bot.delete_message(message.chat.id, quiz_data[message.from_user.id]['option_prompt_msg_id'])
    except: pass

    send_quiz(message.chat.id, message.from_user.id)

def send_quiz(chat_id, user_id):
    photo_id = quiz_data[user_id]['photo_id']
    options = quiz_data[user_id]['options']
    correct_option_id = quiz_data[user_id]['correct_option_id']

    bot.send_photo(chat_id, photo=photo_id, caption="📊 ǫᴜɪᴢ ᴡᴀʟʟᴀʜ")
    bot.send_poll(
        chat_id,
        "Choose the correct option!",
        options,
        type='quiz',
        correct_option_id=correct_option_id,
        is_anonymous=False
    )

    user_states.pop(user_id, None)
    quiz_data.pop(user_id, None)

@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    user_id = poll_answer.user.id
    selected_option = poll_answer.option_ids[0]
    if selected_option == 0:
        scores[user_id] = scores.get(user_id, 0) + 1

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    if not is_allowed(message.chat.id):
        return
    leaderboard = "🏆 Leaderboard 🏆\n"
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for idx, (user_id, score) in enumerate(sorted_scores, start=1):
        try:
            user = bot.get_chat_member(message.chat.id, user_id).user
            name = user.first_name
        except:
            name = "Unknown"
        leaderboard += f"{idx}. {name} - {score} points\n"
    bot.send_message(message.chat.id, leaderboard)

bot.infinity_polling()