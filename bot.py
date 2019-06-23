from PIL import Image
from io import BytesIO
import time
import random
import os
import requests
import re

# Это изменненный мной файл neural_style.py, а точнее его функция stylize
from bot_utils.my_style import stylize
# Импортируем токен бота
from bot_utils.telegram_token import token_my
#Импортируем нейросеточку для переноса стиля с любой картинки(но в плохом качестве + медленно)
from bot_utils.neural_style_with_your_image import run_style_transfer
# Импортируем файл, в котором все ответы бота
import bot_utils.config

# Эта переменная необходима, чтобы запомнить выбор стиля пользователя
answer = str()
# Нашему боту надо будет запомнить картинку для веселья )
first_image_file = {}
def fun(bot, update):
    # Это против некоторых ситуаций, когда пользователь до этого выбрал картинку стиля и перезапустил
    global first_image_file
    first_image_file = {}
    # Это против написанной до этого цифры
    global answer
    answer = ''
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.fun_1 )
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.fun_2)
    
def send_prediction(bot, update):
    # Нам нужно получить две картинки, чтобы произвести перенос стиля, но каждая картинка приходит в
    # отдельном апдейте, поэтому в простейшем случае мы будем сохранять id первой картинки в память,
    # чтобы, когда уже придет вторая, мы могли загрузить в память уже сами картинки и обработать их.
    chat_id = update.message.chat_id
    print("Изображение получено от {}".format(chat_id))
    
    # получаем информацию о картинке
    image_info = update.message.photo[-1]
    image_file = bot.get_file(image_info)

    if chat_id in first_image_file:

        # первая картинка, которая к нам пришла станет content image, а вторая style image
        content_image_stream = BytesIO()
        first_image_file[chat_id].download(out=content_image_stream)
        del first_image_file[chat_id]

        style_image_stream = BytesIO()
        image_file.download(out=style_image_stream)
        
        bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.fun_go)
        output = run_style_transfer(bot, update, content_image_stream, style_image_stream)
        bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.fun_done)
    else:
        first_image_file[chat_id] = image_file
        bot.send_message(chat_id=chat_id, text=bot_utils.config.fun_3)
    
# Команда, с которой бот будет нас приветствовать
def startCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.startCommand_1)
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.startCommand_2)
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.startCommand_3)

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
    print(answer)
    return answer
  
# Отправка предсказания на фотографию
def send_stylized_image(bot, update):
    # Мы получаем картинку контента и должны использовать выбранный пользователем стиль
    chat_id = update.message.chat_id
    print(chat_id)
    print("Got image from {}".format(chat_id))
    style = ['candy.pth','mosaic.pth','rain_princess.pth','udnie.pth', 'AbstractPicasso.model', 'Whist.model', 'Futurism.model', 'Anime.model', 'Error.model']
    # получаем информацию о картинке
    image_i = update.message.photo[-1]
    image = bot.get_file(image_i)

    # Подаем картинку нашей нейросети
    content_image_stream = BytesIO()
    image.download(out=content_image_stream)
    bot.send_message(chat_id=update.message.chat_id, text=bot_utils.config.send_magic_photo)
    output = stylize(content_image_stream, 'models/'+ style[answer - 1])
    
    # теперь отправим назад фото
    output_stream = BytesIO()
    output.save(output_stream, format='PNG')
    output_stream.seek(0)
    bot.send_photo(chat_id, photo=output_stream)
    print("Sent Photo to user")

def bark(bot, update):
    allowed_extension = ['jpg','jpeg','png']
    file_extension = ''
    while file_extension not in allowed_extension:
        contents = requests.get('https://random.dog/woof.json').json()
        url = contents['url']
        file_extension = re.search("([^.]*)$",url).group(1).lower()
    chat_id = update.message.chat_id
    bot.send_photo(chat_id=chat_id, photo=url)

if __name__ == '__main__':
    from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
    from telegram.ext import BaseFilter
    import logging
    # Включим самый базовый логгинг, чтобы видеть сообщения об ошибках
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
    updater = Updater(token=token_my)
    #
    # # Эта вещь очень опциональная, если не хотите, чтобы после каждого запуска удалялся token.py, то закоментите (или удалите)
    # # Мне было нужно, чтобы с гугл диска запускать успешно )
    if os.path.isfile("bot_utils/telegram_token.py")== True:
        os.remove("bot_utils/telegram_token.py")

    # #   
    # Создадим новый фильтр, чтобы бот понимал, что от него требуют
    class FilterAnswer(BaseFilter):
          def filter(self, message):
              global answer
              message = answer
              print(message)
              return (message == 0) or (message == 1) or (message == 2) or (message == 3) or (message == 4) or (message == 5) or (message == 6) or (message == 7) or (message == 8) or (message == 9)

    filter_answer = FilterAnswer()

    # Отдаем наши функции диспатчеру
    updater.dispatcher.add_handler(MessageHandler(Filters.photo & filter_answer, send_stylized_image))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo & (~filter_answer), send_prediction))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, text))
    updater.dispatcher.add_handler(CommandHandler('start', startCommand))
    updater.dispatcher.add_handler(CommandHandler('style', style))
    updater.dispatcher.add_handler(CommandHandler('fun', fun))
    updater.dispatcher.add_handler(CommandHandler('bark', bark))
    updater.start_polling()
