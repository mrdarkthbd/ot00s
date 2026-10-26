#!/usr/bin/env python3
"""
TempNumbers.net OTP Bot — ULTIMATE WEBHOOK EDITION (FULLY FIXED)
"""

import asyncio
import aiohttp
import re
import logging
import os
import hashlib
import json
import socket
import time
from html import escape
from datetime import datetime, timedelta, timezone
from collections import deque
from typing import Optional, Tuple, List, Dict, Any

import phonenumbers
from phonenumbers import geocoder, region_code_for_number
from aiohttp import web

# ============================================================
#  INLINE CONFIGURATION (YOUR SERVER DETAILS)
# ============================================================
CONFIG = {
    # --- New API ---
    "API_BASE_URL": "https://tempnumbers.net/api",
    "API_TOKEN": "2066601be12043160be269182c4a109ddc72c205a585ac066a81665a439605c4",

# --- Webhook Server ---
"WEBHOOK_HOST": "0.0.0.0",
"WEBHOOK_PORT": os.environ.get("PORT", "2379"),
"WEBHOOK_PATH": "/webhook",
"WEBHOOK_SECRET": "",    

    # --- Telegram ---
    "TELEGRAM_BOT_TOKEN": "8841791583:AAHro-N-sS7iE4FLEj7smF89feiEIpmXG7A",
    "TELEGRAM_CHAT_ID": "-1003621784864",
    "ADMIN_IDS": "5076047031",

    # --- Misc ---
    "LAST_N_TO_FORWARD": "5",
    "TELEGRAM_UPDATES_INTERVAL": "2",
    "BACKUP_CHANNEL_URL": "https://t.me/numbervirtualfast",
    "NUMBER_CHANNEL_URL": "https://t.me/virtualnumberxd",
    "USE_PREMIUM_EMOJI": "1",
    "BOT_THEME_FILE": "bot_theme.json",
    
    # --- Website Webhook (SmarterASP.net Domain) ---
    "SITE_WEBHOOK_URL": "https://mrdarkvipx-001-site1.etempurl.com/webhook/main"
}

def _cfg(key, default=""):
    v = CONFIG.get(key)
    if v is not None: return str(v)
    return os.getenv(key, default)

def _cfg_bool(key, default=False):
    return _cfg(key, "1" if default else "0").strip().lower() in {"1","true","yes","on"}

def _cfg_int(key, default=0):
    try: return int(float(_cfg(key, str(default))))
    except Exception: return default

def _cfg_float(key, default=0.0):
    try: return float(_cfg(key, str(default)))
    except Exception: return default

# ============================================================
#  LANGUAGE DETECTION
# ============================================================
try:
    from langdetect import detect as _ld_detect, DetectorFactory
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except Exception:
    _ld_detect = None
    LANGDETECT_AVAILABLE = False

LANG_CODE_TO_NAME = {
    "en":"English","ru":"Russian","uk":"Ukrainian","es":"Spanish","pt":"Portuguese",
    "fr":"French","de":"German","tr":"Turkish","ar":"Arabic","hi":"Hindi",
    "id":"Indonesian","it":"Italian","th":"Thai","vi":"Vietnamese","zh-cn":"Chinese",
    "zh-tw":"Chinese","ja":"Japanese","ko":"Korean","bn":"Bangla","ur":"Urdu",
}

def detect_language_name(text: str) -> str:
    if not text or not text.strip(): return "Unknown"
    if re.search(r'[\u0400-\u04FF]', text): return "Russian"
    if LANGDETECT_AVAILABLE and _ld_detect:
        try: return LANG_CODE_TO_NAME.get(_ld_detect(text), "Unknown")
        except Exception: return "Unknown"
    return "English"

# ============================================================
#  PREMIUM FLAGS
# ============================================================
PREMIUM_FLAGS = {
    "RU":"5433865586356531140","CN":"5433827537241258614","ZA":"5431855966863766753",
    "BR":"5431769908604056769","IN":"5433601609076586221","NO":"5434147542369579483",
    "GB":"5435996255207567113","AF":"5433636707549331311","AL":"5433845881046578644",
    "DZ":"5433627189901801019","AD":"5433946537900128161","AO":"5433750193470191473",
    "AG":"5431752174684092629","AR":"5433754239329383923","AM":"5433804400252434985",
    "AU":"5431556723607352698","AT":"5431640943621060829","BS":"5431375858239550223",
    "BH":"5433682092468746953","BD":"5433854239052935880","BB":"5434027579638035690",
    "BY":"5431739800883312139","BE":"5433598052843665552","BZ":"5431431529605642522",
    "BJ":"5433838931789492934","BO":"5433609855413794108","BA":"5433991338703991663",
    "BW":"5433895109961725692","BN":"5433789964867352475","BG":"5431663303220804322",
    "BF":"5434013938821902926","MM":"5433666360003540231","BI":"5433792911214917126",
    "KH":"5433696429069580735","CM":"5433774971136521802","CA":"5433960238845802718",
    "CV":"5431865097964237519","CF":"5431374711483282830","TD":"5433825269498525925",
    "CL":"5431561302042488884","CO":"5433630999537792332","KM":"5431790266749040145",
    "CD":"5431703839122141424","CG":"5433861570562111275","HR":"5431489619038320862",
    "CU":"5431551436502611633","CY":"5434096943359866241","CZ":"5433958877341169005",
    "DK":"5433708502222649633","DM":"5433614889115464671","DO":"5434140679011842196",
    "EC":"5431462560744353934","EG":"5431619494554383246","SV":"5434134189316257066",
    "GB-ENG":"5431508997930758727","ER":"5433723401464198287","EE":"5433727662071755290",
    "ET":"5433804408842368654","EU":"5434011361841525609","FJ":"5433640560134994324",
    "FI":"5431380440969654931","FR":"5434067424049639550","GF":"5433979415874779870",
    "GA":"5433982207603520017","GM":"5433596974806873997","GE":"5433814347396692144",
    "DE":"5431695798943363996","GH":"5434041611296192616","GR":"5434054805435724481",
    "GT":"5433935894971168754","GW":"5433775701280961741","GY":"5431676201007592926",
    "GN":"5434115081006756195","HN":"5434072118448894385","HU":"5434036689263670086",
    "IS":"5433628435442316429","ID":"5433884376838454074","IR":"5433882955204279044",
    "IQ":"5433749102548496991","IE":"5434155397864764491","IL":"5433810168393511493",
    "IT":"5434067655977874913","JM":"5433860784583096428","JP":"5431626087329182684",
    "JO":"5433643519367461444","KZ":"5433755347430946164","KE":"5433792670696748414",
    "KI":"5434004021742417775","XK":"5433884162090088194","KW":"5433820583689205435",
    "KG":"5433652375590025431","LA":"5431785473565537213","LV":"5433727778035872782",
    "LB":"5433872853441196535","LS":"5431620340662940910","LR":"5431414444225738871",
    "LY":"5433876972314836083","LI":"5433852744404317916","LT":"5434119663736862995",
    "LU":"5431669247455540884","MK":"5433626051735467592","MG":"5433833485770964033",
    "FM":"5433773682646332733","MW":"5433968339154122439","MY":"5434150334098327966",
    "MV":"5434010919459894038","ML":"5433943093336356065","MT":"5433598722858562967",
    "MH":"5434130474169544969","MR":"5433859405898594234","MU":"5431519649449653173",
    "MX":"5434064563601421981","MD":"5431428076451934112","MC":"5433798752370439037",
    "MN":"5433674924168328689","MA":"5434012796360604182","NA":"5431656358258685474",
    "NR":"5434131139889478358","NP":"5433895144321462723","NL":"5434026158003862063",
    "NZ":"5431350891594658893","NE":"5433737613510981562","NG":"5433836092816108548",
    "KP":"5434142701941437163","VE":"5294476442854247878","PK":"5291825606219029010",
    "PE":"5434098446598419585","CI":"5293991322003200135","PH":"5291798075478661634",
}

def _plain_flag(cc: str) -> str:
    code = (cc or "").upper()
    if len(code) != 2 or not code.isalpha(): return "🌍"
    return ''.join(chr(127397 + ord(c)) for c in code)

def premium_flag(cc: str, fallback=None) -> str:
    code = (cc or "").upper()
    custom = (THEME_CONFIG.get("country_flags", {}) if THEME_CONFIG else {}) or {}
    emoji_id = custom.get(code) or PREMIUM_FLAGS.get(code)
    if emoji_id:
        base = fallback or _plain_flag(code)
        return f'<tg-emoji emoji-id="{escape(emoji_id)}">{escape(base)}</tg-emoji>'
    return escape(fallback) if fallback else _plain_flag(code)

# ============================================================
#  ENV
# ============================================================
API_BASE_URL = _cfg("API_BASE_URL", "https://tempnumbers.net/api").rstrip("/")
API_TOKEN = _cfg("API_TOKEN", "")
TELEGRAM_BOT_TOKEN = _cfg("TELEGRAM_BOT_TOKEN")
_TG_CHAT_RAW = _cfg("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_CHAT_IDS: List[str] = [c.strip() for c in _TG_CHAT_RAW.replace(";", ",").split(",") if c.strip()]
WEBHOOK_HOST = _cfg("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = _cfg_int("WEBHOOK_PORT", 2379)
WEBHOOK_PATH = _cfg("WEBHOOK_PATH", "/webhook")
if not WEBHOOK_PATH.startswith("/"): WEBHOOK_PATH = "/" + WEBHOOK_PATH
WEBHOOK_SECRET = _cfg("WEBHOOK_SECRET", "").strip()

SITE_WEBHOOK_URL = _cfg("SITE_WEBHOOK_URL", "https://mrdarkvipx-001-site1.etempurl.com/webhook/main")

LAST_N_TO_FORWARD = _cfg_int("LAST_N_TO_FORWARD", 5)
TELEGRAM_UPDATES_INTERVAL = _cfg_float("TELEGRAM_UPDATES_INTERVAL", 2.0)
TELEGRAM_MAX_MESSAGE_LENGTH = 4000
BACKUP_CHANNEL_URL = _cfg("BACKUP_CHANNEL_URL", "https://t.me/numbervirtualfast")
NUMBER_CHANNEL_URL = _cfg("NUMBER_CHANNEL_URL", BACKUP_CHANNEL_URL)
USE_PREMIUM_EMOJI = _cfg_bool("USE_PREMIUM_EMOJI", True)
THEME_FILE = _cfg("BOT_THEME_FILE", "bot_theme.json").strip()
ADMIN_RAW = _cfg("ADMIN_IDS", _cfg("ADMIN_ID", "5076047031")).strip()
ADMIN_IDS = {int(x.strip()) for x in ADMIN_RAW.replace(";", ",").split(",") if x.strip().isdigit()}

missing = []
if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_CHAT_IDS: missing.append("TELEGRAM_CHAT_ID")
if missing: raise SystemExit(f"Missing config: {', '.join(missing)}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("tempnumbers_otp_bot")

# ============================================================
#  DEFAULT THEME
# ============================================================
DEFAULT_THEME: Dict[str, Any] = {
    "title":"PANEL B","show_title":False,"ui_mode":"premium","otp_style":"premium",
    "quote_message":False,"auto_delete_seconds":0,"silent_send":False,
    "protect_content":False,"pin_message":False,
    "ui":{
        "admin_tag_show":False,"country_show":True,"whatsapp_icon_show":True,
        "time_show":True,"otp_status_show":True,"copy_button_show":True,
        "main_channel_button_show":True,"number_channel_button_show":True,
        "language_show":True,"separator_style":"line","separator_custom":"",
        "separator_length":"medium","separator_custom_len":19,
        "app_name_short_show":True,"app_name_full_show":True,"app_name_show":True,
        "full_message_show":False,"flag_show":True,"number_show":True,
        "range_show":False,"cli_show":False,
        "field_order":["header","number","otp","time","language"],
        "label_number":"Number","label_otp":"Code","label_time":"Time",
        "label_country":"Country","label_service":"Service","label_language":"Lang",
        "number_mask_style":"middle","number_mask_custom":"",
        "otp_display_format":"split","otp_spoiler":False,
        "time_format":"full","time_custom_format":"","time_show_language":True,
        "country_display":"flag_name","app_display":"full",
        "header_text":"","header_emoji":"","footer_text":"","footer_emoji":"",
        "otp_bold":True,"otp_code_block":True,
    },
    "channels":{
        "copy_button_name":"OTP","main_channel_name":"Update",
        "main_channel_url":"https://t.me/numbervirtualfast",
        "number_channel_name":"Number","number_channel_url":"https://t.me/virtualnumberxd",
    },
    "style":{"button_style_primary":"primary","button_style_main":"danger","button_style_number":"success"},
    "button":{"text_template":"{name} • {otp}","rows_per_row":2},
    "premium_emoji_ids":{
        "APP_ICON":"","OTP_READY":"5307843983102204243","COPY_BUTTON":"5212921495008845628",
        "TIME":"6206344711859345194","NUMBER":"5318765591014678496",
        "MAIN_BUTTON":"5215668805199473901","NUMBER_BUTTON":"5247176827016847212",
        "SUCCESS":"5107126898501092348","WARNING":"",
    },
    "app_icons":{
        "whatsapp_business":"5188683998125106802","whatsapp":"5188683998125106802",
        "facebook":"5269631435731379598","instagram":"5364310996179503764",
        "telegram":"","google":"","gmail":"","microsoft":"","x":"","apple":"","icloud":"",
        "tiktok":"","discord":"","amazon":"","netflix":"","yahoo":"","paypal":"","bank":"",
        "chatgpt":"","bolt":"","default":"5938274774756103272",
    },
    "app_aliases":{},
    "country_flags":{
        "PE":"5434098446598419585","CI":"5293991322003200135","PH":"5291798075478661634",
    },
    "country_templates":{},"app_templates":{},
    "custom_templates":{
        "default":"{flag} {app_icon} {app} | {otp_icon} {otp} | {number_icon} {number} | {time_icon} {time}",
    },
    "chat_ids": TELEGRAM_CHAT_IDS.copy(),
}

THEME_CONFIG: Dict[str, Any] = {}
admin_state: Dict[int, Dict[str, str]] = {}
last_seen = deque(maxlen=5000)
recent_otps: Dict[Tuple[str, str], Tuple[str, datetime]] = {}
telegram_update_offset = 0
sent_messages_for_deletion: List[Tuple[str, int, float]] = []

def _deep_merge(base, over):
    m = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(m.get(k), dict):
            m[k] = _deep_merge(m[k], v)
        else: m[k] = v
    return m

def save_theme_config(data):
    global THEME_CONFIG
    THEME_CONFIG = _deep_merge(DEFAULT_THEME, data)
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            json.dump(THEME_CONFIG, f, indent=2, ensure_ascii=False)
    except Exception as e: logger.warning("save_theme_config: %s", e)

def load_theme_config():
    global THEME_CONFIG, TELEGRAM_CHAT_IDS
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            THEME_CONFIG = _deep_merge(DEFAULT_THEME, data if isinstance(data, dict) else {})
            if THEME_CONFIG.get("chat_ids"):
                TELEGRAM_CHAT_IDS.clear()
                TELEGRAM_CHAT_IDS.extend([str(c).strip() for c in THEME_CONFIG["chat_ids"] if str(c).strip()])
    except FileNotFoundError:
        THEME_CONFIG = _deep_merge(DEFAULT_THEME, {})
        save_theme_config(THEME_CONFIG)
    except Exception as e:
        logger.warning("load_theme_config: %s", e)
        THEME_CONFIG = _deep_merge(DEFAULT_THEME, {})
    return THEME_CONFIG

def theme_get(*keys, default=None):
    cur = THEME_CONFIG
    for k in keys:
        if not isinstance(cur, dict): return default
        cur = cur.get(k)
        if cur is None: return default
    return cur

def theme_set(path, value):
    data = _deep_merge(DEFAULT_THEME, THEME_CONFIG); cur = data
    for k in path[:-1]:
        if k not in cur or not isinstance(cur[k], dict): cur[k] = {}
        cur = cur[k]
    cur[path[-1]] = value
    save_theme_config(data)

def theme_toggle(path):
    data = _deep_merge(DEFAULT_THEME, THEME_CONFIG); cur = data
    for k in path[:-1]:
        if k not in cur or not isinstance(cur[k], dict): cur[k] = {}
        cur = cur[k]
    cur[path[-1]] = not bool(cur.get(path[-1], False))
    save_theme_config(data)
    return bool(cur[path[-1]])

load_theme_config()

# ============================================================
#  UTILITIES
# ============================================================
def html_safe(t): return escape(str(t or ""))

def tg_custom_emoji(eid, fb):
    fb = escape(fb or "📩")
    if USE_PREMIUM_EMOJI and eid:
        return f'<tg-emoji emoji-id="{escape(eid)}">{fb}</tg-emoji>'
    return fb

def premium_emoji(name, fb):
    return tg_custom_emoji(str(theme_get("premium_emoji_ids", name, default="") or ""), fb)

def is_admin(uid): return uid in ADMIN_IDS

def country_code_to_flag(cc):
    code = (cc or "").upper()
    if len(code) != 2: return "🌍"
    if USE_PREMIUM_EMOJI:
        try:
            custom = theme_get("country_flags", code, default="")
            if custom: return tg_custom_emoji(custom, _plain_flag(code))
            eid = PREMIUM_FLAGS.get(code)
            if eid: return tg_custom_emoji(eid, _plain_flag(code))
            return premium_flag(code)
        except Exception: pass
    return _plain_flag(code)

def detect_country(phone):
    try:
        n = phone.strip()
        if not n.startswith("+"): n = "+" + re.sub(r'^\D+', '', n)
        parsed = phonenumbers.parse(n, None)
        if parsed and phonenumbers.is_valid_number(parsed):
            cc = region_code_for_number(parsed) or ""
            name = geocoder.description_for_number(parsed, "en") or "Unknown"
            return country_code_to_flag(cc), name, cc
    except Exception: pass
    return "🌍", "Unknown", ""

APP_KEYWORDS = {
    "whatsapp business":("WhatsApp Business","WA-B"),"whatsapp":("WhatsApp","WA"),
    "facebook":("Facebook","FB"),"instagram":("Instagram","IG"),"telegram":("Telegram","TG"),
    "google":("Google","GG"),"gmail":("Gmail","GM"),"microsoft":("Microsoft","MS"),
    "x.com":("X.com","X"),"twitter":("Twitter","X"),"apple":("Apple","AP"),
    "icloud":("iCloud","IC"),"tiktok":("TikTok","TT"),"discord":("Discord","DS"),
    "amazon":("Amazon","AM"),"netflix":("Netflix","NF"),"yahoo":("Yahoo","YH"),
    "paypal":("PayPal","PP"),"bank":("Bank","BANK"),"chatgpt":("ChatGPT","AI"),
    "openai":("ChatGPT","AI"),"bolt":("Bolt","BOLT"),"truecaller":("Truecaller","TC"),
    "uber":("Uber","UB"),"snapchat":("Snapchat","SC"),"linkedin":("LinkedIn","LI"),
    "binance":("Binance","BN"),"revolut":("Revolut","RV"),"wise":("Wise","WS"),
    "tinder":("Tinder","TD"),"bumble":("Bumble","BB"),"signal":("Signal","SG"),
    "viber":("Viber","VB"),"line":("LINE","LN"),"wechat":("WeChat","WC"),
}
APP_EMOJIS = {
    "WhatsApp Business":"🟢","WhatsApp":"🟢","Facebook":"🔵","Instagram":"🟣","Telegram":"✈️",
    "Google":"🔴","Gmail":"📧","Microsoft":"🪟","X.com":"⚫️","Twitter":"⚫️","Apple":"🍎",
    "iCloud":"☁️","TikTok":"🎵","Discord":"🎮","Amazon":"📦","Netflix":"🎬","Yahoo":"💜",
    "PayPal":"💳","Bank":"🏦","ChatGPT":"🤖","Bolt":"⚡","Unknown":"📩",
    "Truecaller":"📞","Uber":"🚗","Snapchat":"👻","LinkedIn":"💼",
    "Binance":"🟡","Revolut":"💳","Wise":"💚","Tinder":"🔥","Bumble":"🐝",
    "Signal":"🔒","Viber":"📞","LINE":"💬","WeChat":"💬",
}

def normalize_app_icon_key(name):
    name = (name or "").strip().lower()
    mp = {"whatsapp business":"whatsapp_business","whatsapp":"whatsapp","facebook":"facebook",
          "instagram":"instagram","telegram":"telegram","google":"google","gmail":"gmail",
          "microsoft":"microsoft","x.com":"x","twitter":"x","x":"x","apple":"apple",
          "icloud":"icloud","tiktok":"tiktok","discord":"discord","amazon":"amazon",
          "netflix":"netflix","yahoo":"yahoo","paypal":"paypal","bank":"bank",
          "chatgpt":"chatgpt","openai":"chatgpt","bolt":"bolt","unknown":"default"}
    return mp.get(name, re.sub(r"[^a-z0-9]+","_",name).strip("_") or "default")

def get_app_icon(app_name):
    if not theme_get("ui","whatsapp_icon_show",default=True): return ""
    aliases = theme_get("app_aliases",default={}) or {}
    if app_name in aliases: return aliases[app_name]
    fb = APP_EMOJIS.get(app_name,"📩")
    key = normalize_app_icon_key(app_name)
    cid = str(theme_get("app_icons",key,default="") or "")
    if cid: return tg_custom_emoji(cid, fb)
    did = str(theme_get("app_icons","default",default="") or "")
    if did: return tg_custom_emoji(did, fb)
    return premium_emoji("APP_ICON", fb)

def detect_app(msg_text, cli_text=""):
    src = f"{cli_text or ''} {msg_text or ''}".lower()
    if not src.strip(): return ("Unknown","UNK")
    for k in sorted(APP_KEYWORDS.keys(), key=len, reverse=True):
        if k in src: return APP_KEYWORDS[k]
    return ("Unknown","UNK")

PREFIX_OTP = re.compile(r'\b(?:FB|META|IG|WA|WHATSAPP|GOOGLE|G|MICROSOFT|MS|APPLE|AP)[\s:\-]*([0-9]{4,8})\b', re.I)
CODEWORDS = re.compile(r'\b(code|otp|passcode|verification|verify|confirmation|login|security|2fa|one[-\s]?time|κωδικ)\b', re.I)
GEN_OTP = re.compile(r'(?<!\d)(?:\d{4,8}|\d{3}[-\s]?\d{3}|\d{4}[-\s]?\d{4})(?!\d)')

def extract_otp(msg):
    if not msg: return None
    flat = msg.replace("\n"," ").strip()
    m = PREFIX_OTP.search(flat)
    if m: return m.group(1)
    has_cw = bool(CODEWORDS.search(flat))
    cands = GEN_OTP.findall(flat)
    cleaned = [re.sub(r"\D","",c) for c in cands if 4 <= len(re.sub(r"\D","",c)) <= 8]
    if not cleaned: return None
    order = [6,5,4,7,8] if has_cw else [5,6,4,7,8]
    for L in order:
        for o in cleaned:
            if len(o) == L: return o
    cleaned.sort(key=len, reverse=True)
    return cleaned[0] if cleaned else None

def format_otp(otp):
    return re.sub(r'\D','', otp) if otp else "Not Found"

def format_otp_for_button(otp):
    d = re.sub(r"\D","", otp or "")
    if len(d) in (5,6): return f"{d[:3]}-{d[3:]}"
    return d or "OTP Not Found"

# ---------- FIELD FORMATTERS ----------
def format_number_by_style(num):
    style = str(theme_get("ui","number_mask_style",default="middle") or "middle").lower()
    custom = str(theme_get("ui","number_mask_custom",default="") or "")
    d = re.sub(r"\D","", num or "")
    if not d: return d
    if style in ("full","none"): return d
    if style == "first": return d[:4] + "•"*max(0,len(d)-4)
    if style == "last": return "•"*max(0,len(d)-4) + d[-4:]
    if style == "formatted":
        if len(d) >= 10: return f"+{d[:-10]} ({d[-10:-7]}) {d[-7:-4]}-{d[-4:]}"
        return d
    if style == "custom" and custom:
        out=[]; i=0
        for ch in custom:
            if ch=='#' and i < len(d): out.append(d[i]); i+=1
            else: out.append(ch)
        return ''.join(out)
    if len(d)>=10: return d[:5]+"•••"+d[-5:]
    if len(d)>=6: return d[:3]+"•••"+d[-3:]
    return d

def wrap_otp_html(otp):
    fmt = str(theme_get("ui","otp_display_format",default="split") or "split").lower()
    d = re.sub(r"\D","", otp or "")
    if not d: return "<code>Not Found</code>"
    if fmt == "spoiler": return f"<tg-spoiler><code>{d}</code></tg-spoiler>"
    if fmt == "pre": return f"<pre>{d}</pre>"
    if fmt == "bold": return f"<b>{d}</b>"
    if fmt == "boldcode": return f"<b><code>{d}</code></b>"
    if fmt == "blockquote": return f"<blockquote>{d}</blockquote>"
    if fmt == "boxed": return "<code>"+" ".join(f"[{x}]" for x in d)+"</code>"
    if fmt == "spaced": return "<code>"+" ".join(d)+"</code>"
    if fmt == "masked":
        if len(d)<=4: return f"<code>{d}</code>"
        return f"<code>{d[:2]}{'•'*(len(d)-4)}{d[-2:]}</code>"
    if fmt == "plain": return f"<code>{d}</code>"
    if len(d) in (5,6): return f"<code>{d[:3]}-{d[3:]}</code>"
    return f"<code>{d}</code>"

def format_time_by_style(dt_str):
    if not dt_str: return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y%m%d%H%M%S"):
        try:
            dt = datetime.strptime(dt_str, fmt); break
        except Exception: dt = None
    if dt is None:
        try: dt = datetime.fromisoformat(dt_str.replace("Z","+00:00"))
        except Exception: return dt_str
        
    fmt = str(theme_get("ui","time_format",default="full") or "full").lower()
    if fmt == "short": return dt.strftime("%H:%M")
    if fmt == "date_only": return dt.strftime("%d/%m/%Y")
    if fmt == "relative":
        try:
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            s = int((now-dt).total_seconds())
            if s < 60: return f"{s}s ago"
            if s < 3600: return f"{s//60}m ago"
            if s < 86400: return f"{s//3600}h ago"
            return f"{s//86400}d ago"
        except Exception: return dt_str
    if fmt == "custom":
        c = str(theme_get("ui","time_custom_format",default="") or "")
        if c:
            try: return dt.strftime(c)
            except Exception: pass
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_separator():
    style = str(theme_get("ui","separator_style",default="line") or "line").lower()
    length = str(theme_get("ui","separator_length",default="medium") or "medium").lower()
    custom = str(theme_get("ui","separator_custom",default="") or "")
    if style == "custom" and custom: return custom
    n = {"short":10,"long":28}.get(length, 19)
    if length == "custom":
        try: n = int(theme_get("ui","separator_custom_len",default=19))
        except Exception: n = 19
    return {"dash":"─"*n,"dot":"• "*((n+1)//2),"star":"✦ "*((n+1)//2),
            "wave":"~"*n,"arrow":"»"*n}.get(style,"━"*n)

def country_display_str(flag, country, iso):
    mode = str(theme_get("ui","country_display",default="flag_name") or "flag_name").lower()
    if mode == "full": return html_safe(country)
    if mode == "iso": return html_safe(iso.upper())
    if mode == "flag": return flag
    if mode == "flag_iso": return f"{flag} {html_safe(iso.upper())}"
    if mode == "flag_name_iso": return f"{flag} <b>{html_safe(country)}</b> ({html_safe(iso.upper())})"
    return f"{flag} <b>{html_safe(country)}</b>"

def app_display_str(full, short, icon):
    if not bool(theme_get("ui","app_name_show",default=True)): return ""
    icon_on = bool(theme_get("ui","whatsapp_icon_show",default=True))
    full_on = bool(theme_get("ui","app_name_full_show",default=True))
    short_on = bool(theme_get("ui","app_name_short_show",default=True))
    ic = icon if icon_on else ""
    mode = str(theme_get("ui","app_display",default="full") or "full").lower()
    tf = html_safe(full) if full_on else ""
    ts = html_safe(short) if short_on else ""
    if mode == "short": c = ts or tf; return f"{ic} {c}".strip() if ic else c
    if mode == "icon_only": return ic
    if mode == "icon_short": c = ts or tf; return f"{ic} {c}".strip() if ic else c
    if mode == "icon_full": c = tf or ts; return f"{ic} {c}".strip() if ic else c
    if tf: return f"{ic} <b>{tf}</b>".strip() if ic else f"<b>{tf}</b>"
    if ts: return f"{ic} <b>{ts}</b>".strip() if ic else f"<b>{ts}</b>"
    return ic

# ============================================================
#  TEMPLATE ENGINE
# ============================================================
def build_template_vars(flag,country,iso,af,ash,ai,num,otp,otp_show,tm,lang):
    return {"{flag}":flag,"{country}":html_safe(country),"{iso}":html_safe(iso.upper()),
            "{app}":html_safe(af),"{app_short}":html_safe(ash),"{app_icon}":ai,
            "{otp}":otp_show,"{otp_raw}":otp or "","{otp_split}":format_otp_for_button(otp),
            "{number}":html_safe(num),"{time}":html_safe(tm),"{language}":html_safe(lang),
            "{sep}":get_separator(),"{newline}":"\n",
            "{otp_icon}":premium_emoji("OTP_READY","🔑"),"{time_icon}":premium_emoji("TIME","🕒"),
            "{number_icon}":premium_emoji("NUMBER","📞"),"{lang_icon}":premium_emoji("SUCCESS","🌍"),
            "{header_emoji}":str(theme_get("ui","header_emoji",default="") or ""),
            "{footer_emoji}":str(theme_get("ui","footer_emoji",default="") or "")}

def apply_template(tpl, v):
    out = tpl
    for k,val in v.items(): out = out.replace(k, val)
    return out

# ============================================================
#  OTP KEYBOARD + RENDERERS
# ============================================================
def build_otp_keyboard(otp_digits, otp_show, country="", app=""):
    rows = []
    copy_name = str(theme_get("channels","copy_button_name",default="OTP") or "OTP")
    tpl = str(theme_get("button","text_template",default="{name} • {otp}") or "{name} • {otp}")
    txt = (tpl.replace("{name}",copy_name).replace("{otp}",otp_show)
              .replace("{otp_split}",otp_show).replace("{country}",country).replace("{app}",app))
    if theme_get("ui","copy_button_show",default=True):
        b = {"text":txt,"copy_text":{"text":otp_digits or "OTP Not Found"}}
        st = str(theme_get("style","button_style_primary",default="primary") or "").strip()
        ic = str(theme_get("premium_emoji_ids","COPY_BUTTON",default="") or "").strip()
        if st: b["style"] = st
        if ic: b["icon_custom_emoji_id"] = ic
        rows.append([b])
    row2 = []
    if theme_get("ui","main_channel_button_show",default=True):
        u = str(theme_get("channels","main_channel_url",default=BACKUP_CHANNEL_URL) or "").strip()
        if u:
            b = {"text":str(theme_get("channels","main_channel_name",default="Update") or "Update"),"url":u}
            st = str(theme_get("style","button_style_main",default="danger") or "").strip()
            ic = str(theme_get("premium_emoji_ids","MAIN_BUTTON",default="") or "").strip()
            if st: b["style"]=st
            if ic: b["icon_custom_emoji_id"]=ic
            row2.append(b)
    if theme_get("ui","number_channel_button_show",default=True):
        u = str(theme_get("channels","number_channel_url",default=NUMBER_CHANNEL_URL) or "").strip()
        if u:
            b = {"text":str(theme_get("channels","number_channel_name",default="Number") or "Number"),"url":u}
            st = str(theme_get("style","button_style_number",default="success") or "").strip()
            ic = str(theme_get("premium_emoji_ids","NUMBER_BUTTON",default="") or "").strip()
            if st: b["style"]=st
            if ic: b["icon_custom_emoji_id"]=ic
            row2.append(b)
    if row2: rows.append(row2)
    return {"inline_keyboard":rows} if rows else None

def render_otp_message_premium(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    ui_mode = str(theme_get("ui_mode",default="premium") or "premium").lower()
    sc = bool(theme_get("ui","country_show",default=True))
    st = bool(theme_get("ui","time_show",default=True))
    ss = bool(theme_get("ui","otp_status_show",default=True))
    sht = bool(theme_get("show_title",default=False))
    sa = bool(theme_get("ui","admin_tag_show",default=False))
    sf = bool(theme_get("ui","flag_show",default=True))
    sn = bool(theme_get("ui","number_show",default=True))
    sl = bool(theme_get("ui","language_show",default=True))
    title = str(theme_get("title",default="") or "").strip()
    ad = (af or ash or "Unknown").strip(); ash2 = (ash or ad or "APP").strip()
    if re.sub(r"\s+"," ",title).strip().lower() in {"",ad.lower(),ash2.lower(),"panel","panel b"}: title = ""
    tl = f"<b>{html_safe(title)}</b>" if sht and title else ""
    fd = flag if sf else ""
    cc = ("  •  " + country_display_str(fd,country,iso)) if (sc and country) else ""
    ac = "  •  <b>Admin</b>" if sa else ""
    astr = app_display_str(ad, ash2, ai)
    ni = premium_emoji("NUMBER","📞"); oi = premium_emoji("OTP_READY","🔑")
    ti = premium_emoji("TIME","🕒"); li = premium_emoji("SUCCESS","🌍")
    ln = str(theme_get("ui","label_number",default="Number") or "Number")
    lo = str(theme_get("ui","label_otp",default="Code") or "Code")
    otp_html = wrap_otp_html(otp_show); tstr = format_time_by_style(dt)
    hd = ""
    if theme_get("ui","header_text",default="") or theme_get("ui","header_emoji",default=""):
        hd = f"{theme_get('ui','header_emoji',default='')} {html_safe(theme_get('ui','header_text',default=''))}".strip()
    ft = ""
    if theme_get("ui","footer_text",default="") or theme_get("ui","footer_emoji",default=""):
        ft = f"{theme_get('ui','footer_emoji',default='')} {html_safe(theme_get('ui','footer_text',default=''))}".strip()
    sep = get_separator()
    if ui_mode == "compact":
        L=[]
        if hd: L.append(hd)
        if tl: L.append(tl)
        h = f"{astr}{cc}{ac}".strip()
        if h: L.append(h)
        if sn: L.append(f"{ni} <code>{html_safe(hidden)}</code>")
        if ss and otp_show != "Not Found": L.append(f"{oi} {otp_html}")
        if st:
            x = f"{ti} <code>{html_safe(tstr)}</code>"
            if sl: x += f" • {li} <b>{html_safe(lang)}</b>"
            L.append(x)
        elif sl: L.append(f"{li} <b>{html_safe(lang)}</b>")
        if ft: L.append(ft)
        return "\n".join(L)
    if ui_mode == "classic":
        L=[]
        if hd: L.append(hd)
        if tl: L.append(tl)
        h = f"{astr}{cc}{ac}".strip()
        if h: L.append(h)
        if sn: L.append(f"{ni} <b>{html_safe(ln)}:</b> <code>{html_safe(hidden)}</code>")
        if ss and otp_show != "Not Found": L.append(f"{oi} <b>{html_safe(lo)}:</b> {otp_html}")
        if st: L.append(f"{ti} <code>{html_safe(tstr)}</code>")
        if sl: L.append(f"{li} <b>{html_safe(lang)}</b>")
        if ft: L.append(ft)
        return "\n".join(L)
    L=[]
    if hd: L.append(hd)
    if tl: L.append(tl)
    h = f"{astr}{cc}{ac}".strip()
    if h: L.append(h)
    L.append(sep)
    if sn: L.append(f"{ni} <b>{html_safe(ln)}:</b> <code>{html_safe(hidden)}</code>")
    if ss and otp_show != "Not Found": L.append(f"{oi} <b>{html_safe(lo)}:</b> {otp_html}")
    L.append(sep)
    if st and sl: L.append(f"{ti} <code>{html_safe(tstr)}</code>  •  {li} <b>{html_safe(lang)}</b>")
    elif st: L.append(f"{ti} <code>{html_safe(tstr)}</code>")
    elif sl: L.append(f"{li} <b>{html_safe(lang)}</b>")
    if ft: L.append(ft)
    return "\n".join(L)

def render_otp_message_style1(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai)
    L=["╭─────────────────╮"]
    if a: L.append(f"│ {a}")
    L.append(f"│ {flag} <b>{html_safe(country)}</b>")
    L.append("├─────────────────┤")
    L.append(f"│ 📞 <code>{html_safe(hidden)}</code>")
    L.append(f"│ 🔑 {wrap_otp_html(otp_show)}")
    L.append(f"│ 🕒 <code>{html_safe(format_time_by_style(dt))}</code>")
    L.append("╰─────────────────╯")
    return "\n".join(L)

def render_otp_message_style2(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); p=[]
    if a: p.append(f"#{a}")
    p.append(f"#{iso}{flag}"); p.append(hidden); p.append(f"#OTP: {otp_show}"); p.append(f"#{lang}")
    return " ".join(p)

def render_otp_message_style3(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai)
    ti=premium_emoji("TIME","🕰"); ni=premium_emoji("NUMBER","📞"); oi=premium_emoji("OTP_READY","🔑")
    L=[f"{flag} New {country} OTP"]
    if a: L.append(f"📱 Service: {a}")
    L.append(f"{ti} Time: {html_safe(format_time_by_style(dt))}")
    L.append(f"🌍 Country: {html_safe(country)} {flag}")
    L.append(f"{ni} Number: {html_safe(hidden)}")
    L.append(f"{oi} OTP: {wrap_otp_html(otp_show)}")
    return "\n".join(L)

def render_otp_message_style4(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai)
    h = f"{flag} <b>{html_safe(country)}</b>"
    if a: h += f" · {a}"
    return f"{h}\n🔑 {wrap_otp_html(otp_show)}\n📞 <code>{html_safe(hidden)}</code>"

def render_otp_message_style5(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); L=[]
    if a: L.append(f"➤ {a}")
    L.append(f"➤ {flag} <b>{html_safe(country)}</b>")
    L.append(f"➤ 🔑 {wrap_otp_html(otp_show)}")
    L.append(f"➤ 📞 <code>{html_safe(hidden)}</code>")
    L.append(f"➤ 🕒 <code>{html_safe(format_time_by_style(dt))}</code>")
    return "\n".join(L)

def render_otp_message_style6(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); L=[]
    L.append(f"┌─[{a}]" if a else "┌─")
    L.append(f"├─[{flag} {html_safe(country)}]")
    L.append(f"├─[🔑 {otp_show}]")
    L.append(f"├─[📞 {html_safe(hidden)}]")
    L.append(f"└─[🕒 {html_safe(format_time_by_style(dt))}]")
    return "\n".join(L)

def render_otp_message_style7(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); hb=[]
    if a: hb.append(a)
    hb.append(f"{flag} <b>{html_safe(country)}</b>")
    return (f"{' | '.join(hb)}\n╔══════════════════╗\n║  <b>OTP: {html_safe(otp_show)}</b>  ║\n"
            f"╚══════════════════╝\n📞 <code>{html_safe(hidden)}</code> · 🕒 <code>{html_safe(format_time_by_style(dt))}</code>")

def render_otp_message_style8(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); L=["╔══════════════════════╗"]
    if a: L.append(f"║  {a}")
    L.append(f"║  {flag} {html_safe(country)}")
    L.append("╠══════════════════════╣")
    L.append(f"║  🔑 {wrap_otp_html(otp_show)}")
    L.append(f"║  📞 <code>{html_safe(hidden)}</code>")
    L.append(f"║  🕒 <code>{html_safe(format_time_by_style(dt))}</code>")
    L.append("╚══════════════════════╝")
    return "\n".join(L)

def render_otp_message_style9(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); L=["🔔 <b>NEW OTP</b> 🔔","━━━━━━━━━━━━━━━━"]
    if a: L.append(a)
    L.append(f"{flag} <b>{html_safe(country)}</b>")
    L.append(f"📞 <code>{html_safe(hidden)}</code>")
    L.append(f"🔐 {wrap_otp_html(otp_show)}")
    L.append(f"⏰ <code>{html_safe(format_time_by_style(dt))}</code>")
    L.append("━━━━━━━━━━━━━━━━")
    return "\n".join(L)

def render_otp_message_style10(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai); p=[]
    if a: p.append(a)
    p.append(flag); p.append(wrap_otp_html(otp_show)); p.append(f"<code>{html_safe(hidden)}</code>")
    return " · ".join(p)

def render_otp_message_style11(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    a = app_display_str(af,ash,ai)
    h = "⭐"
    if a: h += f" {a}"
    h += " ⭐"
    return (f"{h}\n{flag} {html_safe(country)}  •  🕒 <code>{html_safe(format_time_by_style(dt))}</code>\n"
            f"┌───────────────────┐\n│  {wrap_otp_html(otp_show)}  │\n└───────────────────┘\n📞 <code>{html_safe(hidden)}</code>")

def render_otp_message_custom(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    v = build_template_vars(flag,country,iso,af,ash,ai,hidden,otp_raw,otp_show,format_time_by_style(dt),lang)
    ct = theme_get("country_templates",default={}) or {}
    if iso and iso.upper() in ct: return apply_template(ct[iso.upper()], v)
    at = theme_get("app_templates",default={}) or {}
    if af in at: return apply_template(at[af], v)
    if ash in at: return apply_template(at[ash], v)
    tp = theme_get("custom_templates",default={}) or {}
    tpl = tp.get("default") or tp.get("active") or "{flag} {app_icon} {app} | {otp_icon} {otp} | {number_icon} {number} | {time_icon} {time}"
    return apply_template(tpl, v)

OTP_STYLES = {
    "premium":render_otp_message_premium,"style1":render_otp_message_style1,
    "style2":render_otp_message_style2,"style3":render_otp_message_style3,
    "style4":render_otp_message_style4,"style5":render_otp_message_style5,
    "style6":render_otp_message_style6,"style7":render_otp_message_style7,
    "style8":render_otp_message_style8,"style9":render_otp_message_style9,
    "style10":render_otp_message_style10,"style11":render_otp_message_style11,
    "custom":render_otp_message_custom,
}

def render_otp_message(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt):
    fn = OTP_STYLES.get(str(theme_get("otp_style",default="premium") or "premium").lower(), render_otp_message_premium)
    return fn(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt)

# ============================================================
#  TELEGRAM API
# ============================================================
async def telegram_api(session, method, payload=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    async with session.post(url, json=payload or {}) as r:
        try: data = await r.json(content_type=None)
        except Exception:
            text = await r.text()
            raise RuntimeError(f"TG {method} failed: {r.status} {text[:200]}")
        if r.status != 200 or not data.get("ok"): raise RuntimeError(f"TG {method} failed: {data}")
        return data

async def tg_send_message(session, chat_id, text, reply_markup=None, reply_to=None):
    p = {"chat_id":chat_id,"text":text[:TELEGRAM_MAX_MESSAGE_LENGTH],
         "parse_mode":"HTML","disable_web_page_preview":True}
    if theme_get("silent_send",default=False): p["disable_notification"] = True
    if theme_get("protect_content",default=False): p["protect_content"] = True
    if reply_markup: p["reply_markup"] = reply_markup
    if reply_to: p["reply_to_message_id"] = reply_to
    try:
        d = await telegram_api(session,"sendMessage",p)
        return d.get("result",{}).get("message_id")
    except Exception as e:
        err = str(e).lower()
        if reply_to and ("reply message not found" in err or "message to be replied not found" in err):
            p.pop("reply_to_message_id",None)
            try:
                d = await telegram_api(session,"sendMessage",p)
                return d.get("result",{}).get("message_id")
            except Exception: logger.exception("send retry"); return None
        logger.exception("sendMessage"); return None

async def tg_delete_message(session, chat_id, mid):
    try: await telegram_api(session,"deleteMessage",{"chat_id":chat_id,"message_id":mid})
    except Exception: pass

async def tg_pin_message(session, chat_id, mid):
    try: await telegram_api(session,"pinChatMessage",{"chat_id":chat_id,"message_id":mid,"disable_notification":True})
    except Exception: pass

async def tg_edit_message(session, chat_id, mid, text, kb=None):
    p = {"chat_id":chat_id,"message_id":mid,"text":text[:TELEGRAM_MAX_MESSAGE_LENGTH],
         "parse_mode":"HTML","disable_web_page_preview":True}
    if kb: p["reply_markup"] = kb
    try: await telegram_api(session,"editMessageText",p)
    except Exception: logger.exception("editMessageText")

async def tg_answer_callback(session, cqid, text=""):
    p = {"callback_query_id":cqid}
    if text: p["text"] = text[:180]
    try: await telegram_api(session,"answerCallbackQuery",p)
    except Exception: pass

async def tg_get_updates(session, offset):
    try:
        d = await telegram_api(session,"getUpdates",{"timeout":0,"offset":offset,
                                                     "allowed_updates":["message","callback_query"]})
        return d.get("result",[]) if isinstance(d, dict) else []
    except Exception as e:
        if "409" in str(e): return []
        logger.exception("getUpdates"); return []

# ============================================================
#  PREVIEW + SEND
# ============================================================
def preview_sample():
    return {"flag":"🇧🇩","country":"Bangladesh","iso":"BD","app_full":"WhatsApp","app_short":"WA",
            "app_icon":get_app_icon("WhatsApp"),"hidden_number":format_number_by_style("8801712345678"),
            "otp_show":"123-456","otp_raw":"123456","language_name":"English",
            "msg_dt":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

def render_preview():
    s = preview_sample()
    return render_otp_message(s["flag"],s["country"],s["iso"],s["app_full"],s["app_short"],
                              s["app_icon"],s["hidden_number"],s["otp_show"],s["otp_raw"],
                              s["language_name"],s["msg_dt"])

async def send_otp_one(session, chat_id, flag, country, iso, af, ash, ai, hidden,
                       formatted, otp_raw, lang, raw_msg, dt, reply_to=None):
    otp_digits = re.sub(r"\D","", formatted or "")
    otp_show = format_otp_for_button(formatted)
    txt = render_otp_message(flag,country,iso,af,ash,ai,hidden,otp_show,otp_raw,lang,dt)
    kb = build_otp_keyboard(otp_digits, otp_show, country=country, app=af)
    mid = await tg_send_message(session, chat_id, txt, kb, reply_to)
    if mid and theme_get("pin_message",default=False):
        await tg_pin_message(session, chat_id, mid)
    ad = int(theme_get("auto_delete_seconds",default=0) or 0)
    if mid and ad > 0:
        sent_messages_for_deletion.append((str(chat_id), int(mid), time.time()+ad))
    logger.info("✅ OTP sent: chat=%s country=%s app=%s", chat_id, country, af)

async def broadcast_otp(session, flag, country, iso, af, ash, ai, hidden,
                        formatted, otp_raw, lang, raw_msg, dt):
    reply_to = None
    if theme_get("quote_message",default=False):
        try:
            ups = await tg_get_updates(session, 0)
            for u in reversed(ups or []):
                m = u.get("message")
                if m and str(m.get("chat",{}).get("id")) in TELEGRAM_CHAT_IDS:
                    reply_to = m.get("message_id"); break
        except Exception: pass
    for cid in TELEGRAM_CHAT_IDS:
        await send_otp_one(session, cid, flag, country, iso, af, ash, ai, hidden,
                           formatted, otp_raw, lang, raw_msg, dt, reply_to)

async def auto_delete_worker(session):
    while True:
        now = time.time(); keep = []
        for cid, mid, when in list(sent_messages_for_deletion):
            if when <= now: await tg_delete_message(session, cid, mid)
            else: keep.append((cid, mid, when))
        sent_messages_for_deletion.clear(); sent_messages_for_deletion.extend(keep)
        await asyncio.sleep(3)

# ============================================================
#  WEBHOOK HANDLER
# ============================================================
def make_unique_id(msg):
    if not isinstance(msg, dict): return ""
    for k in ("id","msgid","message_id"):
        if msg.get(k): return str(msg[k])
    return hashlib.sha256(f"{msg.get('time','')}|{msg.get('number','')}|{msg.get('content','')}|{msg.get('cli','')}".encode()).hexdigest()

async def process_incoming_sms(session, msg):
    try:
        dt = str(msg.get("time","") or "")
        num = str(msg.get("number","") or "")
        body = str(msg.get("content","") or "")
        cli = str(msg.get("cli","") or "")
        if not dt or not num or not body:
            logger.warning("Incomplete webhook payload: %s", msg); return
        uid = make_unique_id(msg)
        if uid in last_seen:
            logger.info("Duplicate webhook (uid=%s) skipped", uid[:12]); return
        last_seen.append(uid)

        otp_raw = extract_otp(body)
        formatted = format_otp(otp_raw)
        flag, country, iso = detect_country(num)
        af, ash = detect_app(body, cli)
        ai = get_app_icon(af)
        lang = detect_language_name(body)
        num_digits = re.sub(r'\D','', num)
        hidden = format_number_by_style(num_digits)

        if otp_raw:
            now_utc = datetime.now(timezone.utc)
            key = (num_digits, af)
            digits = re.sub(r'\D','', otp_raw)
            prev = recent_otps.get(key)
            if prev and prev[0] == digits and (now_utc - prev[1]) < timedelta(minutes=2):
                logger.info("Recent duplicate OTP skipped"); return
            recent_otps[key] = (digits, now_utc)

        logger.info("Webhook SMS: dt=%s num=%s cli=%s otp=%s", dt, num, cli, formatted)
        await broadcast_otp(session, flag, country, iso, af, ash, ai, hidden,
                            formatted, otp_raw or "", lang, body, dt)
    except Exception:
        logger.exception("process_incoming_sms failed")

async def webhook_handler(request):
    logger.info("📥 WEBHOOK HIT! From IP: %s", request.remote)
    if WEBHOOK_SECRET:
        provided = request.query.get("secret") or request.headers.get("X-Webhook-Secret","")
        if provided != WEBHOOK_SECRET:
            return web.json_response({"status":"error","message":"unauthorized"}, status=401)
            
    try:
        raw_body = await request.text()
        logger.info("📦 RAW BODY RECEIVED: %s", raw_body)
        body = json.loads(raw_body)
        
        # FIX: Double JSON Decode for TempNumbers String payload
        if isinstance(body, str):
            body = json.loads(body)
            
    except Exception as e:
        logger.error("❌ Invalid JSON received: %s", e)
        return web.json_response({"status":"error","message":"invalid json"}, status=400)

    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        logger.warning("⚠️ Payload missing 'data' key")
        return web.json_response({"status":"error","message":"missing data"}, status=400)

    msg = {
        "time": str(data.get("datetime","") or ""),
        "number": str(data.get("num","") or ""),
        "cli": str(data.get("cli","") or ""),
        "content": str(data.get("sms","") or ""),
        "range": str(data.get("rid","") or ""),
        "clientId": str(body.get("clientId","") or ""),
        "inpayout": data.get("inpayout",""),
        "clpayout": data.get("clpayout",""),
        "currency": data.get("currency",""),
        "client": data.get("client",""),
    }
    session = request.app.get("session")
    if session and not session.closed:
        asyncio.create_task(process_incoming_sms(session, msg))

    # --- Send to your website (SmarterASP.net) ---
    try:
        site_payload = {
            "data": {  # <--- ডাটা 'data' কী-এর ভেতরে পাঠানো হচ্ছে
                "num": msg["number"],
                "cli": msg["cli"],
                "sms": msg["content"],
                "datetime": msg["time"]
            }
        }
        headers = {
            "X-Webhook-Token": "b014bba0e82a781d4bc33ede97dab69c0ea1c36c565bc260b75de221537a1c01",
            "Content-Type": "application/json"
        }
        async with session.post(SITE_WEBHOOK_URL, json=site_payload, headers=headers) as resp:
            logger.info(f"Website Webhook sent: {resp.status}")
    except Exception as e:
        logger.error(f"Failed to send to Website: {e}")

    return web.json_response({"status":"success","message":"accepted"})

async def health_handler(request):
    return web.json_response({"status":"ok","service":"otp-bot","chats": len(TELEGRAM_CHAT_IDS)})

async def run_webhook_server(session):
    app = web.Application(client_max_size=1024*512)
    app["session"] = session
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBHOOK_HOST, WEBHOOK_PORT)
    await site.start()
    logger.info("🌐 Webhook server listening: http://%s:%s%s", WEBHOOK_HOST, WEBHOOK_PORT, WEBHOOK_PATH)
    while True:
        await asyncio.sleep(3600)

# ============================================================
#  ADMIN PANEL (Menus)
# ============================================================
def menu_home():
    return {"inline_keyboard": [
        [{"text": "🎛 UI Control", "callback_data": "admin:ui"}, {"text": "🔘 Buttons", "callback_data": "admin:buttons"}],
        [{"text": "✨ Emoji", "callback_data": "admin:emoji"}, {"text": "📱 App Icons", "callback_data": "admin:appicons"}],
        [{"text": "🎨 Theme", "callback_data": "admin:themes"}, {"text": "📝 OTP Style", "callback_data": "admin:otpstyle"}],
        [{"text": "📐 Layout & Fields", "callback_data": "admin:layout"}],
        [{"text": "📋 Templates", "callback_data": "admin:templates"}],
        [{"text": "🌐 Per-Country Templates", "callback_data": "admin:ctemplates"}],
        [{"text": "📲 Per-App Templates", "callback_data": "admin:atemplates"}],
        [{"text": "💠 App Aliases", "callback_data": "admin:aliases"}],
        [{"text": "🔢 Number Format", "callback_data": "admin:numformat"}],
        [{"text": "🕒 Time Format", "callback_data": "admin:timeformat"}],
        [{"text": "🏳️ Country Flags", "callback_data": "admin:flags"}],
        [{"text": "👥 Chat IDs", "callback_data": "admin:chatids"}],
        [{"text": "⚙️ Advanced", "callback_data": "admin:advanced"}],
        [{"text": "👁 Live Preview", "callback_data": "admin:preview"}],
        [{"text": "🔄 Reload Config", "callback_data": "admin:reload"}, {"text": "♻ Reset Theme", "callback_data": "admin:reset"}],
    ]}

def menu_ui():
    m = lambda v: "✅" if v else "❌"
    return {"inline_keyboard": [
        [{"text": f"Title {m(bool(theme_get('show_title', default=False)))}", "callback_data": "toggle:root:show_title"}],
        [{"text": f"Admin Tag {m(bool(theme_get('ui','admin_tag_show', default=False)))}", "callback_data": "toggle:ui:admin_tag_show"}],
        [{"text": f"Country {m(bool(theme_get('ui','country_show', default=True)))}", "callback_data": "toggle:ui:country_show"}],
        [{"text": f"Flag {m(bool(theme_get('ui','flag_show', default=True)))}", "callback_data": "toggle:ui:flag_show"}],
        [{"text": f"App Icon {m(bool(theme_get('ui','whatsapp_icon_show', default=True)))}", "callback_data": "toggle:ui:whatsapp_icon_show"}],
        [{"text": f"App Name (MASTER) {m(bool(theme_get('ui','app_name_show', default=True)))}", "callback_data": "toggle:ui:app_name_show"}],
        [{"text": f"App Full Name {m(bool(theme_get('ui','app_name_full_show', default=True)))}", "callback_data": "toggle:ui:app_name_full_show"}],
        [{"text": f"App Short Name {m(bool(theme_get('ui','app_name_short_show', default=True)))}", "callback_data": "toggle:ui:app_name_short_show"}],
        [{"text": f"Time {m(bool(theme_get('ui','time_show', default=True)))}", "callback_data": "toggle:ui:time_show"}],
        [{"text": f"Language {m(bool(theme_get('ui','language_show', default=True)))}", "callback_data": "toggle:ui:language_show"}],
        [{"text": f"Number {m(bool(theme_get('ui','number_show', default=True)))}", "callback_data": "toggle:ui:number_show"}],
        [{"text": f"OTP Status {m(bool(theme_get('ui','otp_status_show', default=True)))}", "callback_data": "toggle:ui:otp_status_show"}],
        [{"text": "⬅ Back", "callback_data": "admin:home"}],
    ]}

def menu_buttons():
    m = lambda k: "✅" if theme_get("ui", k, default=False) else "❌"
    return {"inline_keyboard": [
        [{"text": f"Copy Button {m('copy_button_show')}", "callback_data": "toggle:ui:copy_button_show"}],
        [{"text": f"Main Channel {m('main_channel_button_show')}", "callback_data": "toggle:ui:main_channel_button_show"}],
        [{"text": f"Number Channel {m('number_channel_button_show')}", "callback_data": "toggle:ui:number_channel_button_show"}],
        [{"text": "✏ Copy Name", "callback_data": "set:copy_button_name"}, {"text": "✍ Title", "callback_data": "set:title"}],
        [{"text": "✏ Main Name", "callback_data": "set:main_channel_name"}],
        [{"text": "✏ Number Name", "callback_data": "set:number_channel_name"}],
        [{"text": "🔗 Main URL", "callback_data": "set:main_channel_url"}],
        [{"text": "🔗 Number URL", "callback_data": "set:number_channel_url"}],
        [{"text": "📝 Button Text Template", "callback_data": "admin:btntemplate"}],
        [{"text": "⬅ Back", "callback_data": "admin:home"}],
    ]}

def menu_emoji():
    keys = ["APP_ICON", "OTP_READY", "COPY_BUTTON", "TIME", "NUMBER", "MAIN_BUTTON", "NUMBER_BUTTON", "SUCCESS", "WARNING"]
    rows = [[{"text": k, "callback_data": f"emoji:{k}"}] for k in keys]
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_app_icons():
    rows = [
        [{"text": "WhatsApp Business", "callback_data": "appemoji:whatsapp_business"}, {"text": "WhatsApp", "callback_data": "appemoji:whatsapp"}],
        [{"text": "Instagram", "callback_data": "appemoji:instagram"}, {"text": "Facebook", "callback_data": "appemoji:facebook"}],
        [{"text": "Telegram", "callback_data": "appemoji:telegram"}, {"text": "TikTok", "callback_data": "appemoji:tiktok"}],
        [{"text": "Google", "callback_data": "appemoji:google"}, {"text": "Gmail", "callback_data": "appemoji:gmail"}],
        [{"text": "Apple", "callback_data": "appemoji:apple"}, {"text": "iCloud", "callback_data": "appemoji:icloud"}],
        [{"text": "Amazon", "callback_data": "appemoji:amazon"}, {"text": "Netflix", "callback_data": "appemoji:netflix"}],
        [{"text": "Discord", "callback_data": "appemoji:discord"}, {"text": "Microsoft", "callback_data": "appemoji:microsoft"}],
        [{"text": "PayPal", "callback_data": "appemoji:paypal"}, {"text": "Bank", "callback_data": "appemoji:bank"}],
        [{"text": "ChatGPT", "callback_data": "appemoji:chatgpt"}, {"text": "X", "callback_data": "appemoji:x"}],
        [{"text": "Bolt", "callback_data": "appemoji:bolt"}, {"text": "Truecaller", "callback_data": "appemoji:truecaller"}],
        [{"text": "Uber", "callback_data": "appemoji:uber"}, {"text": "Snapchat", "callback_data": "appemoji:snapchat"}],
        [{"text": "LinkedIn", "callback_data": "appemoji:linkedin"}, {"text": "Binance", "callback_data": "appemoji:binance"}],
        [{"text": "Revolut", "callback_data": "appemoji:revolut"}, {"text": "Wise", "callback_data": "appemoji:wise"}],
        [{"text": "Default App Icon", "callback_data": "appemoji:default"}],
        [{"text": "⬅ Back", "callback_data": "admin:home"}],
    ]
    return {"inline_keyboard": rows}

def menu_themes():
    current = str(theme_get("ui_mode", default="premium"))
    return {"inline_keyboard": [
        [{"text": f"Classic {'✅' if current == 'classic' else ''}".strip(), "callback_data": "theme:classic"}],
        [{"text": f"Premium {'✅' if current == 'premium' else ''}".strip(), "callback_data": "theme:premium"}],
        [{"text": f"Compact {'✅' if current == 'compact' else ''}".strip(), "callback_data": "theme:compact"}],
        [{"text": f"Copy Style: {theme_get('style','button_style_primary', default='primary')}", "callback_data": "style:button_style_primary"}],
        [{"text": f"Main Btn Style: {theme_get('style','button_style_main', default='danger')}", "callback_data": "style:button_style_main"}],
        [{"text": f"Number Btn Style: {theme_get('style','button_style_number', default='success')}", "callback_data": "style:button_style_number"}],
        [{"text": "🔧 Separator Style", "callback_data": "admin:separator"}],
        [{"text": "⬅ Back", "callback_data": "admin:home"}],
    ]}

def menu_separator():
    cur_style = str(theme_get("ui", "separator_style", default="line"))
    cur_len = str(theme_get("ui", "separator_length", default="medium"))
    return {"inline_keyboard": [
        [{"text": f"line {'✅' if cur_style == 'line' else ''}", "callback_data": "sep:line"}, {"text": f"dash {'✅' if cur_style == 'dash' else ''}", "callback_data": "sep:dash"}],
        [{"text": f"dot {'✅' if cur_style == 'dot' else ''}", "callback_data": "sep:dot"}, {"text": f"star {'✅' if cur_style == 'star' else ''}", "callback_data": "sep:star"}],
        [{"text": f"wave {'✅' if cur_style == 'wave' else ''}", "callback_data": "sep:wave"}, {"text": f"arrow {'✅' if cur_style == 'arrow' else ''}", "callback_data": "sep:arrow"}],
        [{"text": "✏ Custom Separator", "callback_data": "setsep:custom"}],
        [{"text": f"Short {'✅' if cur_len == 'short' else ''}", "callback_data": "seplen:short"}, {"text": f"Medium {'✅' if cur_len == 'medium' else ''}", "callback_data": "seplen:medium"}, {"text": f"Long {'✅' if cur_len == 'long' else ''}", "callback_data": "seplen:long"}],
        [{"text": f"Custom Len ({theme_get('ui','separator_custom_len', default=19)})", "callback_data": "setsep:custom_len"}],
        [{"text": "⬅ Back", "callback_data": "admin:themes"}],
    ]}

def menu_otpstyle():
    cur = str(theme_get("otp_style", default="premium"))
    opts = [
        ("premium", "Premium"), ("style1", "Style1 Box"), ("style2", "Style2 Tag"),
        ("style3", "Style3 Detail"), ("style4", "Style4 Minimal"), ("style5", "Style5 Arrow"),
        ("style6", "Style6 Bracket"), ("style7", "Style7 BoldOTP"), ("style8", "Style8 Card"),
        ("style9", "Style9 EmojiRich"), ("style10", "Style10 Single"), ("style11", "Style11 Star"),
        ("custom", "Custom Template"),
    ]
    rows = []
    for key, label in opts:
        rows.append([{"text": f"{label} {'✅' if cur == key else ''}".strip(), "callback_data": f"otpstyle:{key}"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_layout():
    return {"inline_keyboard": [
        [{"text": "📋 OTP Display Format", "callback_data": "admin:otpdisplay"}],
        [{"text": f"OTP Bold {'✅' if theme_get('ui','otp_bold', default=True) else '❌'}", "callback_data": "toggle:ui:otp_bold"}],
        [{"text": "🏷 Field Labels", "callback_data": "admin:labels"}],
        [{"text": "📌 Header & Footer", "callback_data": "admin:headerfooter"}],
        [{"text": "🌐 Country Display Mode", "callback_data": "admin:countrymode"}],
        [{"text": "📱 App Display Mode", "callback_data": "admin:appmode"}],
        [{"text": "⬅ Back", "callback_data": "admin:home"}],
    ]}

def menu_otpdisplay():
    cur = str(theme_get("ui", "otp_display_format", default="split"))
    opts = ["plain", "split", "spaced", "masked", "boxed", "spoiler", "pre", "bold", "boldcode", "blockquote"]
    rows = [[{"text": f"{o} {'✅' if cur == o else ''}".strip(), "callback_data": f"otpfmt:{o}"}] for o in opts]
    rows.append([{"text": "⬅ Back", "callback_data": "admin:layout"}])
    return {"inline_keyboard": rows}

def menu_labels():
    return {"inline_keyboard": [
        [{"text": f"Number → {theme_get('ui','label_number', default='Number')}", "callback_data": "setlabel:label_number"}],
        [{"text": f"OTP → {theme_get('ui','label_otp', default='Code')}", "callback_data": "setlabel:label_otp"}],
        [{"text": f"Time → {theme_get('ui','label_time', default='Time')}", "callback_data": "setlabel:label_time"}],
        [{"text": f"Country → {theme_get('ui','label_country', default='Country')}", "callback_data": "setlabel:label_country"}],
        [{"text": f"Service → {theme_get('ui','label_service', default='Service')}", "callback_data": "setlabel:label_service"}],
        [{"text": f"Language → {theme_get('ui','label_language', default='Lang')}", "callback_data": "setlabel:label_language"}],
        [{"text": "⬅ Back", "callback_data": "admin:layout"}],
    ]}

def menu_headerfooter():
    return {"inline_keyboard": [
        [{"text": f"Header Text: {theme_get('ui','header_text', default='') or '(empty)'}", "callback_data": "setlabel:header_text"}],
        [{"text": f"Header Emoji: {theme_get('ui','header_emoji', default='') or '(empty)'}", "callback_data": "setlabel:header_emoji"}],
        [{"text": f"Footer Text: {theme_get('ui','footer_text', default='') or '(empty)'}", "callback_data": "setlabel:footer_text"}],
        [{"text": f"Footer Emoji: {theme_get('ui','footer_emoji', default='') or '(empty)'}", "callback_data": "setlabel:footer_emoji"}],
        [{"text": "⬅ Back", "callback_data": "admin:layout"}],
    ]}

def menu_countrymode():
    cur = str(theme_get("ui", "country_display", default="flag_name"))
    opts = [("full", "Full Name"), ("iso", "ISO Code"), ("flag", "Flag Only"),
            ("flag_iso", "Flag + ISO"), ("flag_name", "Flag + Name"), ("flag_name_iso", "Flag + Name + ISO")]
    rows = [[{"text": f"{l} {'✅' if cur == k else ''}".strip(), "callback_data": f"cmode:{k}"}] for k, l in opts]
    rows.append([{"text": "⬅ Back", "callback_data": "admin:layout"}])
    return {"inline_keyboard": rows}

def menu_appmode():
    cur = str(theme_get("ui", "app_display", default="full"))
    opts = [("full", "Full Name"), ("short", "Short Code"), ("icon_only", "Icon Only"),
            ("icon_short", "Icon + Short"), ("icon_full", "Icon + Full")]
    rows = [[{"text": f"{l} {'✅' if cur == k else ''}".strip(), "callback_data": f"amode:{k}"}] for k, l in opts]
    rows.append([{"text": "⬅ Back", "callback_data": "admin:layout"}])
    return {"inline_keyboard": rows}

def menu_templates():
    templates = theme_get("custom_templates", default={}) or {}
    rows = []
    for name in list(templates.keys())[:8]:
        rows.append([{"text": f"✏ {name}", "callback_data": f"tpl:edit:{name}"}, {"text": "🗑", "callback_data": f"tpl:del:{name}"}])
    rows.append([{"text": "➕ Add New Template", "callback_data": "tpl:add"}])
    rows.append([{"text": "📌 Set Active Template", "callback_data": "tpl:setactive"}])
    rows.append([{"text": "📖 Variables Help", "callback_data": "tpl:help"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_ctemplates():
    ct = theme_get("country_templates", default={}) or {}
    rows = []
    for iso in list(ct.keys())[:8]:
        rows.append([{"text": f"✏ {iso}", "callback_data": f"ctpl:edit:{iso}"}, {"text": "🗑", "callback_data": f"ctpl:del:{iso}"}])
    rows.append([{"text": "➕ Add Country Template", "callback_data": "ctpl:add"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_atemplates():
    at = theme_get("app_templates", default={}) or {}
    rows = []
    for app in list(at.keys())[:8]:
        rows.append([{"text": f"✏ {app}", "callback_data": f"atpl:edit:{app}"}, {"text": "🗑", "callback_data": f"atpl:del:{app}"}])
    rows.append([{"text": "➕ Add App Template", "callback_data": "atpl:add"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_aliases():
    aliases = theme_get("app_aliases", default={}) or {}
    rows = []
    for app in list(aliases.keys())[:8]:
        rows.append([{"text": f"✏ {app} → {aliases[app]}", "callback_data": f"alias:edit:{app}"}, {"text": "🗑", "callback_data": f"alias:del:{app}"}])
    rows.append([{"text": "➕ Add Alias", "callback_data": "alias:add"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_numformat():
    cur = str(theme_get("ui", "number_mask_style", default="middle"))
    opts = [("middle", "Middle Mask"), ("first", "First 4 Only"), ("last", "Last 4 Only"),
            ("full", "Full Number"), ("formatted", "Formatted"), ("custom", "Custom (# placeholders)")]
    rows = [[{"text": f"{l} {'✅' if cur == k else ''}".strip(), "callback_data": f"numfmt:{k}"}] for k, l in opts]
    if cur == "custom":
        rows.insert(0, [{"text": f"✏ Pattern: {theme_get('ui','number_mask_custom', default='') or '(empty)'}", "callback_data": "setlabel:number_mask_custom"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_timeformat():
    cur = str(theme_get("ui", "time_format", default="full"))
    opts = [("full", "Full"), ("short", "Short (14:30)"),
            ("date_only", "Date Only"), ("relative", "Relative (5m ago)"),
            ("custom", "Custom strftime")]
    rows = [[{"text": f"{l} {'✅' if cur == k else ''}".strip(), "callback_data": f"timefmt:{k}"}] for k, l in opts]
    if cur == "custom":
        rows.insert(0, [{"text": f"✏ Format: {theme_get('ui','time_custom_format', default='') or '(empty)'}", "callback_data": "setlabel:time_custom_format"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_flags():
    flags = theme_get("country_flags", default={}) or {}
    flag_items = list(flags.items())[:10]
    rows = []
    for code, emoji_id in flag_items:
        flag_display = country_code_to_flag(code)
        rows.append([{"text": f"{flag_display} {code} → {emoji_id[:8]}...", "callback_data": f"flag:{code}"}])
    rows.append([{"text": "➕ Add Flag", "callback_data": "flag:add"}])
    rows.append([{"text": "📋 List All", "callback_data": "flag:list"}])
    rows.append([{"text": "🗑 Clear All", "callback_data": "flag:clear"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_chatids():
    chat_ids = theme_get("chat_ids", default=[]) or []
    rows = []
    for i, chat_id in enumerate(chat_ids[:10]):
        rows.append([{"text": f"❌ Remove {chat_id}", "callback_data": f"chatid:remove:{i}"}])
    if len(chat_ids) > 10:
        rows.append([{"text": f"... and {len(chat_ids) - 10} more", "callback_data": "chatid:list"}])
    rows.append([{"text": "➕ Add Chat ID", "callback_data": "chatid:add"}])
    rows.append([{"text": "📋 List All", "callback_data": "chatid:list"}])
    rows.append([{"text": "⬅ Back", "callback_data": "admin:home"}])
    return {"inline_keyboard": rows}

def menu_advanced():
    m = lambda v: "✅" if v else "❌"
    return {"inline_keyboard": [
        [{"text": f"Quote Mode {m(bool(theme_get('quote_message', default=False)))}", "callback_data": "toggle:root:quote_message"}],
        [{"text": f"Silent Send {m(bool(theme_get('silent_send', default=False)))}", "callback_data": "toggle:root:silent_send"}],
        [{"text": f"Protect Content {m(bool(theme_get('protect_content', default=False)))}", "callback_data": "toggle:root:protect_content"}],
        [{"text": f"Pin Message {m(bool(theme_get('pin_message', default=False)))}", "callback_data": "toggle:root:pin_message"}],
        [{"text": f"Auto-Delete: {int(theme_get('auto_delete_seconds', default=0) or 0)}s", "callback_data": "setlabel:auto_delete_seconds"}],
        [{"text": "⬅ Back", "callback_data": "admin:home"}],
    ]}

def admin_home_text():
    chat_count = len(theme_get("chat_ids", default=[]))
    flag_count = len(theme_get("country_flags", default={}) or {})
    tpl_count = len(theme_get("custom_templates", default={}) or {})
    ctpl_count = len(theme_get("country_templates", default={}) or {})
    atpl_count = len(theme_get("app_templates", default={}) or {})
    otp_style = theme_get("otp_style", default="premium")
    return (
        "<b>⚙ ULTIMATE ADMIN CONTROL PANEL</b>\n\n"
        "<b>📊 Status:</b>\n"
        f"• Theme: <code>{html_safe(theme_get('ui_mode', default='premium'))}</code>\n"
        f"• OTP Style: <code>{html_safe(otp_style)}</code>\n"
        f"• Quote: <code>{'ON' if theme_get('quote_message', default=False) else 'OFF'}</code>\n"
        f"• App Name: <code>{'ON' if theme_get('ui','app_name_show', default=True) else 'OFF'}</code>\n"
        f"• App Short: <code>{'ON' if theme_get('ui','app_name_short_show', default=True) else 'OFF'}</code>\n"
        f"• App Full: <code>{'ON' if theme_get('ui','app_name_full_show', default=True) else 'OFF'}</code>\n"
        f"• App Icon: <code>{'ON' if theme_get('ui','whatsapp_icon_show', default=True) else 'OFF'}</code>\n"
        f"• Chats: <code>{chat_count}</code>  •  Flags: <code>{flag_count}</code>\n"
        f"• Templates: <code>{tpl_count}</code>  •  Country: <code>{ctpl_count}</code>  •  App: <code>{atpl_count}</code>\n"
    )

async def handle_admin_command(session, chat_id, user_id):
    if not is_admin(user_id):
        await tg_send_message(session, chat_id, "Access denied.")
        return
    await tg_send_message(session, chat_id, admin_home_text(), menu_home())

# ============================================================
#  ADMIN TEXT INPUT HANDLER
# ============================================================
async def handle_admin_text_input(session, chat_id, user_id, text):
    global TELEGRAM_CHAT_IDS
    state = admin_state.get(user_id) or {}
    awaiting = state.get("awaiting")
    key = state.get("key", "")
    if not awaiting:
        return False
    value = text.strip()

    if awaiting == "emoji":
        theme_set(["premium_emoji_ids", key], value)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ Emoji updated: <code>{html_safe(key)}</code> = <code>{html_safe(value)}</code>")
        return True

    if awaiting == "appemoji":
        theme_set(["app_icons", key], value)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ App icon updated: <code>{html_safe(key)}</code> = <code>{html_safe(value)}</code>")
        return True

    if awaiting == "flag_add":
        parts = value.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 2 or not parts[0].isalpha():
            await tg_send_message(session, chat_id, "Format: <code>COUNTRY_CODE EMOJI_ID</code>\nExample: <code>US 1234567890</code>")
            return True
        cc = parts[0].upper()
        flags = theme_get("country_flags", default={}) or {}
        flags[cc] = parts[1]
        theme_set(["country_flags"], flags)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ Flag added for {country_code_to_flag(cc)} {cc}")
        return True

    if awaiting == "chatid_add":
        try:
            cid = int(value)
            chat_ids = theme_get("chat_ids", default=[]) or []
            if str(cid) not in chat_ids:
                chat_ids.append(str(cid))
                theme_set(["chat_ids"], chat_ids)
                TELEGRAM_CHAT_IDS.clear()
                TELEGRAM_CHAT_IDS.extend(chat_ids)
                await tg_send_message(session, chat_id, f"✅ Chat ID {cid} added. Total: {len(chat_ids)}")
            else:
                await tg_send_message(session, chat_id, f"⚠️ Already exists")
        except ValueError:
            await tg_send_message(session, chat_id, "❌ Invalid chat ID.")
        admin_state.pop(user_id, None)
        return True

    if awaiting == "style":
        if value.lower() not in {"primary", "secondary", "success", "danger", "default"}:
            await tg_send_message(session, chat_id, "Use: primary|secondary|success|danger|default")
            return True
        theme_set(["style", key], value.lower())
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ {key} = {value.lower()}")
        return True

    field_mapping = {
        "copy_button_name": ["channels", "copy_button_name"],
        "main_channel_name": ["channels", "main_channel_name"],
        "number_channel_name": ["channels", "number_channel_name"],
        "main_channel_url": ["channels", "main_channel_url"],
        "number_channel_url": ["channels", "number_channel_url"],
        "title": ["title"],
        "label_number": ["ui", "label_number"],
        "label_otp": ["ui", "label_otp"],
        "label_time": ["ui", "label_time"],
        "label_country": ["ui", "label_country"],
        "label_service": ["ui", "label_service"],
        "label_language": ["ui", "label_language"],
        "header_text": ["ui", "header_text"],
        "header_emoji": ["ui", "header_emoji"],
        "footer_text": ["ui", "footer_text"],
        "footer_emoji": ["ui", "footer_emoji"],
        "number_mask_custom": ["ui", "number_mask_custom"],
        "time_custom_format": ["ui", "time_custom_format"],
        "separator_custom": ["ui", "separator_custom"],
        "auto_delete_seconds": ["auto_delete_seconds"],
    }
    if awaiting == "field" and key in field_mapping:
        val = value
        if key == "auto_delete_seconds":
            try:
                val = int(value)
            except Exception:
                await tg_send_message(session, chat_id, "❌ Must be a number (seconds). Use 0 to disable.")
                return True
        theme_set(field_mapping[key], val)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ <code>{html_safe(key)}</code> = <code>{html_safe(value)}</code>")
        return True

    if awaiting == "separator_custom_len":
        try:
            n = int(value)
            if n < 1 or n > 60:
                raise ValueError
            theme_set(["ui", "separator_custom_len"], n)
            theme_set(["ui", "separator_length"], "custom")
            admin_state.pop(user_id, None)
            await tg_send_message(session, chat_id, f"✅ Separator length = {n}")
        except Exception:
            await tg_send_message(session, chat_id, "❌ Send number 1-60.")
        return True

    if awaiting == "tpl_add" or awaiting == "tpl_edit":
        parts = value.split(maxsplit=1)
        if len(parts) != 2:
            await tg_send_message(session, chat_id, "Send: <code>name | template text</code>\nExample: <code>my1 | {flag} {otp}</code>")
            return True
        name = parts[0].strip()
        tpl = parts[1].strip()
        templates = theme_get("custom_templates", default={}) or {}
        templates[name] = tpl
        theme_set(["custom_templates"], templates)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ Template <code>{html_safe(name)}</code> saved.")
        return True

    if awaiting == "tpl_setactive":
        templates = theme_get("custom_templates", default={}) or {}
        if value in templates:
            templates["active"] = templates[value]
            templates["default"] = templates[value]
            theme_set(["custom_templates"], templates)
            theme_set(["otp_style"], "custom")
            admin_state.pop(user_id, None)
            await tg_send_message(session, chat_id, f"✅ Active template = <code>{html_safe(value)}</code>. OTP style = custom.")
        else:
            await tg_send_message(session, chat_id, "❌ Template not found.")
        return True

    if awaiting in ("ctpl_add", "ctpl_edit"):
        parts = value.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 2:
            await tg_send_message(session, chat_id, "Send: <code>ISO | template text</code>\nExample: <code>BD | {flag} {otp}</code>")
            return True
        iso = parts[0].upper()
        ct = theme_get("country_templates", default={}) or {}
        ct[iso] = parts[1].strip()
        theme_set(["country_templates"], ct)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ Country template saved for {iso}")
        return True

    if awaiting in ("atpl_add", "atpl_edit"):
        parts = value.split(maxsplit=1)
        if len(parts) != 2:
            await tg_send_message(session, chat_id, "Send: <code>AppName | template text</code>\nExample: <code>WhatsApp | WA: {otp}</code>")
            return True
        app = parts[0].strip()
        at = theme_get("app_templates", default={}) or {}
        at[app] = parts[1].strip()
        theme_set(["app_templates"], at)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ App template saved for {html_safe(app)}")
        return True

    if awaiting in ("alias_add", "alias_edit"):
        parts = value.split(maxsplit=1)
        if len(parts) != 2:
            await tg_send_message(session, chat_id, "Send: <code>AppName | display</code>\nExample: <code>WhatsApp | 🟢 WA</code>")
            return True
        app = parts[0].strip()
        aliases = theme_get("app_aliases", default={}) or {}
        aliases[app] = parts[1].strip()
        theme_set(["app_aliases"], aliases)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ Alias saved for {html_safe(app)}")
        return True

    if awaiting == "btntemplate":
        theme_set(["button", "text_template"], value)
        admin_state.pop(user_id, None)
        await tg_send_message(session, chat_id, f"✅ Button template: <code>{html_safe(value)}</code>")
        return True

    return False

# ============================================================
#  SLASH COMMANDS
# ============================================================
async def handle_admin_slash_command(session, chat_id, user_id, text):
    global TELEGRAM_CHAT_IDS
    if not is_admin(user_id):
        return False
    parts = text.strip().split()
    cmd = parts[0].split("@")[0].lower()
    args = parts[1:]

    if cmd == "/admin":
        await handle_admin_command(session, chat_id, user_id); return True
    if cmd == "/reloadtheme":
        load_theme_config(); await tg_send_message(session, chat_id, "✅ Theme reloaded."); return True
    if cmd == "/resettheme":
        save_theme_config(_deep_merge(DEFAULT_THEME, {})); await tg_send_message(session, chat_id, "✅ Theme reset."); return True
    if cmd == "/settheme" and args and args[0].lower() in {"classic", "premium", "compact"}:
        theme_set(["ui_mode"], args[0].lower()); await tg_send_message(session, chat_id, f"✅ Theme = {args[0].lower()}"); return True
    if cmd == "/setotpstyle" and args and args[0].lower() in OTP_STYLES:
        theme_set(["otp_style"], args[0].lower()); await tg_send_message(session, chat_id, f"✅ OTP style = {args[0].lower()}"); return True
    if cmd == "/setquote" and args and args[0].lower() in {"on", "off"}:
        theme_set(["quote_message"], args[0].lower() == "on"); await tg_send_message(session, chat_id, f"✅ Quote = {args[0].upper()}"); return True
    if cmd == "/preview":
        await tg_send_message(session, chat_id, "<b>👁 Preview</b>\n\n" + render_preview(), build_otp_keyboard("123456", "123-456", "Bangladesh", "WhatsApp"))
        return True
    return False

# ============================================================
#  CALLBACK HANDLER
# ============================================================
async def handle_callback(session, callback):
    global TELEGRAM_CHAT_IDS
    callback_id = str(callback.get("id", ""))
    data = str(callback.get("data", "") or "")
    message = callback.get("message", {}) or {}
    from_user = callback.get("from", {}) or {}
    user_id = int(from_user.get("id", 0) or 0)
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    await tg_answer_callback(session, callback_id)
    if not is_admin(user_id) or chat_id is None or message_id is None:
        return

    nav = {
        "admin:home": (admin_home_text, menu_home),
        "admin:ui": (lambda: "<b>🎛 UI Control</b>", menu_ui),
        "admin:buttons": (lambda: "<b>🔘 Button Control</b>", menu_buttons),
        "admin:emoji": (lambda: "<b>✨ Premium Emoji</b>", menu_emoji),
        "admin:appicons": (lambda: "<b>📱 App Icons</b>", menu_app_icons),
        "admin:themes": (lambda: "<b>🎨 Theme System</b>", menu_themes),
        "admin:separator": (lambda: "<b>🔧 Separator</b>", menu_separator),
        "admin:otpstyle": (lambda: "<b>📝 OTP Style</b>", menu_otpstyle),
        "admin:layout": (lambda: "<b>📐 Layout & Fields</b>", menu_layout),
        "admin:otpdisplay": (lambda: "<b>OTP Display Format</b>", menu_otpdisplay),
        "admin:labels": (lambda: "<b>🏷 Field Labels</b>", menu_labels),
        "admin:headerfooter": (lambda: "<b>📌 Header & Footer</b>", menu_headerfooter),
        "admin:countrymode": (lambda: "<b>🌐 Country Display</b>", menu_countrymode),
        "admin:appmode": (lambda: "<b>📱 App Display</b>", menu_appmode),
        "admin:templates": (lambda: "<b>📋 Custom Templates</b>", menu_templates),
        "admin:ctemplates": (lambda: "<b>🌐 Per-Country Templates</b>", menu_ctemplates),
        "admin:atemplates": (lambda: "<b>📲 Per-App Templates</b>", menu_atemplates),
        "admin:aliases": (lambda: "<b>💠 App Aliases</b>", menu_aliases),
        "admin:numformat": (lambda: "<b>🔢 Number Format</b>", menu_numformat),
        "admin:timeformat": (lambda: "<b>🕒 Time Format</b>", menu_timeformat),
        "admin:flags": (lambda: "<b>🏳️ Country Flags</b>", menu_flags),
        "admin:chatids": (lambda: "<b>👥 Chat IDs</b>", menu_chatids),
        "admin:advanced": (lambda: "<b>⚙️ Advanced</b>", menu_advanced),
    }
    if data in nav:
        txt_fn, kb_fn = nav[data]
        await tg_edit_message(session, chat_id, message_id, txt_fn(), kb_fn())
        return

    if data == "admin:preview":
        preview_text = "<b>👁 LIVE PREVIEW</b>\n\n" + render_preview()
        await tg_edit_message(session, chat_id, message_id, preview_text,
                              {"inline_keyboard": [[{"text": "🔄 Refresh", "callback_data": "admin:preview"}], [{"text": "⬅ Back", "callback_data": "admin:home"}]]})
        return
    if data == "admin:reload":
        load_theme_config(); await tg_edit_message(session, chat_id, message_id, "✅ Reloaded.", menu_home()); return
    if data == "admin:reset":
        save_theme_config(_deep_merge(DEFAULT_THEME, {})); await tg_edit_message(session, chat_id, message_id, "✅ Reset.", menu_home()); return

    if data.startswith("toggle:root:"):
        key = data.split(":", 2)[2]
        new_val = theme_toggle([key])
        await tg_edit_message(session, chat_id, message_id, f"✅ {key} = {'ON' if new_val else 'OFF'}", menu_advanced() if key in {"silent_send", "protect_content", "pin_message"} else menu_ui())
        return
    if data.startswith("toggle:ui:"):
        key = data.split(":", 2)[2]
        new_val = theme_toggle(["ui", key])
        if key in {"otp_bold", "otp_code_block"}:
            await tg_edit_message(session, chat_id, message_id, f"✅ {key} = {'ON' if new_val else 'OFF'}", menu_layout())
        elif key in {"admin_tag_show", "country_show", "flag_show", "whatsapp_icon_show", "app_name_show", "app_name_full_show", "app_name_short_show", "time_show", "language_show", "number_show", "otp_status_show"}:
            await tg_edit_message(session, chat_id, message_id, f"✅ {key} = {'ON' if new_val else 'OFF'}", menu_ui())
        else:
            await tg_edit_message(session, chat_id, message_id, f"✅ {key} = {'ON' if new_val else 'OFF'}", menu_buttons())
        return

    if data.startswith("set:") or data.startswith("setlabel:"):
        key = data.split(":", 1)[1]
        admin_state[user_id] = {"awaiting": "field", "key": key}
        await tg_edit_message(session, chat_id, message_id, f"Send new value for <code>{html_safe(key)}</code>",
                              {"inline_keyboard": [[{"text": "⬅ Cancel", "callback_data": "admin:home"}]]})
        return
    if data == "setsep:custom":
        admin_state[user_id] = {"awaiting": "field", "key": "separator_custom"}
        await tg_edit_message(session, chat_id, message_id, "Send custom separator string.",
                              {"inline_keyboard": [[{"text": "⬅ Cancel", "callback_data": "admin:separator"}]]})
        return
    if data == "setsep:custom_len":
        admin_state[user_id] = {"awaiting": "separator_custom_len"}
        await tg_edit_message(session, chat_id, message_id, "Send custom length (1-60).",
                              {"inline_keyboard": [[{"text": "⬅ Cancel", "callback_data": "admin:separator"}]]})
        return

    if data.startswith("sep:"):
        style = data.split(":", 1)[1].lower()
        if style in {"line", "dash", "dot", "star", "wave", "arrow", "custom"}:
            theme_set(["ui", "separator_style"], style)
            await tg_edit_message(session, chat_id, message_id, f"✅ Separator = {style}", menu_separator())
        return
    if data.startswith("seplen:"):
        length = data.split(":", 1)[1].lower()
        if length in {"short", "medium", "long"}:
            theme_set(["ui", "separator_length"], length)
            await tg_edit_message(session, chat_id, message_id, f"✅ Length = {length}", menu_separator())
        return

    if data.startswith("otpfmt:"):
        fmt = data.split(":", 1)[1].lower()
        theme_set(["ui", "otp_display_format"], fmt)
        await tg_edit_message(session, chat_id, message_id, f"✅ OTP format = {fmt}", menu_otpdisplay())
        return
    if data.startswith("cmode:"):
        mode = data.split(":", 1)[1].lower()
        theme_set(["ui", "country_display"], mode)
        await tg_edit_message(session, chat_id, message_id, f"✅ Country display = {mode}", menu_countrymode())
        return
    if data.startswith("amode:"):
        mode = data.split(":", 1)[1].lower()
        theme_set(["ui", "app_display"], mode)
        await tg_edit_message(session, chat_id, message_id, f"✅ App display = {mode}", menu_appmode())
        return
    if data.startswith("numfmt:"):
        style = data.split(":", 1)[1].lower()
        theme_set(["ui", "number_mask_style"], style)
        await tg_edit_message(session, chat_id, message_id, f"✅ Number format = {style}", menu_numformat())
        return
    if data.startswith("timefmt:"):
        fmt = data.split(":", 1)[1].lower()
        theme_set(["ui", "time_format"], fmt)
        await tg_edit_message(session, chat_id, message_id, f"✅ Time format = {fmt}", menu_timeformat())
        return

    if data.startswith("emoji:"):
        key = data.split(":", 1)[1]
        admin_state[user_id] = {"awaiting": "emoji", "key": key}
        await tg_edit_message(session, chat_id, message_id, f"Send emoji ID for <code>{html_safe(key)}</code>",
                              {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:emoji"}]]})
        return
    if data.startswith("appemoji:"):
        key = data.split(":", 1)[1]
        admin_state[user_id] = {"awaiting": "appemoji", "key": key}
        await tg_edit_message(session, chat_id, message_id, f"Send emoji ID for app <code>{html_safe(key)}</code>",
                              {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:appicons"}]]})
        return

    if data == "admin:btntemplate":
        admin_state[user_id] = {"awaiting": "btntemplate"}
        await tg_edit_message(session, chat_id, message_id,
            "Send button text template.\n\nPlaceholders: <code>{name}</code> <code>{otp}</code> <code>{otp_split}</code> <code>{country}</code> <code>{app}</code>\nExample: <code>{name} • {otp}</code>",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:buttons"}]]})
        return

    if data == "tpl:add":
        admin_state[user_id] = {"awaiting": "tpl_add"}
        await tg_edit_message(session, chat_id, message_id,
            "Send: <code>name | template text</code>\n\nVariables: {flag} {country} {iso} {app} {app_short} {app_icon} {otp} {otp_raw} {otp_split} {number} {time} {language} {sep} {newline} {otp_icon} {time_icon} {number_icon} {lang_icon}",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:templates"}]]})
        return
    if data == "tpl:setactive":
        admin_state[user_id] = {"awaiting": "tpl_setactive"}
        await tg_edit_message(session, chat_id, message_id,
            "Send template name to activate.", {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:templates"}]]})
        return
    if data == "tpl:help":
        await tg_edit_message(session, chat_id, message_id,
            "<b>📖 Template Variables</b>\n\n"
            "<code>{flag}</code> Country flag\n"
            "<code>{country}</code> Country name\n"
            "<code>{iso}</code> ISO code\n"
            "<code>{app}</code> Full app name\n"
            "<code>{app_short}</code> Short app name\n"
            "<code>{app_icon}</code> App icon emoji\n"
            "<code>{otp}</code> Formatted OTP\n"
            "<code>{otp_raw}</code> Raw digits\n"
            "<code>{otp_split}</code> 123-456\n"
            "<code>{number}</code> Masked number\n"
            "<code>{time}</code> Time\n"
            "<code>{language}</code> Language\n"
            "<code>{sep}</code> Separator\n"
            "<code>{newline}</code> Line break\n"
            "<code>{otp_icon}</code> <code>{time_icon}</code> <code>{number_icon}</code> <code>{lang_icon}</code>\n"
            "<code>{header_emoji}</code> <code>{footer_emoji}</code>\n",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:templates"}]]})
        return
    if data.startswith("tpl:edit:") or data.startswith("tpl:del:"):
        action, name = data.split(":", 2)[1], data.split(":", 2)[2]
        if action == "del":
            templates = theme_get("custom_templates", default={}) or {}
            templates.pop(name, None)
            theme_set(["custom_templates"], templates)
            await tg_edit_message(session, chat_id, message_id, f"✅ Deleted {html_safe(name)}", menu_templates())
        else:
            admin_state[user_id] = {"awaiting": "tpl_edit"}
            await tg_edit_message(session, chat_id, message_id,
                f"Send new text for <code>{html_safe(name)}</code> as:\n<code>{html_safe(name)} | new template</code>",
                {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:templates"}]]})
        return

    if data == "ctpl:add":
        admin_state[user_id] = {"awaiting": "ctpl_add"}
        await tg_edit_message(session, chat_id, message_id,
            "Send: <code>ISO | template</code>\nExample: <code>BD | 🇧🇩 {otp}</code>",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:ctemplates"}]]})
        return
    if data.startswith("ctpl:edit:") or data.startswith("ctpl:del:"):
        action, iso = data.split(":", 2)[1], data.split(":", 2)[2]
        if action == "del":
            ct = theme_get("country_templates", default={}) or {}
            ct.pop(iso, None)
            theme_set(["country_templates"], ct)
            await tg_edit_message(session, chat_id, message_id, f"✅ Deleted {iso}", menu_ctemplates())
        else:
            admin_state[user_id] = {"awaiting": "ctpl_edit"}
            await tg_edit_message(session, chat_id, message_id,
                f"Send: <code>{iso} | new template</code>",
                {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:ctemplates"}]]})
        return

    if data == "atpl:add":
        admin_state[user_id] = {"awaiting": "atpl_add"}
        await tg_edit_message(session, chat_id, message_id,
            "Send: <code>AppName | template</code>\nExample: <code>WhatsApp | WA {otp}</code>",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:atemplates"}]]})
        return
    if data.startswith("atpl:edit:") or data.startswith("atpl:del:"):
        action, app = data.split(":", 2)[1], data.split(":", 2)[2]
        if action == "del":
            at = theme_get("app_templates", default={}) or {}
            at.pop(app, None)
            theme_set(["app_templates"], at)
            await tg_edit_message(session, chat_id, message_id, f"✅ Deleted {html_safe(app)}", menu_atemplates())
        else:
            admin_state[user_id] = {"awaiting": "atpl_edit"}
            await tg_edit_message(session, chat_id, message_id,
                f"Send: <code>{html_safe(app)} | new template</code>",
                {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:atemplates"}]]})
        return

    if data == "alias:add":
        admin_state[user_id] = {"awaiting": "alias_add"}
        await tg_edit_message(session, chat_id, message_id,
            "Send: <code>AppName | display text</code>\nExample: <code>WhatsApp | 🟢 WA</code>",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:aliases"}]]})
        return
    if data.startswith("alias:edit:") or data.startswith("alias:del:"):
        action, app = data.split(":", 2)[1], data.split(":", 2)[2]
        if action == "del":
            al = theme_get("app_aliases", default={}) or {}
            al.pop(app, None)
            theme_set(["app_aliases"], al)
            await tg_edit_message(session, chat_id, message_id, f"✅ Deleted alias for {html_safe(app)}", menu_aliases())
        else:
            admin_state[user_id] = {"awaiting": "alias_edit"}
            await tg_edit_message(session, chat_id, message_id,
                f"Send: <code>{html_safe(app)} | new display</code>",
                {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:aliases"}]]})
        return

    if data == "flag:add":
        admin_state[user_id] = {"awaiting": "flag_add"}
        await tg_edit_message(session, chat_id, message_id,
            "Send: <code>CC EMOJI_ID</code>\nExample: <code>US 1234567890</code>",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:flags"}]]})
        return
    if data == "flag:list":
        flags = theme_get("country_flags", default={}) or {}
        if flags:
            msg = "<b>Custom Flags:</b>\n" + "".join(f"{country_code_to_flag(c)} {c}: <code>{e}</code>\n" for c, e in flags.items())
        else:
            msg = "No custom flags."
        await tg_edit_message(session, chat_id, message_id, msg, menu_flags())
        return
    if data == "flag:clear":
        theme_set(["country_flags"], {})
        await tg_edit_message(session, chat_id, message_id, "✅ All cleared.", menu_flags())
        return
    if data.startswith("flag:") and not data.startswith("flag:add") and not data.startswith("flag:list") and not data.startswith("flag:clear"):
        cc = data.split(":", 1)[1]
        if len(cc) == 2:
            admin_state[user_id] = {"awaiting": "flag_add"}
            await tg_edit_message(session, chat_id, message_id,
                f"Send new emoji ID for {country_code_to_flag(cc)} {cc}",
                {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:flags"}]]})
        return

    if data == "chatid:add":
        admin_state[user_id] = {"awaiting": "chatid_add"}
        await tg_edit_message(session, chat_id, message_id,
            "Send chat ID (positive or negative):\nExample: <code>-1001234567890</code>",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:chatids"}]]})
        return
    if data == "chatid:list":
        chat_ids = theme_get("chat_ids", default=[]) or []
        msg = "<b>Chat IDs:</b>\n" + "".join(f"{i}. <code>{c}</code>\n" for i, c in enumerate(chat_ids, 1)) if chat_ids else "None."
        await tg_edit_message(session, chat_id, message_id, msg + f"\n<b>Total: {len(chat_ids)}</b>", menu_chatids())
        return
    if data.startswith("chatid:remove:"):
        try:
            idx = int(data.split(":", 2)[2])
            chat_ids = theme_get("chat_ids", default=[]) or []
            if 0 <= idx < len(chat_ids):
                removed = chat_ids.pop(idx)
                theme_set(["chat_ids"], chat_ids)
                TELEGRAM_CHAT_IDS.clear()
                TELEGRAM_CHAT_IDS.extend(chat_ids)
                await tg_edit_message(session, chat_id, message_id, f"✅ Removed <code>{removed}</code>", menu_chatids())
            else:
                await tg_edit_message(session, chat_id, message_id, "❌ Invalid.", menu_chatids())
        except Exception:
            await tg_edit_message(session, chat_id, message_id, "❌ Error.", menu_chatids())
        return

    if data.startswith("style:"):
        key = data.split(":", 1)[1]
        admin_state[user_id] = {"awaiting": "style", "key": key}
        await tg_edit_message(session, chat_id, message_id,
            f"Send style for <code>{html_safe(key)}</code>\nAllowed: primary|secondary|success|danger|default",
            {"inline_keyboard": [[{"text": "⬅ Back", "callback_data": "admin:themes"}]]})
        return
    if data.startswith("theme:"):
        mode = data.split(":", 1)[1].lower()
        if mode == "reset_default":
            save_theme_config(_deep_merge(DEFAULT_THEME, {}))
            await tg_edit_message(session, chat_id, message_id, "✅ Reset.", menu_themes())
            return
        if mode in {"classic", "premium", "compact"}:
            theme_set(["ui_mode"], mode)
            await tg_edit_message(session, chat_id, message_id, f"✅ Theme = {mode}", menu_themes())
            return
    if data.startswith("otpstyle:"):
        style = data.split(":", 1)[1].lower()
        if style in OTP_STYLES:
            theme_set(["otp_style"], style)
            await tg_edit_message(session, chat_id, message_id, f"✅ OTP style = {style}", menu_otpstyle())
            return

# ============================================================
#  UPDATES LOOP
# ============================================================
async def process_telegram_updates(session):
    global telegram_update_offset
    updates = await tg_get_updates(session, telegram_update_offset)
    for u in updates:
        try:
            telegram_update_offset = max(telegram_update_offset, int(u.get("update_id",0)) + 1)
            if "callback_query" in u:
                await handle_callback(session, u["callback_query"]); continue
            m = u.get("message") or {}
            text = str(m.get("text","") or "")
            cid = m.get("chat",{}).get("id")
            uid = int((m.get("from",{}) or {}).get("id",0) or 0)
            if not cid or not text: continue
            if await handle_admin_text_input(session, cid, uid, text): continue
            await handle_admin_slash_command(session, cid, uid, text)
        except Exception:
            logger.exception("update processing")

async def admin_poll_loop(session):
    logger.info("Admin control: %s", ", ".join(str(x) for x in sorted(ADMIN_IDS)))
    while True:
        await process_telegram_updates(session)
        await asyncio.sleep(TELEGRAM_UPDATES_INTERVAL)

# ============================================================
#  MAIN RUN
# ============================================================
async def main():
    logger.info("="*60)
    logger.info("🚀 TempNumbers.net OTP Bot — WEBHOOK EDITION")
    logger.info("Webhook URL: http://jembut.jhonaleystore.id:%s%s", WEBHOOK_PORT, WEBHOOK_PATH)
    logger.info("Chats: %d", len(TELEGRAM_CHAT_IDS))
    logger.info("="*60)

    conn = aiohttp.TCPConnector(ssl=False, force_close=True, limit=30)
    timeout = aiohttp.ClientTimeout(total=25)
    async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
        await asyncio.gather(
            run_webhook_server(session),
            admin_poll_loop(session),
            auto_delete_worker(session),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception:
        logger.exception("Fatal")