import os
import subprocess 

if os.path.isfile("bot_utils/telegram_token.py")== True:
    os.remove("bot_utils/telegram_token.py")
f = open("bot_utils/telegram_token.py", 'x')
print('Введите токен вашего бота:')
answer = input()
f.write("token_my =  '%s'" % (str(answer)))
f.close()

subprocess.Popen('bot.py')
