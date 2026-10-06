import json
import os
import random
import urllib.request
from http.server import BaseHTTPRequestHandler

from storage import add_user, get_all_user_ids, get_user, get_users, set_language

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = os.environ.get("ADMIN_ID", "").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "").strip().lstrip("@")

REACTIONS = ["❤️", "🔥", "👍", "😍"]

# Put exactly five MP4 files in /videos:
# welcome1.mp4, welcome2.mp4, welcome3.mp4, welcome4.mp4, welcome5.mp4
WELCOME_VIDEOS = [f"/videos/welcome{i}.mp4" for i in range(1, 6)]

LANGUAGES = {
    "en":"English","hi":"हिन्दी","hinglish":"Hinglish","bn":"বাংলা","te":"తెలుగు",
    "mr":"मराठी","ta":"தமிழ்","gu":"ગુજરાતી","ur":"اردو","kn":"ಕನ್ನಡ",
    "or":"ଓଡ଼ିଆ","ml":"മലയാളം","pa":"ਪੰਜਾਬੀ","as":"অসমীয়া","mai":"मैथिली",
    "sa":"संस्कृतम्","ne":"नेपाली","es":"Español","fr":"Français","de":"Deutsch",
    "it":"Italiano","pt":"Português","ru":"Русский","ar":"العربية","tr":"Türkçe",
    "id":"Bahasa Indonesia","ms":"Bahasa Melayu","th":"ไทย","vi":"Tiếng Việt",
    "ko":"한국어","ja":"日本語","zh":"中文"
}

TEXT = {
    "en":{
        "welcome":"Welcome, {name}! 👋",
        "description":"I am an Auto Reaction Bot. Add me to your group or channel and I will automatically react to new messages with random reactions: ❤️ 🔥 👍 😍",
        "add":"➕ Add to your Group/Channel","language":"🌐 Language","choose":"Choose your language:",
        "saved":"✅ Language changed to {lang}.","status":"🤖 Auto Reaction Bot is online.\n🎲 Random reactions: ❤️ 🔥 👍 😍",
        "no_access":"❌ You are not authorized to use this command.","users":"👥 Total users: {count}",
        "user_card":"👤 USER DETAILS\n\n🆔 User ID: {id}\n👤 Name: {name}\n🔗 Username: {username}\n🌐 Language: {language}\n📅 First seen: {first_seen}\n🕒 Last seen: {last_seen}",
        "broadcast_usage":"Usage:\n/broadcast Your message\n\nOr:\n/broadcast USER_ID Your message",
        "broadcast_done":"📣 Broadcast finished.\n\n✅ Sent: {sent}\n❌ Failed: {failed}",
        "broadcast_one_done":"✅ Message sent to {id}.","broadcast_one_failed":"❌ Could not send the message to {id}.",
        "not_found":"❌ User not found."
    },
    "hi":{
        "welcome":"स्वागत है, {name}! 👋",
        "description":"मैं Auto Reaction Bot हूँ। मुझे अपने ग्रुप या चैनल में जोड़ें। मैं नए मैसेज पर ❤️ 🔥 👍 😍 में से random reaction लगाऊँगा।",
        "add":"➕ अपने Group/Channel में जोड़ें","language":"🌐 भाषा","choose":"अपनी भाषा चुनें:",
        "saved":"✅ भाषा बदलकर {lang} कर दी गई।","status":"🤖 Auto Reaction Bot चालू है।\n🎲 Random reactions: ❤️ 🔥 👍 😍",
        "no_access":"❌ आप इस command के लिए authorized नहीं हैं।","users":"👥 कुल users: {count}",
        "user_card":"👤 USER DETAILS\n\n🆔 User ID: {id}\n👤 नाम: {name}\n🔗 Username: {username}\n🌐 भाषा: {language}\n📅 पहली बार: {first_seen}\n🕒 आखिरी बार: {last_seen}",
        "broadcast_usage":"Usage:\n/broadcast अपना message\n\nया:\n/broadcast USER_ID अपना message",
        "broadcast_done":"📣 Broadcast पूरा हुआ।\n\n✅ भेजा गया: {sent}\n❌ Failed: {failed}",
        "broadcast_one_done":"✅ {id} को message भेज दिया गया।","broadcast_one_failed":"❌ {id} को message नहीं भेज सका।",
        "not_found":"❌ User नहीं मिला।"
    },
    "hinglish":{
        "welcome":"Welcome, {name}! 👋",
        "description":"Main Auto Reaction Bot hoon. Mujhe apne group ya channel me add karo. Main naye messages par ❤️ 🔥 👍 😍 me se random reaction lagaunga.",
        "add":"➕ Add to your Group/Channel","language":"🌐 Language","choose":"Apni language choose karo:",
        "saved":"✅ Language {lang} set kar di gayi.","status":"🤖 Auto Reaction Bot online hai.\n🎲 Random reactions: ❤️ 🔥 👍 😍",
        "no_access":"❌ Aap authorized nahi ho.","users":"👥 Total users: {count}",
        "user_card":"👤 USER DETAILS\n\n🆔 User ID: {id}\n👤 Name: {name}\n🔗 Username: {username}\n🌐 Language: {language}\n📅 First seen: {first_seen}\n🕒 Last seen: {last_seen}",
        "broadcast_usage":"Usage:\n/broadcast Your message\n\nYa:\n/broadcast USER_ID Your message",
        "broadcast_done":"📣 Broadcast complete.\n\n✅ Sent: {sent}\n❌ Failed: {failed}",
        "broadcast_one_done":"✅ Message {id} ko bhej diya.","broadcast_one_failed":"❌ Message {id} ko nahi bhej saka.",
        "not_found":"❌ User nahi mila."
    }
}

def api(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    body = json.dumps(data or {}, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def bot_username():
    global BOT_USERNAME
    if BOT_USERNAME:
        return BOT_USERNAME
    try:
        BOT_USERNAME = api("getMe")["result"]["username"]
    except Exception:
        BOT_USERNAME = ""
    return BOT_USERNAME

def send_message(chat_id, text, markup=None):
    data = {"chat_id":chat_id, "text":text}
    if markup: data["reply_markup"] = markup
    return api("sendMessage", data)

def send_video(chat_id, video, caption, markup=None):
    data = {"chat_id":chat_id, "video":video, "caption":caption}
    if markup: data["reply_markup"] = markup
    return api("sendVideo", data)

def react(chat_id, message_id):
    return api("setMessageReaction", {
        "chat_id":chat_id, "message_id":message_id,
        "reaction":[{"type":"emoji","emoji":random.choice(REACTIONS)}]
    })

def t(lang, key, **kw):
    d = TEXT.get(lang, TEXT["en"])
    return d.get(key, TEXT["en"].get(key, key)).format(**kw)

def lang_of(uid):
    return (get_user(uid) or {}).get("language","en")

def keyboard(lang):
    username = bot_username()
    add_url = f"https://t.me/{username}?startgroup=true" if username else "https://t.me/"
    return {"inline_keyboard":[
        [{"text":t(lang,"add"),"url":add_url}],
        [{"text":t(lang,"language"),"callback_data":"language"}]
    ]}

def language_keyboard():
    items=list(LANGUAGES.items())
    return {"inline_keyboard":[
        [{"text":label,"callback_data":f"lang:{code}"} for code,label in items[i:i+3]]
        for i in range(0,len(items),3)
    ]}

def edit(chat_id, message_id, text, markup):
    return api("editMessageText", {
        "chat_id":chat_id,"message_id":message_id,
        "text":text,"reply_markup":markup
    })

def welcome(message):
    user=message.get("from",{})
    uid=str(user.get("id"))
    record=add_user(user)
    lang=record.get("language","en")
    name=user.get("first_name") or "there"
    caption=f"{t(lang,'welcome',name=name)}\n\n{t(lang,'description')}\n\n🎲 ❤️ 🔥 👍 😍"
    index=(record.get("welcome_count",1)-1)%5
    # Telegram needs a public HTTPS URL. Vercel serves /videos/* as static files.
    base=os.environ.get("VERCEL_PROJECT_PRODUCTION_URL","").strip()
    if not base:
        base=os.environ.get("VERCEL_URL","").strip()
    if base and not base.startswith("http"):
        base="https://"+base
    if base:
        video_url=base.rstrip("/") + WELCOME_VIDEOS[index]
        try:
            send_video(message["chat"]["id"],video_url,caption,keyboard(lang))
            return
        except Exception:
            pass
    send_message(message["chat"]["id"],caption,keyboard(lang))

def is_admin(uid):
    return bool(ADMIN_ID) and str(uid)==str(ADMIN_ID)

def private_message(message):
    chat_id=message["chat"]["id"]
    sender=message.get("from",{})
    uid=str(sender.get("id",""))
    text=(message.get("text") or "").strip()

    if text.startswith("/start"):
        welcome(message); return

    if text=="/status":
        send_message(chat_id,t(lang_of(uid),"status")); return

    if text=="/user":
        if not is_admin(uid):
            send_message(chat_id,t("en","no_access")); return
        users=get_users()
        send_message(chat_id,t("en","users",count=len(users)))
        for u in users[:100]:
            username="@"+u["username"] if u.get("username") else "—"
            card=t("en","user_card",
                id=u.get("id","—"),name=u.get("first_name","—"),
                username=username,language=LANGUAGES.get(u.get("language","en"),u.get("language","en")),
                first_seen=u.get("first_seen","—"),last_seen=u.get("last_seen","—"))
            send_message(chat_id,card)
        return

    if text.startswith("/broadcast"):
        if not is_admin(uid):
            send_message(chat_id,t("en","no_access")); return
        parts=text.split(maxsplit=2)
        if len(parts)<2:
            send_message(chat_id,t("en","broadcast_usage")); return
        if len(parts)==3 and parts[1].lstrip("-").isdigit():
            target=parts[1]; msg=parts[2]
            try:
                send_message(target,msg)
                send_message(chat_id,t("en","broadcast_one_done",id=target))
            except Exception:
                send_message(chat_id,t("en","broadcast_one_failed",id=target))
            return
        msg=text[len("/broadcast"):].strip()
        if not msg:
            send_message(chat_id,t("en","broadcast_usage")); return
        sent=failed=0
        for target in get_all_user_ids():
            try:
                send_message(target,msg); sent+=1
            except Exception:
                failed+=1
        send_message(chat_id,t("en","broadcast_done",sent=sent,failed=failed))

def callback(q):
    qid=q["id"]; data=q.get("data",""); msg=q.get("message",{}); user=q.get("from",{})
    uid=str(user.get("id",""))
    if data=="language":
        api("answerCallbackQuery",{"callback_query_id":qid})
        edit(msg["chat"]["id"],msg["message_id"],t(lang_of(uid),"choose"),language_keyboard())
    elif data.startswith("lang:"):
        code=data.split(":",1)[1]
        if code not in LANGUAGES: return
        set_language(uid,code)
        api("answerCallbackQuery",{"callback_query_id":qid,"text":LANGUAGES[code]})
        edit(msg["chat"]["id"],msg["message_id"],
             f"{t(code,'welcome',name=user.get('first_name') or 'there')}\n\n"
             f"{t(code,'description')}\n\n{t(code,'saved',lang=LANGUAGES[code])}",
             keyboard(code))

def process(update):
    if "callback_query" in update:
        callback(update["callback_query"]); return
    msg=update.get("message")
    if msg:
        typ=msg.get("chat",{}).get("type")
        if typ=="private":
            add_user(msg.get("from",{})); private_message(msg); return
        if typ in ("group","supergroup"):
            if not (msg.get("text") or "").startswith("/"):
                try: react(msg["chat"]["id"],msg["message_id"])
                except Exception: pass
            return
    post=update.get("channel_post")
    if post and post.get("chat",{}).get("type")=="channel":
        try: react(post["chat"]["id"],post["message_id"])
        except Exception: pass

class handler(BaseHTTPRequestHandler):
    def out(self,status,data):
        body=json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        self.out(200,{"ok":True,"service":"Telegram Auto Reaction Bot","videos":5,"reactions":REACTIONS})

    def do_POST(self):
        try:
            n=int(self.headers.get("Content-Length","0"))
            update=json.loads(self.rfile.read(n).decode())
            process(update)
        except Exception:
            pass
        self.out(200,{"ok":True})
