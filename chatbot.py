import time
import json
import requests
import websocket
'''
데이터 생성 규칙
tmi-sent-ts     // 서버에 메세지 전송된 시각
message         // 메세지


'''

import datetime

class TwitchWSS(websocket.WebSocketApp):

    def __init__(self,username,passwd,channel,client_id,on_message,on_command=None,command="!",onError=None,on_sys_command=None,onclose=None,onJoin=None):
        super().__init__("wss://irc-ws.chat.twitch.tv:443/",on_open=self.onOpen,on_message = self.onMessage,on_error = onError,on_close = self.onClose)
        self.username = username
        self.passwd = 'oauth:' + passwd
        self.channel = channel

        self.client_id = client_id

        self._message = on_message
        self.command = command
        self.oncommand = on_command
        self.onsyscommand = on_sys_command
        self.onclose = onclose
        self.onjoin = onJoin

        self.start_time = None
        print(self.passwd,self.username)
        
        self.header = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        
        self.streamer = self.get_api_request("kraken/users?login="+channel[1:])['users'][0]
        print("방송시간 :",self.convert_time(self.get_stream_running_s()))

    def convert_time(self,s):
        if s <= 0:
            return "방송중이 아닙니다!"
        return time.strftime("%H시%M분%S초", time.gmtime(s))

    def onError(self,message):
        print("Error",message)

    def onClose(self):
        try:
            self.close()
        except Exception as e:
            print(e)
        if self.onclose:# 기타처리
            self.onclose(self)
        print("### closed ###")

    def onOpen(self):
        print("Connect to " + self.channel)
        self.onSend("REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership","CAP")
        self.onSend(self.passwd,"PASS")
        self.onSend(self.username,"NICK")
        self.onSend(self.channel,"JOIN")
        # self.start_timev = time.strftime("%H시%M분", time.gmtime(s))

    def sendMessage(self, message):
        print("메세지 전송 : ",message)
        self.onSend(self.channel + " :" +str(message))

    def onSend(self,message ,option = 'PRIVMSG'):
        self.send(option + " " + message)

    def onMessage(self, message):
        if message == "":
            return
        messages = message.replace('\r','').split("\n")
        for data in messages:
            if data == "" or not data:
                continue
            data = self.parse_message(data)
            if data['command'] == "PRIVMSG":
                if data['message'][0] == self.command:
                    if self.oncommand:
                        print(self,data['message'][1:])
                        self.oncommand(self,data,data['message'][1:])
                else:
                    if self._message:
                        #print(data['display-name']+" :",data['message'])
                        self._message(self,data,data['message'])
            elif data['command'] == "PING":
                self.onSend(data['message'],"PONG")
            elif data['command'] == "JOIN":
                # print(data['message'])
                if self.onjoin:
                    self.onjoin(data['message'])
            else :
                if self.onsyscommand:# 기타처리
                    self.onsyscommand(data)

    def run(self):
        super().run_forever()

    def parse_message(self,rawMessage):# 구문분석
        parseMessage = {'message':'','command':''}
        if (rawMessage[0] == ':'):
            data = rawMessage.split()
            parseMessage['command'] = data[1]
            if (parseMessage['command'] == 'JOIN'):
                parseMessage['message'] = data[2]
            else :
                parseMessage['message'] = rawMessage
        elif rawMessage[:4] in ["PING"]:
            parseMessage['command'],parseMessage['message'] = rawMessage.split()
        else:
            data = rawMessage.split(";")
            for i in data:
                d = i.split("=")
                if i == '' or len(d) < 2:
                    continue
                parseMessage[d[0]] = d[1]
            if 'user-type' in parseMessage:
                user_type = parseMessage['user-type'].split()
                parseMessage["user-name"] = parseMessage["user-type"][parseMessage["user-type"].find(":")+1
                        :parseMessage["user-type"].find("!")]
                if "mod" in user_type[0]:
                    del user_type[0]
                    parseMessage['user-mod'] = True
                else :
                    parseMessage['user-mod'] = False
                parseMessage['user-connect'] = user_type[0]
                parseMessage['command'] = user_type[1]
                parseMessage['chatroom'] = user_type[2]
                parseMessage['message'] = " ".join(user_type[3:])[1:]
        return parseMessage
    
    def get_api_request(self,url,header=None):
        if not header:
            header = self.header
        return json.loads(requests.get("https://api.twitch.tv/"+url,headers=header).content.decode("UTF-8"))

    def get_stream_started(self):
        try:
            # 한국시 보정 + 10
            return datetime.datetime.strptime(self.get_api_request("helix/streams?user_id=" + self.streamer['_id'])['data'][0]['started_at'], '%Y-%m-%dT%H:%M:%SZ') + datetime.timedelta(hours=9)
        except :
            return datetime.datetime.now()
    
    def get_stream_running_s(self):
        return self.get_passing_time(self.get_stream_started()).seconds

    def get_passing_time(self,time):
        return datetime.datetime.now()  - time

if __name__ == "__main__":
    websocket.enableTrace(True)
    def onmsg(ws,data,msg):
        print(data['display-name'],":"+msg)
    tw = TwitchWSS('wggm5zt40gfgffnzm5m3o3rgu1dfha','ui88tjx9zn5ves0mt7q8rdevqbps8m','#kimdduddi',onmsg)
    tw.run()
