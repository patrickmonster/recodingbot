import os
import sys
import time
import json
import gc
import threading
from datetime import datetime
from chatbot import TwitchWSS


chat_dir = "/chatting/"
config = "/options.config"
config_user_file = "/user.config"
config_option = {"words":{},"nicks":[]} # 금지어 목록
config_user = {}
isSave = False

tw = []
chatting = []
messages = {
    "레봇":"현재 {channel}님 채팅 서버에서 가동중입니다! 주로 채팅을 제어하거나 필터링 및 모니터링 합니다!",
    "디코":"구미단! 어서와!  https://discord.gg/eP4ZQfD",
}
isRun = True

def convert_time(s):
    if s <= 0:
        return "방송중이 아닙니다!"
    if s <= 60*60:
        return time.strftime("%M분%S초", time.gmtime(s))
    return time.strftime("%H시%M분%S초", time.gmtime(s))

def get_message(ws,data,message):
    chatting.append(data)
    print(data['display-name']+" :",data['message'])
    for i in config_option["words"].keys():
        if message.find(i) != -1:#/delete
            ws.sendMessage("/delete "+ data["id"])
            print("메세지 삭제! - [" + i + "] 언급!")
            if config_option["words"][i]:
                ws.sendMessage(config_option["words"][i])
            break
    try:
        if data["user-name"] not in config_user:
            config_user[data["user-name"]] = {"user-id":data["user-id"],"display-name":data["display-name"]}
    except Exception as e:
        print(e)
    for i in config_option["nicks"]:
        if data["display-name"].find(i) != -1:
            j = data["user-type"].find("!")
            ws.sendMessage("/ban "+ data["user-type"][2:j])
            print("사용자 벤! - [" + i + "] 포함된 단어!")
            if config_option["words"][i]:
                ws.sendMessage(config_option["words"][i])
            break

def get_command(ws,data,message):
    global isRun
    msg = message.split()
    print("COMMAND",msg)
    if msg[0] == "방송":
        ws.sendMessage("방송시간:" + convert_time(ws.get_stream_running_s()))
    elif msg[0] == "레봇":
        # ws.sendMessage("/w "+ data["user-name"] +" 현재[" + ws.channel+"]님 채팅 서버에서 가동중입니다! 주로 채팅을 제어하거나 필터링 및 모니터링 합니다!")
        ws.sendMessage("현재[" + ws.channel+"]님 채팅 서버에서 가동중입니다! 주로 채팅을 제어하거나 필터링 및 모니터링 합니다!")
    elif msg[0] == "디코":
        ws.sendMessage("구미단! 어서와!  https://discord.gg/eP4ZQfD")
    elif msg[0] == "팔로우":
        d = ws.get_api_request("kraken/users/" + data['user-id'] + "/follows/channels")
        for i in d['follows']:
            if i['channel']['name'] in ws.channel:
                d = i['created_at']
                break
        d = d[:d.find("T")]
        try:
            print(data['display-name'] + "님은 " + d + "일 부터 팔로우중...")
            ws.sendMessage(data['display-name'] + "님은 " + d + "일 부터 팔로우중입니다.")
        except :
            ws.sendMessage(data['display-name'] + "님은 아직 팔로우를 하지 않았습니다!")
    else :
        if data["user-id"] == "129955642" or data["badges"].find("broadcaster") != -1 or data["badges"].find("mod") != -1:
            if msg[0] == "레봇안녕":
                print("서버가 종료됨..." + data['display-name'])
                ws.sendMessage("레봇이 ["+ws.channel+"]님의 채널을 떠납니다! 안뇽~")
                tw.onClose()
                isRun = False
            else:
                command(msg,isComsole=False)

def get_join(ws,message):
    print(message)

def get_closed(ws):
    global isSave
    try:
        ws.close()
    except Exception as e:
        print(e)
    if not isSave:
        save_config()
        save_config_user()
        isSave = True

def save_config():
    global config_option,config
    try:
        with open(config, "w") as json_file:
            json.dump(config_option, json_file)
        print("저장됨!")
    except:
        print("저장에 실패하였습니다!")
        return False
    return True

def load_config():
    global config_option,config
    try:
        with open(config, "r") as st_json:
            config_option = json.load(st_json)
        print("불러오기 성공!")
    except:
        print("불러오기에 실패함!")
        return False
    return True

def save_config_user():
    global config_user_file,config_user
    try:
        with open(config_user_file, "w") as json_file:
            json.dump(config_user, json_file)
        print("사용자 저장됨!")
    except:
        print("사용자 저장에 실패하였습니다!")
        return False
    return True

def load_config_user():
    global config_user_file,config_user
    try:
        with open(config_user_file, "r") as st_json:
            config_user = json.load(st_json)
        print("사용자 불러오기 성공!")
    except:
        print("사용자 불러오기에 실패함!")
        return False
    return True

def get_sys_command(ws,data):
    print("System cmd :",data)

def run():
    global isRun, chatting, tw, config_option
    while isRun:
        comm = input().split(" ")
        if comm[0] == "exit":
            print("서버가 종료됨...")
            tw.onClose()
            isRun = False
        elif comm[0] == "msg":# 채팅내용 저장
            msg=" ".join(comm[1:])
            tw.sendMessage(msg)
        elif comm[0] == "op":# 채팅내용 저장
            print(config_option)
        elif comm[0] == "us":# 채팅내용 저장
            print(config_user)
        else :
            command(comm,isComsole=True)

def command(comm, isComsole=False):
    global tw, config_user, config_option
    try:
        if comm[0] == "알림":
            if len(comm) < 3:
                if isComsole:
                    print(config_option["time"])
                else :
                    tw.sendMessage("설정된 알림 : " + str(config_option["time"]))
                # print("최소 3자리 [t time message]")
            else:
                config_option["time"] = {"message":" ".join(comm[2:]),"time":60 * (int(comm[1]))} # time 은 s단위
                print(config_option["time"],end="로 설정됨!\n")
        elif comm[0] == "금지어":
            if len(comm) < 2:
                if isComsole:
                    print(",".join(config_option["words"].keys()), end="]금지어\n")
                else :
                    tw.sendMessage("/me 금지어 목록[" + ",".join(config_option["words"].keys()) + "]")
            else:
                config_option["words"][comm[1]] = " ".join(comm[2:])
                if isComsole:
                    print("금지어 추가됨!")
                else:
                    tw.sendMessage("금지어 추가됨!")
        elif comm[0] == "제거":
            if comm[1] == "닉":
                if len(comm) < 3:
                    print(",".join(config_option["nicks"]), end="]금지닉네임\n")
                else:
                    i = config_option["nicks"].index(comm[2])
                    if i == -1:
                        return
                    config_option["nicks"].pop(i)
                    if isComsole:
                        print("금지 닉네임 제거됨!")
                    else:
                        tw.sendMessage("금지 닉네임 제거됨!")
            else:
                if len(comm) < 2:
                    if isComsole:
                        print(",".join(config_option["words"].keys()), end="]금지어\n")
                    else :
                        tw.sendMessage("/me 금지어["+",".join(config_option["words"].keys()) +"]")
                else:
                    del config_option["words"][comm[1]]
                    if isComsole:
                        print("금지어 제거됨!")
                    else:
                        tw.sendMessage("금지어 제거됨!")
        elif comm[0] == "금지닉":
            if len(comm) < 2:
                if isComsole:
                    print(",".join(config_option["nicks"]), end="]금지닉네임\n")
                else :
                    tw.sendMessage("/me 금지닉["+",".join(config_option["nicks"]) +"]")
            else:
                config_option["nicks"].append(comm[1])
                print("금지 닉네임 추가됨!")
        elif comm[0] == "뷰봇":
            print("뷰봇 클리너 동작... 검색단어 :" + comm[1])
            if not isComsole:
                tw.sendMessage("뷰봇 클리너 동작... 검색단어 :" + comm[1])
            users = {}
            for i in chatting:
                if i["user-name"] in users:
                    continue 
                if i["message"].find(comm[1]) != -1:
                    users[i["user-name"]] = (i["user-id"],i["display-name"])
                    # print("사용자 " + i["user-name"])
                    tw.sendMessage("/ban " + i["user-name"])
            print("뷰봇 클리너 동작완료!... 사용자" + str(len(users.keys())) + "명을 찾아 벤 하였습니다")
            print(users.keys())
            if not isComsole:
                tw.sendMessage("뷰봇 클리너 동작완료!... 사용자" + str(len(users.keys())) + "명을 찾아 벤 하였습니다")
        elif comm[0] == "save":# 채팅내용 저장
            save_chat()
        elif comm[0] == "users":# 사용자
            print(",".join(config_user.keys()), len(config_user.keys()))
        elif comm[0] == "user":
            isFound = False
            for i in config_user.keys():
                user = config_user[i]
                if user["display-name"].find(comm[1]) != -1:
                    isFound = True
                    if isComsole:
                        print(user["display-name"] + " : " + i + "(" + user["user-id"] + ")")
                    else :
                        tw.sendMessage(user["display-name"] + "] " + i + "(" + user["user-id"] + ")")
                    break
            if not isFound:
                if isComsole:
                    print("사용자를 찾을 수 없음!")
                else :
                    tw.sendMessage("사용자를 찾을 수 없음!")

    except Exception as e:
        print("에러 : ", e)

def save_chat():
    global chatting
    if not len(chatting):
        return
    print("채팅 저장중...")
    with open(chat_dir +  "/chat_" + str(time.time())+".chat", "w") as json_file:
        json.dump(chatting, json_file)
    chatting = []
    print("채팅 저장됨!")

# 정기 알림 메세지
def message():
    global isRun
    start = time.time()
    if "time" not in config_option.keys():
        config_option["time"] = {"message":"테스트 메세지 입니다","time":60 * 5} # time 은 s단위
    save_time = 60 * 10
    try:
        while isRun:
            time.sleep(1)
            now =time.time() - start # 현재
            if int(now % save_time) == 0: # 10분에 한번씩 채팅 저장
                save_chat()
            if int(now % config_option["time"]["time"]) != 0:
                continue
            if tw.get_stream_running_s() <= 0:
                continue
            if config_option["time"]["message"]:
                tw.sendMessage(config_option["time"]["message"])
    except Exception as e:
        print(e)
    # print("타임 메세지 중지")
def init(target):
    global chat_dir,config_user_file, config
    chat_dir = os.getcwd() + "/" + target + chat_dir
    config_user_file = os.getcwd() + "/" + target + config_user_file
    config = os.getcwd() + "/" + target + config
    if not os.path.isfile(config):
        os.mkdir(os.getcwd() + "/" + target)
        os.mkdir(chat_dir)
    load_config()
    load_config_user()

if __name__ == "__main__":
    target = input("enter to channel>")
    init(target)
    t = threading.Thread(target=run)
    t.start()
    t1 = threading.Thread(target=message)
    t1.start()
    tw = TwitchWSS('wggm5zt40gfgffnzm5m3o3rgu1dfha','oauth:q4nxdhnv8gxnpg4r6dl02deeubabnz',
            "#"+config_option["channel"],on_message=get_message,on_command=get_command,
            on_sys_command=get_sys_command,onclose=get_closed,onJoin=get_join)
    tw.run()

