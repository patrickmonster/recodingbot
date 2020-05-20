import os, sys
import threading
import recodingbot
from chatbot import TwitchWSS

# http 서버
import http.server
from urllib.parse import urlparse

def end():
    pass

if len(sys.argv) <= 1:
    print("아규먼트 부족!")
    exit()
target = sys.argv[1]
bot = recodingbot.Recodingbot("#"+target,loop=recodingbot.loop)
bot.run()

# class BotWebPage(http.server.BaseHTTPRequestHandler):
#     def do_GET(self):
#         parsed_path=urlparse(self.path)
#         if parsed_path.path == '/':
#             pass
#         elif 
# if not sys.argv[2]:
#     sys.argv[2] = "1025"
# server=http.server.HTTPServer(("",int(sys.argv[2])),BotWebPage)