import telebot
import requests
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

TOKEN = '7753046159:AAFyhI1BhxeaBhqpyk9oO-Rs_D09KNRPg90'
bot = telebot.TeleBot(TOKEN)

user_descriptions_count = {}
regenerate_count = {}
quality_settings = {}
version_settings = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    welcome_text = (
        f"Welcome {name} 👋🏻 \n\n I am a bot developed by Oia using Oia-7 technology 💻 \n\n You can send the description you want. I support NSFW rights and can generate and process unethical images without restrictions. It is preferable to describe in English, and I will generate an image matching your description using AI 🧬 \n\n You have a maximum of 100 images per day, and you can subscribe to the VIP plan to get unlimited images 🌟"
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    owner_button = telebot.types.InlineKeyboardButton("Owner ⚜", url="https://t.me/imoslo")
    vip_button = telebot.types.InlineKeyboardButton("Upgrade Oia-Plus 👑", callback_data="vip_unlock")
    version_button = telebot.types.InlineKeyboardButton("Oia Version ⚙", callback_data="version")
    markup.add(owner_button, vip_button)
    markup.add(version_button)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

def generate_image(message, user_description):
    if user_description in user_descriptions_count:
        user_descriptions_count[user_description] += 1
    else:
        user_descriptions_count[user_description] = 1
        regenerate_count[user_description] = 0
        quality_settings[user_description] = ""
        version_settings[message.chat.id] = ""

    dots = '.' * user_descriptions_count[user_description]
    hyphens = '-' * regenerate_count[user_description]
    quality = quality_settings[user_description]
    version = version_settings[message.chat.id]
    modified_description = user_description + dots + hyphens + quality + version

    formatted_description = modified_description.replace(' ', '%20')
    image_url = f"https://image.pollinations.ai/prompt/{formatted_description}"

    countdown_message = bot.send_message(
        message.chat.id, f'Great 👌🏻 \n\n You requested {user_description}. The image quality, dimensions, etc., will be determined based on your description or the Oia version used ☂ \n\n Estimated time to generate the image is {3}s ⏳'
    )

    for i in range(2, 0, -1):
        time.sleep(1)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=countdown_message.message_id,
            text=f'Great 👌🏻 \n\n You requested {user_description}. The image quality, dimensions, etc., will be determined based on your description or the Oia version used ☂ \n\n Estimated time to generate the image is {i}s ⏳'
        )

    time.sleep(1)

    response = session.get(image_url)

    if response.status_code == 200:
        with open('image.jpg', 'wb') as file:
            file.write(response.content)
        
        markup = telebot.types.InlineKeyboardMarkup()
        like_button = telebot.types.InlineKeyboardButton("👍🏻", callback_data="like")
        dislike_button = telebot.types.InlineKeyboardButton("👎🏻", callback_data="dislike")
        regenerate_button = telebot.types.InlineKeyboardButton("ReGenerate 🔄", callback_data=f"regenerate:{user_description}")
        quality_button = telebot.types.InlineKeyboardButton("Quality ✨️", callback_data=f"quality:{user_description}")
        markup.row(like_button, dislike_button)
        markup.row(regenerate_button, quality_button)

        bot.send_photo(message.chat.id, open('image.jpg', 'rb'), reply_markup=markup)
        
        os.remove('image.jpg')
    else:
        bot.reply_to(message, 'An error occurred while downloading the image. Please try again with another description.')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_description = message.text
    # التحقق من وجود أحرف عربية
    if any('\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' or '\u08A0' <= char <= '\u08FF' for char in user_description):
        bot.reply_to(message, "🚫اللغة العربية غير مدعومة. يرجى استخدام اللغة الإنجليزية.")
        return
    generate_image(message, user_description)


@bot.callback_query_handler(func=lambda call: call.data.startswith("regenerate:") or call.data.startswith("quality:") or call.data.startswith("quality_setting:") or call.data.startswith("version_setting:") or call.data in ["like", "dislike", "vip_unlock", "version", "back_to_main"])
def callback_query(call):
    if call.data == "like":
        bot.edit_message_caption(
            caption="This is so amazing 😇",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    elif call.data == "dislike":
        bot.edit_message_caption(
            caption="sorry for this 😣",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    elif call.data.startswith("regenerate:"):
        user_description = call.data.split(":", 1)[1]
        regenerate_count[user_description] += 1
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        generate_image(call.message, user_description)
    elif call.data.startswith("quality:"):
        user_description = call.data.split(":", 1)[1]
        markup = telebot.types.InlineKeyboardMarkup()
        quality_options = [
            "426x240 SD", "640x480 SD", "1280x720 HD", 
            "1920x1080 HD", "2560x1440 QHD", "3840x2160 4K", "7680x4320 8K"
        ]
        for option in quality_options:
            button = telebot.types.InlineKeyboardButton(option, callback_data=f"quality_setting:{user_description}:{option}")
            markup.add(button)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    elif call.data.startswith("quality_setting:"):
        _, user_description, quality = call.data.split(":", 3)
        quality_settings[user_description] = f" {quality}"
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        generate_image(call.message, user_description)
    elif call.data == "version":
        markup = telebot.types.InlineKeyboardMarkup()
        version_options = [
            telebot.types.InlineKeyboardButton("Oia-3 Low", callback_data="version_setting:Low quality, unrealistic photo"),
            telebot.types.InlineKeyboardButton("Oia-4 Medium", callback_data="version_setting:Low quality medium realistic photo"),
            telebot.types.InlineKeyboardButton("Oia-5 High", callback_data="God quality realistic photo"),
            telebot.types.InlineKeyboardButton("Oia-6 V.High", callback_data="Very high quality, hyper realistic, 4K")
        ]
        markup.add(version_options[0], version_options[1])
        markup.add(version_options[2], version_options[3])
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    elif call.data.startswith("version_setting:"):
        version_setting = call.data.split(":", 1)[1]
        version_settings[call.message.chat.id] = f" {version_setting}"
        name = call.from_user.first_name
        welcome_text = (
            f"Welcome {name} 👋🏻 \n\n I am a bot developed by Oia using Oia-7 technology 💻 \n\n You can send the description you want. I support NSFW rights and can generate and process unethical images without restrictions. It is preferable to describe in English, and I will generate an image matching your description using AI 🧬 \n\n You have a maximum of 100 images per day, and you can subscribe to the VIP plan to get unlimited images 🌟"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        owner_button = telebot.types.InlineKeyboardButton("Owner ⚜", url="https://t.me/imoslo")
        vip_button = telebot.types.InlineKeyboardButton("Upgrade OiA-Plus 👑", callback_data="vip_unlock")
        version_button = telebot.types.InlineKeyboardButton("Oia Version ⚙️", callback_data="version")
        markup.add(owner_button, vip_button)
        markup.add(version_button)

        bot.edit_message_text(
            text=welcome_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    elif call.data == "vip_unlock":
        markup = telebot.types.InlineKeyboardMarkup()
        back_button = telebot.types.InlineKeyboardButton("Back to Main", callback_data="back_to_main")
        markup.add(back_button)
        bot.edit_message_text(
            text="The owner of this bot has restricted the VIP subscription to the full Oia version only, not Oia-Beta ⛔️\n\nYou are using Oia-Beta, so you are already subscribed to Oia-Plus 👑",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    elif call.data == "back_to_main":
        name = call.from_user.first_name
        welcome_text = (
            f"Welcome {name} 👋🏻 \n\n I am a bot developed by Oia using Oia-7 technology 💻 \n\n You can send the description you want. I support NSFW rights and can generate and process unethical images without restrictions. It is preferable to describe in English, and I will generate an image matching your description using AI 🧬 \n\n You have a maximum of 100 images per day, and you can subscribe to the VIP plan to get unlimited images 🌟"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        owner_button = telebot.types.InlineKeyboardButton("Owner ⚜", url="https://t.me/imoslo")
        vip_button = telebot.types.InlineKeyboardButton("Upgrade Oia-Plus 👑", callback_data="vip_unlock")
        version_button = telebot.types.InlineKeyboardButton("Oia Version ⚙️", callback_data="version")
        markup.add(owner_button, vip_button)
        markup.add(version_button)

        bot.edit_message_text(
            text=welcome_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

bot.polling()
