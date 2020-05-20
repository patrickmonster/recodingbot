import os
import threading
import recodingbot
from chatbot import TwitchWSS

def end():
    pass

target = "first_7"
bot = recodingbot.Recodingbot("#"+target,loop=recodingbot.loop)
bot.run()