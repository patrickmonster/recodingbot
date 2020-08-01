const tmi = require('tmi.js');
const request = require('sync-request');
const fs = require('fs');

!fs.existsSync("logger") && fs.mkdirSync("logger");
!fs.existsSync("users") && fs.mkdirSync("users");
const log = require('simple-node-logger').createRollingFileLogger({
    errorEventName:'error',
    logDirectory:'logger', // NOTE: folder must exist and be writable...
    fileNamePattern:'bot<DATE>.log',
    dateFormat:'YYYY.MM.DD'
});

const opts = {
  connection: {
		reconnect: true,
		secure: true
	},
  identity: {
    username: "recodingbot",
    password: "oauth:q4nxdhnv8gxnpg4r6dl02deeubabnz"
  },
  channels: [
    "recodingbot"
  ]
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
    "helpAdd":"!추가 [word] [message or commands - {user}/{id}/{channel}/\\n]","helpBadWord":"!금지어 [word] [message or commands - ban/timeout/delete/\\n]"
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
    if(!ChatBot.chats.hasOwnProperty(target))
      ChatBot.chats[target] = new Stack(500);
    switch (commandName[0]) {
      case '!유저':case '!user':
        if(target!="#recodingbot")return;
        client.say(target,`${Object.keys(ChatBot.commands).length}명 온라인`);
        break;
      case '!방송':case '!stream':
        if(target=="#recodingbot")return;
        client.say(target,ChatBot.getStreamStarted(target));
        break;
      case '!레봇':case '!recodingbot':case '!rb':
        client.say(target,`현재${target.substr(1)}님 채팅 서버에서 가동중입니다! 주로 채팅을 제어하거나 필터링 및 모니터링 합니다! - 기타문의 : 쪽지`);
        break;
      //////////////////////////////////////////////////////////////////////////
      case '!명령어':case '!commands':
        var out = (commandName[0]=='!commands'?
            ['!stream','!recodingbot','!commands','!follows','!add','!viewbot']:
            ['!방송','!레봇','!명령어','!팔로우','!추가','!뷰봇']
          ).join(",");
        if(target=="#recodingbot")
          out = ['!레봇','!입장','!퇴장'].join(",");
        if(ChatBot.commands.hasOwnProperty(target.substr(1)) && ChatBot.commands[target.substr(1)].auto)
          out+=Object.keys(ChatBot.commands[target.substr(1)].auto).join(",");
        client.say(target,"/me " + out);
        break;[]
      case '!팔로우': case '!follows':
        if(target=="#recodingbot")return;
        client.say(target,ChatBot.getFollow(target,context['user-id']));
        break;
      case '!종료': case '!end': case '!저장': case '!save':
        if(target!="#recodingbot")return;
        for(var i in ChatBot.commands){
            if(i=="recodingbot")continue;
            if(commandName[0]!='!save' && commandName[0]!='!저장')
              client.say(`#${i}`,commandName.length > 1?`/me ${commandName.slice(1).join(" ")}`:`/me ${i}채널에서 퇴장합니다(시스템 리부트)`);
            console.log(`제거 #${i}`);
            ChatBot.loadUser(i);
            client.ws.send(`PART #${user}`);
        }
        if(commandName[0]=='!save' || commandName[0]=='!저장'){
          client.say(`#recodingbot`,`/me 시스템 현재상태가 저장됨`);
          break;
        }
        client.say(`#recodingbot`,commandName.length > 1?`/me ${commandName.slice(1).join(" ")}`:`/me ${target}채널에서 퇴장합니다(시스템 리부트)`);
        console.log(commandName.length > 1?`${commandName.slice(1).join(" ")}`:`채널에서 퇴장합니다(시스템 리부트)`);
        log.info(target,commandName.length > 1?`${commandName.slice(1).join(" ")}`:`채널에서 퇴장합니다(시스템 리부트)`);
        console.log(Object.keys(ChatBot.commands).length+"명 온라인");
        fs.writeFileSync("users/recodingbot.config",JSON.stringify(Object.keys(ChatBot.commands)),"utf8");
        client.disconnect().catch(console.error);
        setTimeout(_=>{process.exit()},10*1000);
        break;
      case '!퇴장': case '!exit':
        var user = target!="#recodingbot" ? target.substr(1) : context.username;
        if(!context.mod && context.username != target.substr(1))return;
        if(target!="#recodingbot"){
          if(commandName.length <= 1)return;//명령없음
          user=commandName[1];
        }
        if(!ChatBot.commands.hasOwnProperty(user))return;
        client.say("#"+user,`/me ${user}채널에서 퇴장합니다`);
        console.log(`제거 #${user}`);
        log.info(target,`${context['display-name']}(${context['username']}) 채널에서 퇴장함 - [${context['user-id']} ${user}]`);
        ChatBot.loadUser(user);
        delete ChatBot.commands[user];
        client.ws.send(`PART #${user}`);
        break;
      case '!입장': case '!join':
        if(target!="#recodingbot")break;
        if(context.username == "recodingbot"){
          if(commandName.length >= 2){
            client.ws.send(`JOIN #${commandName[1]}`);
            client.say(target,`/me ${commandName[1]}채널에 입장시켰습니다!`);
            client.say(`#${commandName[1]}`,`/me ${commandName[1]}채널에 입장하였습니다!`);
            ChatBot.getStreamData(commandName[1]);
            ChatBot.loadUser(commandName[1],false);
            console.log(`추가 #${commandName[1]}`);
            log.info(target,context['username'],context['user-id'],context['display-name'],`추가 #${context.username}`);
            break;
          }else{
            client.say(target,`/me ${commandName[0]} [입장할채널]`);
            break;
          }
        }
        client.ws.send(`JOIN #${context.username}`);
        client.say(target,`/me ${context.username}채널에 입장시켰습니다!`);
        client.say(`#${context.username}`,`/me ${context.username}채널에 입장하였습니다!`);
        ChatBot.getStreamData(context.username);
        ChatBot.loadUser(context.username,false);
        console.log(`추가 #${context.username}`);
        log.info(target,context['username'],context['user-id'],context['display-name'],`추가 #${context.username}`);
        break;
      case '!추가': case '!add': case '!금지어': case '!badword':
        if(target=="#recodingbot")return;
        if(!context.mod && context.username != target.substr(1))return;
        if(commandName.length < 2){//
          client.say(target,(commandName[0]=='!추가'||commandName[0]=='!add')?ChatBot.message.helpAdd:ChatBot.message.helpBadWord);
        }else{
          var t = (commandName[0]=='!추가'||commandName[0]=='!add')?'auto':'words';
          ChatBot.commands[target.substr(1)][t][commandName[1]] = commandName.length > 3 ? commandName.slice(2).join(" "):commandName[2];
          console.log(commandName.slice(2).join(" "),commandName[1]);
          client.say(target,`/me 명령이 추가됨! ${commandName[1]}`);
        }
        break;
      case '!제거': case '!del':
        if(target=="#recodingbot")break;
        if(!context.mod && context.username != target.substr(1))break;
        if(commandName.length <= 1){
          client.say(target,ChatBot.message.errAdd);
        }else{
          if(!ChatBot.command[target.substr(1)].auto.hasOwnProperty(commandName[1])){
            if(!ChatBot.command[target.substr(1)].words.hasOwnProperty(commandName[1])){
              client.say(target,`/me 명령이 없습니다!`);return;
            }
            ChatBot.commands[target.substr(1)].words[commandName[1]] = '';
            delete ChatBot.commands[target.substr(1)].words[commandName[1]]
            client.say(target,`/me 금지어가 제거됨! ${commandName[1]}`);
            break;
          }
          ChatBot.commands[target.substr(1)].auto[commandName[1]] = '';
          delete ChatBot.commands[target.substr(1)].auto[commandName[1]]
          client.say(target,`/me 명령이 제거됨! ${commandName[1]}`);
        }
        break;
      case '!정보':
        if(context["username"]!='neocats_')break;
        var channeldata = ChatBot.getStreamData(target);
        if(!channeldata){
          client.say(target,"방송중이지 않아! 정보를 불러올 수 없습니다!");
          break;
        }
        if(typeof channeldata == 'string') client.say(target,channeldata);
        else client.say(target,`${channeldata.channel.game} (${channeldata.channel.followers})]${channeldata.channel.status} `);
        break;
      case '!뷰봇': case '!viewbot':
        if(target=="#recodingbot")return;
        if(!context.mod && context.username != target.substr(1))return;
        if(commandName.length < 2){
          client.say(target,"최근 채팅중, 불건전한 채팅을 검색하여 모두 벤 하는 기능입니다 [!뷰봇 검색채팅]");
        }else{
          chats = ChatBot.chats[target];
          var users=[];
          for(var i=0;i<chats.length();i++){
            var j = chats.get(i);
            if(j.message.indexOf(commandName[1])==-1)continue;
            users.push(j.username);
            ChatBot.command(target,"ban",j.username,"you using bad program! 밴 해지가 필요하면 쪽지로 매니저에게 요청하세요~");
          }
          client.say(target,`/me 사용자 ${users.length}명을 벤처리 하였습니다`);
          console.log(`${target} 사용자 ${users.length}명을 벤처리 하였습니다`);
          log.info(target,`${target} 사용자 ${users.length}명을 벤처리 하였습니다`);
        }
        break;
      default://////////////////////////////////////////////////////////////////
        if(target=="#recodingbot")break;
        ChatBot.chats[target].push({
          'display-name':context['display-name'],
          'room-id':context['room-id'],
          'user-id':context['user-id'],
          'username':context['username'],
          'id':context['id'],
          'message':msg
        });
        if(context["username"]=="recodingbot")break;
        log.info(target,context['username'],context['user-id'],context['display-name'],msg);
        var comm = ChatBot.commands[target.substr(1)].words;
        for(var i in comm)/////////////////////////////////////////////금지어처리
          if(msg.indexOf(i)!= -1){//전채스캔
            var out = comm[i].replace("{user}",context['display-name']).replace("{id}",context["username"]).replace("{channel}",target.substr(1));
            var out = out.split("\n");
            for(var i of out){
              var list = i.split(" ");
              if(["ban","timeout","delete"].indexOf(list[0])==-1||list.length >= 2)
                client.say(target,i);
              else ChatBot.command(target,list[0],list[0]!='delete'?context["username"]:context["id"],list[1]);
            }
            break
          }//if
        var comm = ChatBot.commands[target.substr(1)].auto;
        for(var i in comm)/////////////////////////////////////////////명령어처리
          if(commandName[0].indexOf(i)!= -1){
            var out = comm[i].replace("{user}",context['display-name']).replace("{id}",context["username"]).replace("{channel}",target.substr(1));
            var out = out.split("\n");
            console.log(out);
            for(var i of out)
              client.say(target,i);
            break;
          }
    }//switch
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
