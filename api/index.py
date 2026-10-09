import json
import os
import random
import time
import urllib.request
from http.server import BaseHTTPRequestHandler

# Vercel loads api/index.py directly. Add this directory so the
# sibling storage.py module is always importable.
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import (
    add_user,
    set_language,
    get as get_user,
    get_all_user_ids,
    get_users,
    get_gate_unlock,
    set_gate_unlock,
)

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = os.environ.get("ADMIN_ID", "").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "").strip().lstrip("@")

# First video shown after /start. Add your direct MP4 link here.
# Keep the URL ending in .mp4 when possible.
START_GATE_VIDEO_URL = "https://videotourl.com/videos/1791526055647-a7fa42c7-53dc-4db7-82ef-1a172870a746.mp4"
START_GATE_SECONDS = 65

# ============================================================
# WELCOME VIDEO URLS
# ============================================================
#
# YAHAN APNE DIRECT .MP4 VIDEO URL DALO
#
# Example:
# "https://videotourl.com/videos/example.mp4"
#
# Exactly 5 URLs rakh sakte ho.
# Agar abhi sirf 1 video hai, baaki slots mein same URL bhi
# rakh sakte ho.
#

WELCOME_VIDEOS = [
    "https://videotourl.com/videos/1791278971286-a204a8a9-469a-4993-93cf-ea2b16220f2d.mp4",

    "https://videotourl.com/videos/1791280897244-f1e1a4c4-8406-4833-84ec-eaf79dac2f20.mp4",

    "https://videotourl.com/videos/1791280942521-6b6d5f7e-cb3a-499d-aa81-5cb4426b0ff6.mp4",

    "https://yourimageshare.com/ib/aLiKKKuG3P.mp4",

    "https://videotourl.com/videos/1791282441015-51991811-7fa2-4f08-8ee0-13e1812e1092.mp4",
]


# ============================================================
# REACTIONS
# ============================================================
#
# Telegram mein har Unicode emoji reaction ke roop mein
# supported nahi hota. Isliye yahan Telegram ke commonly
# supported reaction emojis ka pool use kiya gaya hai.
#
# Random reaction har message par choose hoga.
#

REACTIONS = [
    "👍", "👎", "❤", "🔥", "🥰", "👏", "😁", "🤔",
    "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
    "🙏", "⚡", "🏆", "🌚", "🌭", "💔", "🍾", "💯",
    "🤣", "😎", "😍", "😘", "😇", "😡", "🤗", "🫡",
    "🫶", "✨", "🎊", "❤️", "🫣", "🤷", "😛", "🥴"
]


# ============================================================
# LANGUAGES
# ============================================================

LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "hinglish": "Hinglish",
    "bn": "বাংলা",
    "te": "తెలుగు",
    "mr": "मराठी",
    "ta": "தமிழ்",
    "gu": "ગુજરાતી",
    "ur": "اردو",
    "kn": "ಕನ್ನಡ",
    "or": "ଓଡ଼ିଆ",
    "ml": "മലയാളം",
    "pa": "ਪੰਜਾਬੀ",
    "as": "অসমীয়া",
    "mai": "मैथिली",
    "sa": "संस्कृतम्",
    "ne": "नेपाली",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ru": "Русский",
    "ar": "العربية",
    "tr": "Türkçe",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "th": "ไทย",
    "vi": "Tiếng Việt",
    "ko": "한국어",
    "ja": "日本語",
    "zh": "中文"
}


# ============================================================
# LANGUAGE FILES
# ============================================================
# Every language has its own JSON file in api/languages/.
# Missing keys safely fall back to English in t().

LANGUAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "languages")
TEXT = {}

for _language_code in LANGUAGES:
    _language_path = os.path.join(LANGUAGE_DIR, f"{_language_code}.json")
    try:
        with open(_language_path, "r", encoding="utf-8") as _language_file:
            TEXT[_language_code] = json.load(_language_file)
    except (OSError, json.JSONDecodeError):
        TEXT[_language_code] = {}


# ============================================================
# TELEGRAM API
# ============================================================

def api(method, data=None):

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    body = json.dumps(
        data or {},
        ensure_ascii=False
    ).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as response:

        return json.loads(
            response.read().decode()
        )


# ============================================================
# BOT USERNAME
# ============================================================

def bot_username():

    global BOT_USERNAME

    if BOT_USERNAME:
        return BOT_USERNAME

    try:

        result = api("getMe")

        BOT_USERNAME = (
            result.get("result", {})
            .get("username", "")
        )

    except Exception:

        BOT_USERNAME = ""

    return BOT_USERNAME


# ============================================================
# SEND MESSAGE
# ============================================================

def send_message(chat_id, text, markup=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if markup:
        data["reply_markup"] = markup

    return api(
        "sendMessage",
        data
    )


# ============================================================
# SEND VIDEO
# ============================================================

def send_video(chat_id, video, caption, markup=None):

    data = {
        "chat_id": chat_id,
        "video": video,
        "caption": caption
    }

    if markup:
        data["reply_markup"] = markup

    return api(
        "sendVideo",
        data
    )


# ============================================================
# REACTION
# ============================================================

def react(chat_id, message_id, private=False):

    # Keep private-chat reactions on a conservative set of common
    # Telegram emoji reactions. Group/channel behavior keeps using
    # the full configured pool below.
    pool = (
        [
            "👍", "👎", "❤", "🔥", "🥰", "👏", "😁", "🤔",
            "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
            "🙏", "💔", "💯", "🤣", "🏆", "🍾", "🌚", "🌭"
        ]
        if private else REACTIONS
    )

    emoji = random.choice(pool)

    return api(
        "setMessageReaction",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [
                {
                    "type": "emoji",
                    "emoji": emoji
                }
            ]
        }
    )


# ============================================================
# TRANSLATION
# ============================================================

def t(lang, key, **kw):

    data = TEXT.get(
        lang,
        TEXT["en"]
    )

    value = data.get(
        key,
        TEXT["en"].get(key, key)
    )

    return value.format(**kw)


# ============================================================
# GET USER LANGUAGE
# ============================================================

def lang_of(uid):

    return (
        get_user(uid) or {}
    ).get(
        "language",
        "en"
    )


# ============================================================
# MAIN KEYBOARD
# ============================================================

def keyboard(lang):

    username = bot_username()

    if username:

        add_url = (
            f"https://t.me/{username}?startgroup=true"
        )

    else:

        add_url = "https://t.me/"

    return {
        "inline_keyboard": [

            [
                {
                    "text": t(lang, "add"),
                    "url": add_url
                }
            ],

            [
                {
                    "text": t(lang, "language"),
                    "callback_data": "language"
                }
            ]

        ]
    }


# ============================================================
# LANGUAGE KEYBOARD
# ============================================================

def language_keyboard():

    items = list(
        LANGUAGES.items()
    )

    return {
        "inline_keyboard": [

            [
                {
                    "text": label,
                    "callback_data": f"lang:{code}"
                }

                for code, label in items[i:i + 3]
            ]

            for i in range(
                0,
                len(items),
                3
            )
        ]
    }


# ============================================================
# EDIT MESSAGE
# ============================================================

def edit(chat_id, message_id, text, markup):

    return api(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": markup
        }
    )


# ============================================================
# START VIDEO GATE
# ============================================================

def start_video_gate(message):
    """Show the intro gate only when the user's 24-hour unlock has expired."""
    user = message.get("from", {})
    chat_id = message.get("chat", {}).get("id")
    uid = str(user.get("id", ""))

    # process() already saves private users. Read the latest persisted record.
    record = get_user(uid) or add_user(user)

    # A completed gate remains unlocked for 24 hours, including across redeploys.
    try:
        unlocked_until = int(get_gate_unlock(uid) or 0)
    except (TypeError, ValueError):
        unlocked_until = 0

    if int(time.time()) < unlocked_until:
        welcome(message, existing_record=record)
        return

    if (not START_GATE_VIDEO_URL.startswith("http") or
            "PASTE_YOUR_DIRECT_MP4_LINK_HERE" in START_GATE_VIDEO_URL):
        send_message(chat_id, "⚠️ Welcome video link abhi set nahi hai. Developer ko START_GATE_VIDEO_URL mein direct MP4 link add karna hoga.")
        return

    lang = record.get("language", "en")
    name = user.get("first_name") or "there"
    caption = (
        f"{t(lang, 'welcome', name=name)}\n\n"
        f"{t(lang, 'description')}\n\n"
        "👑 Developer: Toxice Hacker"
    )
    unlock_at = int(time.time()) + START_GATE_SECONDS
    markup = {"inline_keyboard": [[{
        "text": t(lang, "continue"),
        "callback_data": f"watch:{unlock_at}:{uid}"
    }]]}
    try:
        send_video(chat_id, START_GATE_VIDEO_URL, caption, markup)
    except Exception:
        send_message(chat_id, caption + "\n\n⚠️ Video load nahi hua. Link check karo.", markup)


# ============================================================
# WELCOME
# ============================================================

def welcome(message, existing_record=None):

    user = message.get(
        "from",
        {}
    )

    uid = str(
        user.get("id")
    )

    record = existing_record or add_user(user)

    lang = record.get(
        "language",
        "en"
    )

    name = (
        user.get("first_name")
        or "there"
    )

    caption = (
        f"{t(lang, 'welcome', name=name)}\n\n"
        f"{t(lang, 'description')}\n\n"
        "🎲 ❤️ 🔥 👍 😍"
    )

    # --------------------------------------------------------
    # Select one of the 5 videos
    # --------------------------------------------------------

    welcome_count = record.get(
        "welcome_count",
        1
    )

    index = (
        int(welcome_count) - 1
    ) % len(WELCOME_VIDEOS)

    video_url = WELCOME_VIDEOS[index]

    # --------------------------------------------------------
    # Send external video URL directly
    # --------------------------------------------------------

    if (
        video_url
        and video_url.startswith("http")
        and video_url.lower().endswith(".mp4")
        and "VIDEO_URL_" not in video_url
    ):

        try:

            send_video(
                message["chat"]["id"],
                video_url,
                caption,
                keyboard(lang)
            )

            return

        except Exception:

            pass

    # --------------------------------------------------------
    # If video fails, send text welcome
    # --------------------------------------------------------

    send_message(
        message["chat"]["id"],
        caption,
        keyboard(lang)
    )


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(uid):

    return (
        bool(ADMIN_ID)
        and str(uid) == str(ADMIN_ID)
    )


# ============================================================
# PRIVATE MESSAGE
# ============================================================

def private_message(message):

    chat_id = message["chat"]["id"]

    sender = message.get(
        "from",
        {}
    )

    uid = str(
        sender.get("id", "")
    )

    text = (
        message.get("text")
        or ""
    ).strip()

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    if text.startswith("/start"):

        start_video_gate(message)

        return

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if text == "/status":

        send_message(
            chat_id,
            t(
                lang_of(uid),
                "status"
            )
        )

        return

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if text == "/user":

        if not is_admin(uid):

            send_message(
                chat_id,
                t("en", "no_access")
            )

            return

        users = get_users()

        send_message(
            chat_id,
            t(
                "en",
                "users",
                count=len(users)
            )
        )

        for u in users[:100]:

            username = (
                "@"
                + u["username"]
                if u.get("username")
                else "—"
            )

            card = t(
                "en",
                "user_card",
                id=u.get("id", "—"),
                name=u.get("first_name", "—"),
                username=username,
                language=LANGUAGES.get(
                    u.get("language", "en"),
                    u.get("language", "en")
                ),
                first_seen=u.get(
                    "first_seen",
                    "—"
                ),
                last_seen=u.get(
                    "last_seen",
                    "—"
                )
            )

            send_message(
                chat_id,
                card
            )

        return

    # --------------------------------------------------------
    # BROADCAST
    # --------------------------------------------------------

    if text.startswith("/broadcast"):

        if not is_admin(uid):

            send_message(
                chat_id,
                t("en", "no_access")
            )

            return

        parts = text.split(
            maxsplit=2
        )

        if len(parts) < 2:

            send_message(
                chat_id,
                t(
                    "en",
                    "broadcast_usage"
                )
            )

            return

        # ----------------------------------------------------
        # Broadcast to one user
        # ----------------------------------------------------

        if (
            len(parts) == 3
            and parts[1].lstrip("-").isdigit()
        ):

            target = parts[1]
            msg = parts[2]

            try:

                send_message(
                    target,
                    msg
                )

                send_message(
                    chat_id,
                    t(
                        "en",
                        "broadcast_one_done",
                        id=target
                    )
                )

            except Exception:

                send_message(
                    chat_id,
                    t(
                        "en",
                        "broadcast_one_failed",
                        id=target
                    )
                )

            return

        # ----------------------------------------------------
        # Broadcast to all users
        # ----------------------------------------------------

        msg = text[
            len("/broadcast"):
        ].strip()

        if not msg:

            send_message(
                chat_id,
                t(
                    "en",
                    "broadcast_usage"
                )
            )

            return

        sent = 0
        failed = 0

        for target in get_all_user_ids():

            try:

                send_message(
                    target,
                    msg
                )

                sent += 1

            except Exception:

                failed += 1

        send_message(
            chat_id,
            t(
                "en",
                "broadcast_done",
                sent=sent,
                failed=failed
            )
        )


# ============================================================
# CALLBACK
# ============================================================

def callback(q):

    qid = q["id"]

    data = q.get(
        "data",
        ""
    )

    msg = q.get(
        "message",
        {}
    )

    user = q.get(
        "from",
        {}
    )

    uid = str(
        user.get("id")
    )

    # --------------------------------------------------------
    # INTRO VIDEO CONTINUE (65-second time gate)
    # --------------------------------------------------------
    if data.startswith("watch:"):
        try:
            _, unlock_at, target_uid = data.split(":", 2)
            unlock_at = int(unlock_at)
        except (ValueError, TypeError):
            api("answerCallbackQuery", {"callback_query_id": qid, "text": "Invalid button. Please send /start again.", "show_alert": True})
            return

        if str(target_uid) != uid:
            api("answerCallbackQuery", {"callback_query_id": qid, "text": "Ye button kisi aur user ke liye hai.", "show_alert": True})
            return

        now_ts = int(time.time())
        # Expire old gate buttons so a stale button cannot bypass a future gate.
        if now_ts > unlock_at + 86400:
            api("answerCallbackQuery", {
                "callback_query_id": qid,
                "text": "This gate expired. Please send /start again.",
                "show_alert": True
            })
            return

        if now_ts < unlock_at:
            api("answerCallbackQuery", {
                "callback_query_id": qid,
                "text": "🔒 Watch the full video and press Continue to unlock! 💗",
                "show_alert": True
            })
            return

        # Start a fresh 24-hour unlock window only after the timer has elapsed.
        # Redis stores the expiry so redeploys and separate serverless instances retain it.
        set_gate_unlock(uid, now_ts + 86400)
        api("answerCallbackQuery", {"callback_query_id": qid, "text": "✅ Continue unlocked!"})

        # Remove the introductory force-watch video before showing the
        # regular rotating welcome video. Telegram may reject deletion in
        # unusual cases, so don't block the welcome flow if that happens.
        try:
            gate_chat_id = msg.get("chat", {}).get("id")
            gate_message_id = msg.get("message_id")
            if gate_chat_id is not None and gate_message_id is not None:
                api("deleteMessage", {
                    "chat_id": gate_chat_id,
                    "message_id": gate_message_id
                })
        except Exception:
            pass

        regular_message = {"from": user, "chat": msg.get("chat", {})}
        record = get_user(uid)
        welcome(regular_message, existing_record=record)
        return

    # --------------------------------------------------------
    # LANGUAGE MENU
    # --------------------------------------------------------

    if data == "language":

        api(
            "answerCallbackQuery",
            {
                "callback_query_id": qid
            }
        )

        edit(
            msg["chat"]["id"],
            msg["message_id"],
            t(
                lang_of(uid),
                "choose"
            ),
            language_keyboard()
        )

    # --------------------------------------------------------
    # LANGUAGE SELECTED
    # --------------------------------------------------------

    elif data.startswith("lang:"):

        code = data.split(
            ":",
            1
        )[1]

        if code not in LANGUAGES:

            return

        set_language(
            uid,
            code
        )

        api(
            "answerCallbackQuery",
            {
                "callback_query_id": qid,
                "text": LANGUAGES[code]
            }
        )

        edit(
            msg["chat"]["id"],
            msg["message_id"],

            f"{t(code, 'welcome', name=user.get('first_name') or 'there')}\n\n"
            f"{t(code, 'description')}\n\n"
            f"{t(code, 'saved', lang=LANGUAGES[code])}",

            keyboard(code)
        )


# ============================================================
# PROCESS UPDATE
# ============================================================

def process(update):

    # --------------------------------------------------------
    # CALLBACK
    # --------------------------------------------------------

    if "callback_query" in update:

        callback(
            update["callback_query"]
        )

        return

    # --------------------------------------------------------
    # NORMAL MESSAGE
    # --------------------------------------------------------

    msg = update.get(
        "message"
    )

    if msg:

        chat = msg.get(
            "chat",
            {}
        )

        typ = chat.get(
            "type"
        )

        # ----------------------------------------------------
        # PRIVATE
        # ----------------------------------------------------

        if typ == "private":

            add_user(
                msg.get(
                    "from",
                    {}
                )
            )

            # React to the user's private message as well. This includes
            # /start, so the user gets an immediate reaction in the DM.
            try:

                react(
                    chat["id"],
                    msg["message_id"],
                    private=True
                )

            except Exception:

                # A reaction must never stop the normal bot reply.
                pass

            private_message(
                msg
            )

            return

        # ----------------------------------------------------
        # GROUP / SUPERGROUP
        # ----------------------------------------------------

        if typ in (
            "group",
            "supergroup"
        ):

            text = (
                msg.get("text")
                or ""
            )

            # Commands par reaction nahi
            if not text.startswith("/"):

                try:

                    react(
                        chat["id"],
                        msg["message_id"]
                    )

                except Exception:

                    pass

            return

    # --------------------------------------------------------
    # CHANNEL POST
    # --------------------------------------------------------

    post = update.get(
        "channel_post"
    )

    if post:

        chat = post.get(
            "chat",
            {}
        )

        if chat.get("type") == "channel":

            try:

                react(
                    chat["id"],
                    post["message_id"]
                )

            except Exception:

                pass


# ============================================================
# VERCEL HANDLER
# ============================================================

class handler(BaseHTTPRequestHandler):

    def out(self, status, data):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode()

        self.send_response(
            status
        )

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(
            body
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def do_GET(self):

        self.out(
            200,
            {
                "ok": True,
                "service": "Telegram Auto Reaction Bot",
                "welcome_videos": len(WELCOME_VIDEOS),
                "start_gate_seconds": START_GATE_SECONDS,
                "reactions": len(REACTIONS)
            }
        )

    # --------------------------------------------------------
    # POST WEBHOOK
    # --------------------------------------------------------

    def do_POST(self):

        try:

            n = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            raw = self.rfile.read(
                n
            ).decode()

            update = json.loads(
                raw
            )

            process(
                update
            )

        except Exception:

            pass

        self.out(
            200,
            {
                "ok": True
            }
        )
