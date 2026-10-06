import json
import os
import time
import urllib.request

URL = os.environ.get("UPSTASH_REDIS_REST_URL","").strip()
TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN","").strip()
MEMORY = {}

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

def command(cmd):
    if not URL or not TOKEN:
        return None
    req=urllib.request.Request(URL,
        data=json.dumps(cmd).encode(),
        headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"},
        method="POST")
    with urllib.request.urlopen(req,timeout=10) as r:
        return json.loads(r.read().decode())

def get(uid):
    try:
        r=command(["GET",f"bot:user:{uid}"])
        if r and r.get("result"):
            return json.loads(r["result"])
    except Exception:
        pass
    return MEMORY.get(str(uid))

def add_user(user):
    uid=str(user.get("id"))
    old=get(uid) or {}
    record={
        "id":uid,
        "first_name":user.get("first_name",""),
        "last_name":user.get("last_name",""),
        "username":user.get("username",""),
        "language":old.get("language","en"),
        "first_seen":old.get("first_seen",now()),
        "last_seen":now(),
        "welcome_count":int(old.get("welcome_count",0))+1
    }
    MEMORY[uid]=record
    try:
        command(["SET",f"bot:user:{uid}",json.dumps(record,ensure_ascii=False)])
        command(["SADD","bot:users",uid])
    except Exception:
        pass
    return record

def set_language(uid,language):
    r=get(uid) or {"id":str(uid),"first_name":"","last_name":"","username":"","first_seen":now(),"welcome_count":0}
    r["language"]=language; r["last_seen"]=now()
    MEMORY[str(uid)]=r
    try:
        command(["SET",f"bot:user:{uid}",json.dumps(r,ensure_ascii=False)])
        command(["SADD","bot:users",str(uid)])
    except Exception:
        pass

def get_all_user_ids():
    try:
        r=command(["SMEMBERS","bot:users"])
        if r and isinstance(r.get("result"),list):
            return [str(x) for x in r["result"]]
    except Exception:
        pass
    return list(MEMORY.keys())

def get_users():
    out=[]
    for uid in get_all_user_ids():
        u=get(uid)
        if u: out.append(u)
    return out
