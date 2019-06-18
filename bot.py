from PIL import Image
from io import BytesIO
import time
import random
import os

# Это изменненный мной файл neural_style.py, а точнее его функция stylize
from bot_utils.my_style import stylize
# Импортируем токен бота
from bot_utils.telegram_token import token_my
# Импортируем файл, в котором все ответы бота
import bot_utils.config
# Эта переменная необходима, чтобы запомнить выбор стиля пользователя
answer = str()

# Команда, с которой бот будет нас приветствовать
def startCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.startCommand_1)
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.startCommand_2)

# Введя эту команду, пользователь получит возможность посмотреть все возможные стили для переноса
def style(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_0_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_0_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_1_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_1_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_2_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_2_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_3_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_3_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_4_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_4_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_5_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_5_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_6_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_6_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_7_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_7_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_8_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_8_photo)
    
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.style_9_text)
    bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.style_9_photo)
    
    
# Эта функция будет проверять каждое текстовое сообщение пользователя, цифра это в нужном диапозоне или нет.
def text(bot, update):
    global answer
    answer = update.message.text
    print(answer)
    if answer=='1' or answer=='2' or answer=='3' or answer=='4' or answer=='5' or answer=='6' or answer=='7' or answer=='8':
        answer = int(answer)
        bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.answer_1_8)
    elif answer=='9':
        answer = int(answer)
        bot.send_photo(chat_id=update.message.chat_id, photo=bot_utils.config.photo_9, caption=bot_utils.config.answer_9)
    elif answer=='0':
        answer = random.randint(1, 9)
        bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.answer_0_1 + str(answer) + bot_utils.config.answer_0_2)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.answer_other)
    return answer
  
# Отправка предсказания на фотографию
def send_prediction_on_photo(bot, update):
    # Мы получаем картинку контента и должны использовать выбранный пользователем стиль
    chat_id = update.message.chat_id
    print("Got image from {}".format(chat_id))
    style = ['candy.pth','mosaic.pth','rain_princess.pth','udnie.pth', 'AbstractPicasso.model', 'Futurism.model', 'Whist.model', 'Anime.model', 'Error.model']
    # получаем информацию о картинке
    image_info = update.message.photo[-1]
    image_file = bot.get_file(image_info)


    # Подаем картинку нашей нейросети
    content_image_stream = BytesIO()
    image_file.download(out=content_image_stream)
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.send_magic_photo)
    output = stylize(content_image_stream, 'models/'+ style[answer - 1])

    # теперь отправим назад фото
    output_stream = BytesIO()
    output.save(output_stream, format='PNG')
    output_stream.seek(0)
    bot.send_photo(chat_id, photo=output_stream)
    print("Sent Photo to user")

if __name__ == '__main__':
    from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
    import logging
    # Включим самый базовый логгинг, чтобы видеть сообщения об ошибках
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
    updater = Updater(token=token_my)
    if os.path.isfile("bot_utils/telegram_token.py")== True:
        os.remove("bot_utils/telegram_token.py")

    # Отдаем наши функции диспатчеру
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, send_prediction_on_photo))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, text))
    updater.dispatcher.add_handler(CommandHandler('start', startCommand))
    updater.dispatcher.add_handler(CommandHandler('style', style))
    updater.start_polling()
