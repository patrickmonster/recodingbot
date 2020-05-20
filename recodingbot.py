import os
import sys
import time
import json
import gc
import threading
from datetime import datetime
from chatbot import TwitchWSS

isSave = False

isRun = True


def convert_time(s):
    if s <= 0:
        return "방송중이 아닙니다!"
    if s <= 60*60:
        return time.strftime("%M분%S초", time.gmtime(s))
    return time.strftime("%H시%M분%S초", time.gmtime(s))

class DataFile(dict):
    def __init__(self,dir):
        self.dir = dir
        if os.path.isfile(dir):
            self.load()
        else:
            self.save()

    # def __getattr__(self, name):
    #     return self[name]

    # def __setattr__(self, name, value):
    #     self[name] = value
    
    def save(self):
        try:
            with open(self.dir, "w") as json_file:
                json.dump(self, json_file)
            print("저장됨! - " + self.dir)
        except:
            print("저장에 실패하였습니다! -" + self.dir)
            return False
        return True
    
    def load(self):
        try:
            with open(self.dir, "r", encoding='UTF8') as st_json:
                data = json.load(st_json)
                for i in data:
                    self[i] = data[i]
            print("불러오기 성공!")
        except:
            print("불러오기에 실패함!")
            return False
        return True

    def add(self,name,data):
        self[name] = data
        return self
class Chatting(list):
    def __init__(self,dir,count = 1,extension=".chat",write_size=5000):
        self.dir = dir
        self.count = count
        self.extension = extension
        self.write_size = write_size

    def append(self, value):
        if len(self) >= self.write_size:
            self.save()
            self.clear()
        super().append(value)
    
    def pop(self):
        if len(self) <= 0:
            return -1
        return super().pop()
    
    def save(self):
        try:
            acess = "a"
            if not os.path.isfile(self.dir+str(self.count) +self.extension):
                acess = "w"
            with open(self.dir+str(self.count) +self.extension, acess, encoding='UTF8') as file:
                while len(self) > 0: # 시간 메세지아이디 유저아이디 유저이름
                    file.write(self.pop())
                    # file.write(f'{i["tmi-sent-ts"]}\t{i["id"]} {i["user-id"]}\t{i["display-name"]}({i["user-name"]})\t\t:{i["message"]}\r\n')
            print("채팅이 저장됨! - " + self.dir)
            self.count += 1
        except Exception as e:
            print("채팅 저장에 실패하였습니다! - ", e)
            return False
        return True
        

class Recodingbot(TwitchWSS):
    def __init__(self,channel,loop=None,on_end=None):
        super().__init__('recodingbot','q4nxdhnv8gxnpg4r6dl02deeubabnz',
            channel,'gza456joczze4p3ltn6wqi385l10vk',Recodingbot.get_message,on_sys_command=Recodingbot.get_sys_cmd)
        
        self.setDir()
        self.oncommand = Recodingbot.get_command
        self.on_end = on_end
        self.isRun = True
        self.isOnce = False
        if loop:
            self.notice = threading.Thread(target=loop, args=(self,))

    def __del__(self): # 모든 데이터 저장
        if self.on_end:
            self.on_end()
        self.isRun = False

    def run(self):
        if self.notice:
            self.notice.start() # 정기 알림용 스레드 동작
        super().run()
        

    def setDir(self):
        t = os.getcwd() + "/" + self.channel[1:]
        self.chat_dir = t + "/chatting/"
        self.config_user_file = t + "/user.config"
        self.command_file = t + "/commands/"
        self.config = t + "/options.config"
        if not os.path.isfile(self.config):
            os.mkdir(os.getcwd() + "/" + self.channel[1:])
            os.mkdir(self.chat_dir)
            os.mkdir(self.command_file)
            self.config_option=DataFile(self.config)
            self.config_option.add("words",{}).add("nicks",{}).add("auto",{})
            print(f'신규사용자 - {self.channel}님을 생성하였습니다!')
        else:
            self.config_option=DataFile(self.config)
        self.chatting = Chatting(self.chat_dir + datetime.now().strftime('%Y_%m_%d'),write_size=10000)
        self.command_log = Chatting(self.command_file + datetime.now().strftime('%Y_%m_%d'),extension=".log")
        self.config_user = DataFile(self.config_user_file)

    def onClose(self):
        self.isRun = False
        if not self.isOnce:
            self.isOnce = True
            self.chatting.save()
            self.config_user.save()
            self.config_option.save()
            self.command_log.save()
        super().onClose()

    def user_ban(self,user,msg_id,message=""):
        self.sendMessage(f'/ban {user}')
        self.command_log.append(f'{datetime.now().strftime("%Y/%m/%d %H:%M")}\t[ban]\t{user} {msg_id} [{message}]\r\n')
        print("ban user",user,msg_id,message)

    def user_timeout(self,user,msg_id,time,message=""):
        self.sendMessage(f'/timout {user} {time}')
        self.command_log.append(f'{datetime.now().strftime("%Y/%m/%d %H:%M")}\t[timeout]\t{user} {time} {msg_id} [{message}]\r\n')
        print("timeout user",user,msg_id,time,message)

    def user_message_delete(self,user,msg_id,message=""):
        self.sendMessage(f'/delete {msg_id}')
        self.command_log.append(f'{datetime.now().strftime("%Y/%m/%d %H:%M")}\t[del message]\t{user} {msg_id} [{message}]\r\n')
        print("delete Message",user,msg_id,message)

    def get_sys_cmd(self,data):
        print(data["command"],data["message"])

    def get_message(self,data,message):
        try:
            self.chatting.append(f'{data["tmi-sent-ts"]}\t{data["id"]}\t{data["user-id"]}\t{data["display-name"]}({data["user-name"]})\t\t:{data["message"]}\r\n')
        except Exception as e:
            print(e)
        print(data['display-name']+" :",data['message'])
        for i in self.config_option["words"].keys():
            if message.find(i) != -1:
                j = data["user-type"].find("!")
                if self.config_option["words"][i]:
                    self.user_message_delete(data["user-type"][2:j],data["id"],self.config_option["words"][i])
                    self.sendMessage(self.config_option["words"][i])
                else :
                    self.user_message_delete(data["user-type"][2:j],data["id"])
                break
        try:
            if data["user-name"] not in self.config_user:
                self.config_user[data["user-name"]] = {"user-id":data["user-id"],"display-name":data["display-name"]}
        except Exception as e:
            print(e)
        self.command_message(data,message) # 추가 명령처리
        for i in self.config_option["nicks"]:
            if data["display-name"].find(i) != -1:
                j = data["user-type"].find("!")
                self.user_ban(data["user-type"][2:j],"0","부적절한 닉네임" + data["display-name"])
                if self.config_option["words"][i]:
                    self.sendMessage(self.config_option["words"][i])
                break

    def command_message(self,data,message):
        msg = message.split(" ")[0]
        for i in self.config_option["auto"].keys():
            if msg.find(i) != -1: 
                self.sendMessage(self.config_option["auto"][i].replace("{user}",data['display-name']).replace("{id}",data["user-name"]).replace("{channel}",self.channel))
                break
        # if msg in self.config_option["auto"]:
        #     self.sendMessage(self.config_option["auto"][msg].replace("{user}",data['display-name']).replace("{id}",data["user-name"]).replace("{channel}",self.channel))
    
    # 기본 명령어 처리
    def get_command(self,data,message):
        global isRun
        self.command_message(data,"!"+message)
        print("명령어!" + message)
        msg = message.split()
        if msg[0] == "방송":
            self.sendMessage("방송시간:" + convert_time(self.get_stream_running_s()))
        elif msg[0] == "레봇":
            self.sendMessage("현재[" + self.channel+"]님 채팅 서버에서 가동중입니다! 주로 채팅을 제어하거나 필터링 및 모니터링 합니다! - 기타문의 : 쪽지")
        # elif msg[0] == "팔로우":
        #     d = self.get_api_request("helix/users/follows?to_id" + data['user-id'],{
        #         # 'Client-ID': self.client_id,"Authorization" : 'OAuth ' + self.passwd
        #         'Client-ID': self.client_id,'Authorization' : 'Bearer ' + self.passwd.split(':')[1]
        #     })
        #     print({
        #         # 'Client-ID': self.client_id,"Authorization" : 'OAuth ' + self.passwd
        #         'Client-ID': self.client_id,"Authorization" : 'Bearer ' + self.passwd.split(':')[1]
        #     })
            # print(d)
            # d = self.get_api_request("kraken/users/" + data['user-id'] + "/follows/channels")
            # isFound = False
            # for i in d['follows']:
            #     if i['channel']['name'] in self.channel:
            #         d = i['created_at']
            #         isFound = True
            #         break
            # if not isFound:
            #     self.sendMessage(f'{data["display-name"]}님은 아직 팔로우를 하지 않았습니다!')
            # else:
            #     self.sendMessage(f'{data["display-name"]}님은 {d[:d.find("T")]}일 부터 팔로우 중입니다!')
        elif msg[0] == "명령어":
            try:
                self.sendMessage("/me 명령어["+",".join(self.config_option["auto"].keys()) +"]")
            except Exception as e:
                print(e)
        else : # 커맨드 명령
            if data["user-id"] == "129955642" or data["badges"].find("broadcaster") != -1 or data["badges"].find("mod") != -1:
                self.command_log.append(f'{datetime.now().strftime("%Y/%m/%d %H:%M")}\t{data["user-name"]}({data["display-name"]}): {" ".join(msg)}\r\n')
                self.commands(msg,isComsole=False)
    
    # 관리자 명령
    def commands(self, comm, isComsole=False):
        try:
            if comm[0] == "레봇안녕":
                print("서버가 종료됨...")
                self.sendMessage("레봇이 ["+self.channel+"]님의 채널을 떠납니다! 안뇽~")
                self.onClose()
            elif comm[0] == "알림":
                if len(comm) < 3:
                    if isComsole:
                        print(self.config_option["time"])
                    else :
                        self.sendMessage("설정된 알림 : " + str(self.config_option["time"]))
                else:
                    self.config_option["time"] = {"message":" ".join(comm[2:]),"time":60 * (int(comm[1]))} # time 은 s단위
                    print(self.config_option["time"],end="로 설정됨!\n")
            elif comm[0] == "저장":
                self.chatting.save()
                self.config_user.save()
                self.config_option.save()
                self.command_log.save()
                self.sendMessage("/me 데이터 저장됨")
            elif comm[0] == "추가":
                if len(comm) < 2:
                    if isComsole:
                        print("올바르지 않은 문장입니다! [!추가 명령 채팅값]")
                    else :
                        self.sendMessage("/me 올바르지 않은 문장입니다! [!추가 명령 채팅값]")
                else:
                    self.config_option["auto"][comm[1]] = " ".join(comm[2:])
                    if isComsole:
                        print(f'명령이 추가됨! :{comm[1]}')
                    else:
                        self.sendMessage(f'명령이 추가됨! {comm[1]}')
            elif comm[0] == "금지어":
                if len(comm) < 2:
                    if isComsole:
                        print(",".join(self.config_option["words"].keys()), end="]금지어\n")
                    else :
                        self.sendMessage("/me 금지어 목록[" + ",".join(self.config_option["words"].keys()) + "]")
                else:
                    self.config_option["words"][comm[1]] = " ".join(comm[2:])
                    if isComsole:
                        print("금지어 추가됨!")
                    else:
                        self.sendMessage("금지어 추가됨!")
            elif comm[0] == "제거":
                if comm[1] == "닉":
                    if len(comm) < 3:
                        print(",".join(self.config_option["nicks"]), end="]금지닉네임\n")
                    else:
                        i = self.config_option["nicks"].index(comm[2])
                        if i == -1:
                            return
                        self.config_option["nicks"].pop(i)
                        if isComsole:
                            print("금지 닉네임 제거됨!")
                        else:
                            self.sendMessage("금지 닉네임 제거됨!")
                elif comm[1] == "어":
                    if len(comm) < 3:
                        print(",".join(self.config_option["words"]), end="]금지닉네임\n")
                    else:
                        del self.config_option["words"][comm[2]]
                        if isComsole:
                            print("금지어 제거됨!")
                        else:
                            self.sendMessage("금지어 제거됨!")
                else:
                    if len(comm) < 2:
                        if isComsole:
                            print("올바르지 않은 문장입니다! [!제거 명령]")
                        else :
                            self.sendMessage("올바르지 않은 문장입니다! [!제거 명령]")
                    else:
                        if not comm[1] in self.config_option["auto"]:
                            if isComsole:
                                print("명령이 없습니다!")
                            else:
                                self.sendMessage("명령이 없습니다!")
                        else :
                            del self.config_option["auto"][comm[1]]
                            if isComsole:
                                print("명령 제거됨!" + comm[1])
                            else:
                                self.sendMessage("명령 제거됨!" + comm[1])
            elif comm[0] == "금지닉":
                if len(comm) < 2:
                    if isComsole:
                        print(",".join(self.config_option["nicks"]), end="]금지닉네임\n")
                    else :
                        self.sendMessage("/me 금지닉["+",".join(self.config_option["nicks"]) +"]")
                else:
                    self.config_option["nicks"].append(comm[1])
                    print("금지 닉네임 추가됨!")
            elif comm[0] == "명령어":
                try:
                    print("명령어["+",".join(self.config_option["auto"].keys()) +"]")
                except Exception as e:
                    print(e)
            elif comm[0] == "뷰봇":
                if len(comm) < 2:
                    if isComsole:
                        print("최근 채팅중, 불건전한 채팅을 검색하여 모두 벤 하는 기능입니다 [!뷰봇 검색채팅]")
                    else :
                        self.sendMessage("/me 금지닉["+",".join(self.config_option["nicks"]) +"]")
                print("뷰봇 클리너 동작... 검색단어 :" + comm[1])
                if not isComsole:
                    self.sendMessage("뷰봇 클리너 동작... 검색단어 :" + comm[1])
                users = []
                for i in self.chatting:
                    chat = i.split("\t")
                    if chat[3] in users:
                        continue
                    if chat[5].find(comm[1]) != -1 :
                        users.append(chat[3])
                        self.user_ban(chat[3].split("(")[1][:-1],chat[2],f'뷰봇 벤 처리 {comm[1]}')
                print(f'뷰봇 클리너 동작완료!... 사용자 {str(len(users))} 명을 찾아 벤 하였습니다')
                print(",".join(users))
                if not isComsole:
                    self.sendMessage(f'뷰봇 클리너 동작완료!... 사용자 {str(len(users))} 명을 찾아 벤 하였습니다')
            elif comm[0] == "users":# 사용자
                print(",".join(self.config_user.keys()), len(self.config_user.keys()))
            elif comm[0] == "user":# 사용자 탐색
                if len(comm) < 2:
                    if isComsole:
                        print("사용자 검색 [!users 레봇]")
                        return
                    else :  
                        self.sendMessage("/me 사용자 검색 [!users 레봇]")
                users = list(map(lambda x: f'{self.config_user[x]["display-name"]}:{x}',list(filter(lambda x:self.config_user[x]["display-name"].find(comm[1])!=-1,self.config_user.keys()))))
                if isComsole:
                    if len(users) >= 0:
                        print(f'{",".join(users)} 총 {len(users)}명이 검색됨!')
                    else :
                        print("사용자를 찾을 수 없음!")
                else :
                    if len(users) >= 0:
                        self.sendMessage(f'{",".join(users)} 총 {len(users)}명이 검색됨!')
                    else :
                        self.sendMessage("사용자를 찾을 수 없음!")
        except Exception as e:
            print("명령처리에러 : ", e)

def loop(tw):
    start = time.time()
    if "time" not in tw.config_option:
        tw.config_option["time"] = {"message":"","time":60 * 5} # time 은 s단위
    # save_time = 60 * 10
    try:
        while tw.isRun:
            time.sleep(1)
            now =time.time() - start # 현재
            # if int(now % save_time) == 0: # 10분에 한번씩 채팅 저장
            #     save_chat()
            if int(now % tw.config_option["time"]["time"]) != 0:
                continue
            if tw.get_stream_running_s() <= 0:
                continue
            if tw.config_option["time"]["message"]:
                tw.sendMessage(tw.config_option["time"]["message"])
    except:
        pass

# 커맨드창 전용
def run(tw):
    try:
        while tw.isRun:
            comm = input().split(" ")
            if comm[0] == "exit":
                print("서버가 종료됨...")
                tw.onClose()
            elif comm[0] == "msg":
                msg=" ".join(comm[1:])
                tw.sendMessage(msg)
            elif comm[0] == "op":
                print(tw.config_option)
            elif comm[0] == "us":
                print(tw.config_user)
            else :
                tw.commands(comm,isComsole=True)
    finally:
        print("입력종료")

def end():
    pass

if __name__ == "__main__":
    target = input("enter to channel>")
    
    bot = Recodingbot("#"+target,loop=loop,on_end=end)
    t = threading.Thread(target=run,args=(bot,))
    t.start()# 입력 스레드
    bot.run()
