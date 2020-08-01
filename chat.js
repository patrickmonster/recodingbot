const tmi = require('tmi.js');
const request = require('sync-request');
const fs = require('fs');
var config = require('./dbconfig');

!fs.existsSync("logger") && fs.mkdirSync("logger");
!fs.existsSync("users") && fs.mkdirSync("users");
const log = require('simple-node-logger').createRollingFileLogger({
    errorEventName:'error',
    logDirectory:'logger', // NOTE: folder must exist and be writable...
    fileNamePattern:'bot<DATE>.log',
    dateFormat:'YYYY.MM.DD'
});
const senter_user = config.botOptions.username;

const opts = {
  connection: {
		reconnect: true,
		secure: true
	},
  identity: {
    username: config.botOptions.username,//"recodingbot",
    password: config.botOptions.password//"oauth:q4nxdhnv8gxnpg4r6dl02deeubabnz"
  },
  channels: [senter_user]
};
function Stack(size=0){
  this.data = [];
  this.top = 0;
  this.push=function(e){this.data[this.top++]=e;if(size!=0&&size<=this.top)this.pop();return this.top};
	this.get=function(i){return this.data.length<i?this.data[i]:0};
	this.pop=function(){return this.top?this.data[--this.top]:0};
	this.peek=function(){return this.data[this.top-1]};
	this.indexOf=function(s){return this.data.indexOf(s)};
	this.length=function(){return this.top;};
	this.clear=function(){this.top=0;this.data.length=0;};
	this.all=function(a,l){l=[];for(a=0;a<this.top;a++)l.push(this.data[a]);return l;};
}

var ChatBot = {
  message:{"noneStream":"오프라인!","runStream":"방송중!","errAdd":"올바르지 않은 문장입니다!","followsUser":"팔로우한지 ","followsNo":"팔로우하지 않았습니다!",
    "helpAdd":"!추가 [word] [message or commands - {user}/{id}/{channel}/\\n]","helpBadWord":"!금지어 [word] [message or commands - ban/timeout/delete/\\n]",
    "helpClear":"!clear [ban or message]"
  },time:["초","분","시","일","년"],
  commands:{},chats:{},users:{},stream:{},
  onConnectedHandler:function(addr, port){
    console.log(`* Connected to ${addr}:${port}`);
    for(var i in ChatBot.commands){
        if(i=="recodingbot")continue;
        console.log(`추가 #${i}`);
        client.ws.send(`JOIN #${i}`);
        client.say(`#${i}`,`/me ${i}채널에 입장하였습니다!`);
    }
    client.say("#recodingbot",`${Object.keys(ChatBot.commands).length}명을 입장시켰습니다!`);
  },onMessageHandler:function(target, context, msg, self) {
    if (self) { return; }
    const commandName = msg.trim().split(" ");//공백제거
    if(target==`#${senter_user}`){//레봇채널
      switch (commandName[0]){
        case '!유저':case '!user':
           client.say(target,`${Object.keys(ChatBot.commands).length}명 온라인`);
           break;
        case '!recodingbot':case '!봇':
          client.say(target,`현재${target.substr(1)}채널을 중점으로 동작중입니다! - 기타문의 : 쪽지`);
          break;
        case '!입장':case '!join':
          var user = commandName[1] || context.username;
          if(ChatBot.commands.hasOwnProperty(target)){
            client.say(target,'이미 입장하였습니다!');
            break;
          }
          client.ws.send(`JOIN #${user}`);
          client.say(target,`/me ${user}채널에 입장시켰습니다!`);//현재채널 알림
          client.say(`#${user}`,`/me 봇이 채널에 입장하였습니다!`);//입장채널 알림
          ChatBot.getStreamData(user);ChatBot.loadUser(user,false);// 데이터 로드
          log.info(target,context['username'],context['user-id'],context['display-name'],`추가 #${user}`);
        case '!퇴장': case '!exit':// 관리자만 명령
          if((!context.mod && context.username != target.substr(1)))return;//관리자
          var user=commandName[1];
          if(!ChatBot.commands.hasOwnProperty(user))return;
          client.say(`#${user}`,`/me 레봇이가 채널에서 탈출합니다! 안녕~`);
          log.info(target,`${context['display-name']}(${context['username']}) 채널에서 퇴장함 - [${context['user-id']} ${user}]`);
          ChatBot.loadUser(user);//데아터 저장
          delete ChatBot.commands[user];//제거
          client.ws.send(`PART #${user}`);//저장
          break;
        case '!저장': case '!save':// 관리자만 명령
          if((!context.mod && context.username != target.substr(1)))return;//관리자
          for(var i in ChatBot.commands)
            ChatBot.loadUser(i);
          client.say(target,`/me 저장됨`);
          fs.writeFileSync("users/recodingbot.config",JSON.stringify(Object.keys(ChatBot.commands)),"utf8");
          // client.say(target,`${Object.keys().length}명 온라인`);
          break;
        default:break;
      }//switch
    }else{//사용자 채널//////////////////////////////////////////////////////////
      if(context["username"]=="recodingbot")return;
      if(!ChatBot.chats.hasOwnProperty(target.substr(1)))
        ChatBot.chats[target.substr(1)] = new Stack(500);
      switch (commandName[0]) {
       case '!방송':case '!stream'://방송시간
         var channeldata = ChatBot.getStreamData(target);
         if(!channeldata){
           client.say(target,"방송중이지 않아! 정보를 불러올 수 없습니다!");
           break;
         }
         if(typeof channeldata == 'string') client.say(target,channeldata);
         else client.say(target,`${channeldata.channel.game} (${channeldata.channel.followers}): ${channeldata.channel.status}`);
         break;//`#${senter_user}`
       case '!팔로우': case '!follows'://///////////////////////////////////////
         client.say(target,ChatBot.getFollow(target,context['user-id']));
         break;
       case '!업타임': case '!uptime':// 스트리밍 정보
         client.say(target,ChatBot.getStreamStarted(target));
         break;
       case '!레봇':case '!recodingbot':case '!rb':
         client.say(target,`현재${target.substr(1)}님 채팅 서버에서 가동중입니다! 주로 채팅을 제어하거나 필터링 및 모니터링 합니다! - 기타문의 : 쪽지`);
         break;
        case '!퇴장': case '!exit':// 채널에서 퇴장
          if((!context.mod && context.username != target.substr(1)))return;
          client.say(target,`/me 레봇이가 채널에서 탈출합니다! 안녕~`);
          log.info(target,`${context['display-name']}(${context['username']}) 채널에서 퇴장함 - [${context['user-id']} ${target.substr(1)}]`);
          ChatBot.loadUser(target);//데아터 저장
          delete ChatBot.commands[target.substr(1)];//제거
          client.ws.send(`PART ${target}`);//저장
          break;
        case '!명령어':case '!commands':// 명령어
          var out = (commandName[0]=='!commands'?
              ['!stream','!follows','!uptime','!recodingbot','!add','!del','!clear']:
              ['!방송','!업타임','!레봇','!팔로우','!명령어','!추가','!제거','!클리어']
            ).join(",");
          if(ChatBot.commands.hasOwnProperty(target.substr(1)) && ChatBot.commands[target.substr(1)].auto)
            out+=Object.keys(ChatBot.commands[target.substr(1)].auto).join(",");
          client.say(target,"/me " + out);
          break;
        case '!추가': case '!add'://0 1 2 //3
          if(!context.mod && context.username != target.substr(1))return;
          if(commandName.length < 3 || commandName[1].length ==0 || commandName[2].length ==0){//
            client.say(target,ChatBot.message.helpAdd);
          }else{
            ChatBot.commands[target.substr(1)].auto[commandName[1]] = commandName.length > 3?commandName.slice(2).join(" "):commandName[2];
            client.say(target,`명령이 추가됨! ${commandName[1]}`);
          }
          break;
        case '!제거': case '!del':
          if(!context.mod && context.username != target.substr(1))break;
          if(commandName.length <= 1){
            client.say(target,ChatBot.message.errAdd);
          }else{
            if(!ChatBot.command[target.substr(1)].auto.hasOwnProperty(commandName[1])){
              client.say(target,`명령이 존재하지 않음!`);
              break;
            }
            ChatBot.commands[target.substr(1)].auto[commandName[1]] = '';
            delete ChatBot.commands[target.substr(1)].auto[commandName[1]];
            client.say(target,`명령이 제거됨! ${commandName[1]}`);
          }
          break;
        case '!클리어':case '!clear':
          if(!context.mod && context.username != target.substr(1))break;
          if(commandName.length <= 1){
            client.say(target,ChatBot.message.helpClear);
          }else{
            if(!ChatBot.command[target.substr(1)].auto.hasOwnProperty(commandName[1])){
              client.say(target,`명령이 존재하지 않음!`);
              break;
            }
            var users = [];
            var index=commandName[1]=='ban'?2:1;//0 1 2
            var message=commandName.length>index+1?commandName.slice(index).join(" "):commandName[index];
            for(var i of ChatBot.chats[target.substr(1)])
              if(users.indexOf(i['username'])==-1 && i.message.indexOf(message)!=-1){
                if(index == 2){
                    users.append(i['username']);
                    client.say(target,`/ban ${i['username']} 당신은 불법프로그램을 사용하여 차단당하였습니다.You were blocked for using illegal programs. Inquiries: Notes`);
                }else
                  client.say(target,`/delete ${context['id']}`);
              }
            if(users.length)
              log.info(target,`${context['display-name']}(${context['username']}) 채널에서 퇴장 조취됨(clenner) - [${users.join(",")}]`);
            else log.info(target,`${context['display-name']}(${context['username']}) 채널에서 메세지 제거됨(clenner) - [${message}]`);
            client.say(target,`처리됨 :${index==2?(users.length+'명'):'메세지 제거처리'}`);
          }
          break;
        default:////////////////////////////////////////////////////////////////
          ChatBot.chats[target.substr(1)].push({
            'display-name':context['display-name'],
            'room-id':context['room-id'],
            'user-id':context['user-id'],
            'username':context['username'],
            'id':context['id'],
            'message':msg
          });
          log.info(target,context['username'],context['user-id'],context['display-name'],msg);
          var comm = ChatBot.commands[target.substr(1)].auto;
          for(var i in comm)/////////////////////////////////////////////명령어처리
            if(commandName[0].indexOf(i)!= -1){
              var out = comm[i].replace("{user}",context['display-name']).replace("{id}",context["username"]).replace("{channel}",target.substr(1)).split("@n");
              for(var i of out)
                client.say(target,i);
              break;
            }
      }
    }
    return;
  },command:function(target,type,user,option){
    if(["ban","timeout","delete"].indexOf(type)==-1)
      return;
    chats.say(target,`/${type} ${user} ${option}`);
    console.log(target,type,user,option);
    log.error(target,type,user,option);
  },getAPIData:function(url,header){
    if(!header)
      header ={'Client-ID':"wggm5zt40gfgffnzm5m3o3rgu1dfha", 'Accept': 'application/vnd.twitchtv.v5+json'};
    return request('GET',"https://api.twitch.tv/" + url,{headers:header})
  },getChannelId:function(channel){
    if(channel[0]=="#")channel=channel.substr(1);
    if(ChatBot.users.hasOwnProperty(channel))return ChatBot.users[channel];
    var data = ChatBot.getAPIData("kraken/users?login="+channel);
    if(data.statusCode != 200)return {};
    ChatBot.users[channel]=JSON.parse(data.getBody('utf8')).users[0];
    return ChatBot.users[channel];
  },getStreamData:function(target,isRe){
      if(target[0]=="#")target=target.substr(1);
      var user = ChatBot.getChannelId(target);
      if(!user.hasOwnProperty("_id"))return {};
      //강제 / 존재하지 않을때 / 5분 경과후
      if(!isRe && ChatBot.stream.hasOwnProperty(target) && Date.now() - ChatBot.stream[target].loading < 5 * 60 * 1000)
        return ChatBot.stream[target];
      var data = JSON.parse(ChatBot.getAPIData("kraken/streams/"+user["_id"]).getBody('utf8')).stream;
      if(!data)return ChatBot.message.noneStream;
      data.loading = Date.now();
      ChatBot.stream[target] = data;
      return data
  },getStreamStarted:function(target){
      if(target[0]=="#")target=target.substr(1);
      var data = ChatBot.getStreamData(target);
      if(data==ChatBot.message.noneStream)return ChatBot.message.noneStream;
      var start_at = new Date(data["created_at"]);
      return ChatBot.getConvertTime((Date.now() - start_at) / 1000).join("") + ChatBot.message.runStream;
  },getConvertTime:function(sec,skip=0){
    var mons = [31,28,31,30,31,30,31,31,30,31,30,31];
    var value = [60,60,24,365];
    var sec = sec;
    var out = [];
    if(!sec)return
    for(var i in value){
      if(skip<=0)
        out.push(Math.trunc(sec%value[i]) + ChatBot.time[i]);
      else skip--;
      if(sec < value[i]) break;
      sec/=value[i];
    }
    return out.reverse()
  },getFollow:function(target,users){
    var streamer = ChatBot.getChannelId(target);
    var data =ChatBot.getAPIData(`kraken/users/${users}/follows/channels/${streamer["_id"]}`);
    if(!data || data.statusCode!=200)return ChatBot.message.followsNo;
    data=JSON.parse(data.getBody('utf8'));
    var start_at = new Date(data["created_at"]);
    return `${ChatBot.message.followsUser}${ChatBot.getConvertTime((Date.now() - start_at) / 1000,1).join("")}`;
  },loadUser:function(target,isSave=true){
    var data=`{"words":{},"auto":{},"nicks":{},"time":{}}`;
    var t = target;
    if(t[0]=="#")t=t.substr(1);
    var f = `users/${t}.config`;
    if(ChatBot.commands.hasOwnProperty(t))
      data = JSON.stringify(ChatBot.commands[t]);
    if(!fs.existsSync(f)){
      fs.writeFileSync(f,data,"utf8");
      console.log('신규사용자! #',t);
      log.info(t,`신규사용자 #${t}`);
      ChatBot.commands[t] = {"words":{},"auto":{},"nicks":{},"time":{}};
      return;
    }
    if(isSave)
      fs.writeFile(f,data,"utf8",function(err){
        if(err)throw err;
        log.info("성공적으로 저장",t,data.length);
      })
    else fs.readFile(f,"utf8",function(err,data){
      if(err)throw err;
      if(data.length)
        ChatBot.commands[t] = JSON.parse(data);
      else {
        ChatBot.commands[t] = {"words":{},"auto":{},"nicks":{},"time":{}};
        log.info("불러오지 못함",t);
        console.log("불러오지 못함",t);
      }
    });
  },
}
////////////////////////////////////////////////////////////////////////////////
if(fs.existsSync("users/recodingbot.config")){
  fs.readFile("users/recodingbot.config","utf8",function(err,data){
    if(err)throw err;
    if(data.length)
      JSON.parse(data).forEach((item, i) => {
        ChatBot.loadUser(item,false);
      });
  });
}
////////////////////////////////////////////////////////////////////////////////
const client = new tmi.client(opts);
client.on('message', ChatBot.onMessageHandler);
client.on('connected', ChatBot.onConnectedHandler);
client.connect().catch(console.error);
////////////////////////////////////////////////////////////////////////////////
