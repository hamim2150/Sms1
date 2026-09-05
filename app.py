import requests
import time
import json
import random
import sqlite3
import os
import re
import html
import threading
import firebase_admin
from firebase_admin import credentials, firestore
# ---- RENDER ER PORT FIX KORAR JONNO NOTUN CODE ----
from flask import Flask
import threading
import os

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running perfectly!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# Web server take background e chalu kora holo
threading.Thread(target=run_web, daemon=True).start()
# ---------------------------------------------------

# ==========================================
# Configuration
# ==========================================
BOT_TOKEN = "8919458173:AAFxKL0sE5xhVdQxRCf2aCLHwsHlOPICdTo"
ADMIN_ID = 8360805978
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
BOT_USERNAME = ""

# 2oo9 API Configuration
API_2OO9_BASE = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
API_2OO9_KEY_DEFAULT = "MHF5UTYD3L7"

# Global states
current_db_mode = "sqlite"
db_firebase = None 
waiting_for_firebase = False
user_states = {}

# User & Cooldown States
user_cache = {} 
user_active_sessions = {} # format: {"number": user_id}
user_cooldowns = {} 

# Voltx Auto System States
voltx_auto_mode = True 
voltx_keys = [API_2OO9_KEY_DEFAULT]
force_join_status = False
force_join_channels = []

# OTP Forwarding States
otp_forward_groups = []
otp_button_link = "https://t.me/your_default_bot"
recent_success_otps = set()

voltx_dynamic_data = {} 
recent_traffic = []
daily_stats = {"date": "", "numbers": 0, "otps": 0} # 🌟 Daily Stats Tracker
daily_user_otps = {"date": "", "users": {}}

# 🌟 Caching Variables for Rocket Speed!
cached_services_kb = None
cached_countries_kb = {}
cached_leaderboard_text = ""

def auto_cache_menu_thread():
    global cached_services_kb, cached_countries_kb, voltx_auto_mode, voltx_dynamic_data
    while True:
        try:
            if voltx_auto_mode and voltx_dynamic_data:
                service_hits = [(sid, s_data, sum(r["hits"] for r in s_data["ranges"].values())) for sid, s_data in voltx_dynamic_data.items()]
                top_services = sorted(service_hits, key=lambda x: x[2], reverse=True)[:15] # 🌟 Top 15 Services
                
                new_srv_kb = {"inline_keyboard": []}
                row = []; styles = ["primary", "success", "danger"]; style_idx = 0
                for sid, data, hits in top_services:
                    safe_sid = html.escape(str(sid))
                    
                    # 🌟 BUG FIX: Emoji injected into standard text parameter
                    emoji_icon = data.get("normal_emoji", "📱")
                    btn_text = f"{emoji_icon} {safe_sid}".strip()
                    
                    row.append({"text": btn_text, "callback_data": f"srv_{safe_sid[:15]}", "style": styles[style_idx % 3], "icon_custom_emoji_id": data.get("emoji_id", "")})
                    style_idx += 1
                    if len(row) == 2: new_srv_kb["inline_keyboard"].append(row); row = []
                if row: new_srv_kb["inline_keyboard"].append(row)
                new_srv_kb["inline_keyboard"].append([{"text": "CLOSE", "callback_data": "close_panel", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}])
                
                cached_services_kb = new_srv_kb

                new_cnt_kb = {}
                for sid, data, hits in top_services:
                    safe_sid_short = html.escape(str(sid))[:15]
                    country_map = {}
                    for r, r_data in data["ranges"].items():
                        clean_r = str(r).replace("X", "")
                        if not re.match(r'^\d+$', clean_r): continue
                        c_code, c_name = get_country_info(clean_r)
                        if c_code not in country_map: country_map[c_code] = {"name": c_name, "hits": 0}
                        country_map[c_code]["hits"] += r_data["hits"]
                    
                    top_countries = sorted(country_map.items(), key=lambda x: x[1]["hits"], reverse=True)[:15] # 🌟 Top 15 Countries
                    
                    cnt_kb = {"inline_keyboard": []}
                    styles_c = ["primary", "success", "danger"]; style_idx_c = 0
                    std_service = detect_service("", sid)
                    rate = get_otp_reward(std_service)
                    
                    for c_code, c_data in top_countries:
                        c_name_full = c_data["name"]
                        parts = c_name_full.split(" ", 1)
                        emoji_char = parts[0]
                        clean_name = parts[1] if len(parts) > 1 else c_name_full
                        
                        # 🌟 BUG FIX: Flag Emoji is now prepended properly
                        btn_text = f"{emoji_char} Other (+{c_code}) - {rate} TK" if "Other" in clean_name else f"{emoji_char} {clean_name} (+{c_code}) - {rate} TK"
                        btn = {"text": btn_text, "callback_data": f"cc_{safe_sid_short}_{c_code}", "style": styles_c[style_idx_c % 3]}
                        if emoji_char in GLOBAL_BODY_EMOJIS: btn["icon_custom_emoji_id"] = GLOBAL_BODY_EMOJIS[emoji_char]
                            
                        cnt_kb["inline_keyboard"].append([btn])
                        style_idx_c += 1
                        
                    cnt_kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "back_to_services", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}])
                    new_cnt_kb[safe_sid_short] = cnt_kb
                    
                cached_countries_kb = new_cnt_kb
                
            # --- 🌟 Leaderboard Caching ---
            global cached_leaderboard_text, daily_user_otps
            today = time.strftime("%Y-%m-%d")
            if daily_user_otps.get("date") != today:
                daily_user_otps["date"] = today
                daily_user_otps["users"] = {}
                
            top_users = sorted(daily_user_otps["users"].items(), key=lambda x: x[1], reverse=True)[:5]
            lb_msg = "<blockquote><tg-emoji emoji-id=\"5240021484516185513\">🏆</tg-emoji> <b>𝗧𝗢𝗣 𝟱 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗 (TODAY)</b></blockquote>\n━━━━━━━━━━━━━━━━━\n"
            emoji_map = [("1️⃣", "5238176680098440792"), ("2️⃣", "5237806896299157399"), ("3️⃣", "5239965456667812809"), ("4️⃣", "5237911487342751418"), ("5️⃣", "5240278297790686165")]
            
            if not top_users: 
                lb_msg += "<i>No OTPs received today.</i>\n"
            else:
                for idx, (uid_str, otp_count) in enumerate(top_users):
                    u_data = get_user(int(uid_str))
                    fname = u_data["first_name"] if u_data else "User"
                    emoji_char, emoji_id = emoji_map[idx]
                    lb_msg += f"<blockquote><tg-emoji emoji-id=\"{emoji_id}\">{emoji_char}</tg-emoji> <a href='tg://user?id={uid_str}'>{html.escape(str(fname))}</a> - {otp_count} OTP</blockquote>\n"
            lb_msg += "━━━━━━━━━━━━━━━━━"
            cached_leaderboard_text = lb_msg
            
        except Exception as e:
            pass
        time.sleep(5) # 🌟 5 সেকেন্ড পরপর ব্যাকগ্রাউন্ডে ক্যাশ রেডি হবে

# Admin Settings (DXA Control)
bot_settings = {
    "withdraw_on": True,
    "min_withdraw": 10.0,
    "support_link": "",
    "w_group": "",
    "auto_br_on": False,
    "auto_br_interval": 60,
    "cooldown": 5, # Default 5 seconds
    "num_req": 1, # Default 1 number per request
    "w_methods": ["bKash", "Nagad"],
    "otp_default_rate": 0.5,
    "otp_service_rates": {},
    "main_channel_link": ""
}

BOT_DATA_FILE = "bot_data.json"
USERS_LIST_FILE = "users_list.json"

# ==========================================
# Helper: Get Active Voltx Key & Rates
# ==========================================
def get_api_key():
    return random.choice(voltx_keys) if voltx_keys else API_2OO9_KEY_DEFAULT

def get_otp_reward(service_name):
    rates = bot_settings.get("otp_service_rates", {})
    val = rates.get(service_name, bot_settings.get("otp_default_rate", 0.5))
    return float(val)

def update_daily_stat(key, amount=1):
    global daily_stats
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date") != today:
        daily_stats = {"date": today, "numbers": 0, "otps": 0}
    daily_stats[key] = daily_stats.get(key, 0) + amount

# ==========================================
# Local Storage Managers
# ==========================================
def load_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels, voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings, user_active_sessions, daily_stats, daily_user_otps
    if os.path.exists(BOT_DATA_FILE):
        try:
            with open(BOT_DATA_FILE, "r") as f:
                data = json.load(f)
                recent_traffic = data.get("recent_traffic", [])
                voltx_dynamic_data = data.get("voltx_dynamic_data", {})
                loaded_keys = data.get("voltx_keys", [])
                
                if not loaded_keys:
                    voltx_keys = [API_2OO9_KEY_DEFAULT]
                else:
                    voltx_keys = loaded_keys
                    
                force_join_status = data.get("force_join_status", False)
                force_join_channels = data.get("force_join_channels", [])
                voltx_auto_mode = data.get("voltx_auto_mode", True)
                otp_forward_groups = data.get("otp_forward_groups", [])
                otp_button_link = data.get("otp_button_link", "https://t.me/your_default_bot")
                recent_success_otps = set(data.get("recent_success_otps", []))
                
                loaded_settings = data.get("bot_settings", {})
                for k, v in loaded_settings.items(): bot_settings[k] = v
                
                daily_stats = data.get("daily_stats", {"date": "", "numbers": 0, "otps": 0})
                daily_user_otps = data.get("daily_user_otps", {"date": "", "users": {}})
                user_active_sessions = data.get("user_active_sessions", {})
        except Exception as e:
            print(f"Error loading local data: {e}")

def save_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels, voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings, user_active_sessions, daily_stats
    try:
        with open(BOT_DATA_FILE, "w") as f:
            json.dump({
                "recent_traffic": recent_traffic, 
                "voltx_dynamic_data": voltx_dynamic_data,
                "voltx_keys": voltx_keys,
                "force_join_status": force_join_status,
                "force_join_channels": force_join_channels,
                "voltx_auto_mode": voltx_auto_mode,
                "otp_forward_groups": otp_forward_groups,
                "otp_button_link": otp_button_link,
                "recent_success_otps": list(recent_success_otps),
                "bot_settings": bot_settings,
                "user_active_sessions": user_active_sessions,
                "daily_stats": daily_stats,
                "daily_user_otps": daily_user_otps
            }, f)
    except Exception as e:
        print(f"Error saving local data: {e}")
        
    # 🌟 Firebase এ লাইভ আপডেট পাঠানো
    if current_db_mode == "firebase" and db_firebase:
        try:
            db_firebase.collection('settings').document('bot_config').set({
                "bot_settings": bot_settings,
                "force_join_status": force_join_status,
                "force_join_channels": force_join_channels,
                "otp_forward_groups": otp_forward_groups,
                "otp_button_link": otp_button_link,
                "voltx_keys": voltx_keys,
                "voltx_auto_mode": voltx_auto_mode
            }, merge=True)
        except: pass

# গ্লোবাল ভেরিয়েবলে ইউজার লিস্ট ক্যাশ করে রাখা হলো
cached_user_list = set()

def add_to_broadcast_list(user_id):
    global cached_user_list
    if not cached_user_list and os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                cached_user_list = set(json.load(f))
        except: pass
        
    if user_id not in cached_user_list:
        cached_user_list.add(user_id)
        try:
            with open(USERS_LIST_FILE, "w") as f:
                json.dump(list(cached_user_list), f)
        except: pass

def get_all_user_ids():
    global user_cache
    users = set()
    
    # 🌟 ১. প্রথমে RAM Cache থেকে দ্রুত ইউজার নিবে
    for uid in user_cache.keys():
        users.add(int(uid))
        
    # 🌟 ২. এরপর লোকাল JSON ফাইল থেকে নিবে
    if os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                for u in json.load(f): users.add(int(u))
        except: pass
        
    #RAM সবসময় আপডেটেড থাকে!
    return list(users)

# ==========================================
# Telegram APIs & Force Join Helpers
# ==========================================
def get_bot_info():
    try:
        res = requests.get(BASE_URL + "getMe").json()
        if res.get("ok"): return res["result"]["username"]
    except Exception: pass
    return ""

def set_bot_commands():
    commands = [{"command": "start", "description": "Start the bot or refresh menu"}]
    try: requests.post(BASE_URL + "setMyCommands", json={"commands": commands})
    except Exception: pass

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": apply_emojis(text), "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: return requests.post(BASE_URL + "sendMessage", json=payload).json()
    except Exception: return None

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": apply_emojis(text), "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: requests.post(BASE_URL + "editMessageText", json=payload)
    except Exception: pass

def answer_callback_query(callback_query_id, text="", show_alert=False):
    payload = {"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert}
    requests.post(BASE_URL + "answerCallbackQuery", json=payload)

def delete_message(chat_id, message_id):
    payload = {"chat_id": chat_id, "message_id": message_id}
    requests.post(BASE_URL + "deleteMessage", json=payload)

def copy_message(chat_id, from_chat_id, message_id, reply_markup=None):
    payload = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: return requests.post(BASE_URL + "copyMessage", json=payload).json()
    except Exception: return None

def get_chat_details(chat_identifier):
    chat_identifier = str(chat_identifier).strip()
    if chat_identifier.startswith("https://t.me/"):
        chat_identifier = "@" + chat_identifier.split("/")[-1]
    elif not chat_identifier.startswith("@") and not chat_identifier.startswith("-100"):
        chat_identifier = "@" + chat_identifier
        
    url = BASE_URL + "getChat"
    res = requests.get(url, params={"chat_id": chat_identifier}).json()
    if res.get("ok"):
        chat = res["result"]
        chat_data = {
            "id": chat["id"],
            "username": "@" + chat["username"] if "username" in chat else "",
            "title": chat.get("title", "Private Channel"),
            "invite_link": chat.get("invite_link", "")
        }
        if not chat_data["invite_link"]:
            inv_res = requests.post(BASE_URL + "exportChatInviteLink", json={"chat_id": chat["id"]}).json()
            if inv_res.get("ok"):
                chat_data["invite_link"] = inv_res["result"]
        return chat_data
    return None

def is_user_joined(user_id):
    if not force_join_status or not force_join_channels: return True
    if user_id == ADMIN_ID: return True
    
    for ch in force_join_channels:
        try:
            res = requests.get(BASE_URL + "getChatMember", params={"chat_id": ch["id"], "user_id": user_id}).json()
            if res.get("ok"):
                status = res["result"]["status"]
                if status in ["left", "kicked"]: return False
            else:
                return False
        except: return False
    return True

# ==========================================
# Global Emojis Map
# ==========================================
GLOBAL_BODY_EMOJIS = {
    "➖": "5870818207383686839", "🚫": "5334807341109908955", "😒": "5334763399299506604",
    "🖥": "5334880948259427772", "🌐": "5334590977837403844", "🌟": "5337102391244263212",
    "🕓": "5336983442125001376", "⌛": "5337172996211648018", "💬": "5337302974806922068",
    "🔐": "5337255927735163754", "🍏": "5337132498965010628", "❔": "5336850036145823599",
    "⚠️": "5336944168944047463", "🔥": "5337267511261960341", "💸": "5429612421977253466",
    "🥚": "5348390922507817684", "👨‍⚖": "5334763399299506604", "🐁": "5348494358205207761",
    "🧻": "5348486915026884464", "⚗": "5346311574221000149", "🛴": "5348075478634766440",
    "📊": "5353032893096567467", "🔢": "5226929552319594190", "👤": "5352861489541714456",
    "📁": "5352721946054268944", "🚀": "5352597830089347330", "💎": "5352838545826420397",
    "📍": "5352922460897452503", "👋": "5353027129250453493", "✅": "5352694861990501856",
    "1️⃣": "5352651766288652742", "2️⃣": "5355186458418257716", "3️⃣": "5352867219028091093",
    "4️⃣": "5352566657216714037", "5️⃣": "5353086880835474989", "6️⃣": "5354859211975071385",
    "7️⃣": "5352859127309707652", "8️⃣": "5352957533600389988", "9️⃣": "5353060913463204207",
    "🔤": "5352727417842606016", "📣": "5352980533150259581", "📤": "5353001161878182134",
    "✨": "5352552689983067014", "🔹": "5352638632278660622", "🎙": "5355102594886833928",
    "💴": "5352985330628730418", "📅": "5352585194295564660", "📴": "5352974971167611327",
    "✏️": "5395444784611480792", "📱": "5337132498965010628", "🔗": "5420517437885943844",
    "❌": "5420130255174145507", "⚙️": "5420155432272438703", "🫂": "5420145051336485498",
    "➕": "5420323438508155202", "🗑": "5422557736330106570", "🎁": "5420396762189831222",
    "➤": "5420618897898381296", "🏢": "5420156334215565595", "💳": "5190899075968441286",
    "📝": "5192739271886282680", "🛡": "5190447043545438788", "🤝": "5192805934073685937",
    "💰": "5190576863226933563", "👀": "5190645917711114179", "🕹": "5193100774988617665",
    "🟢": "5192812028632274956", "🧪": "5190781475468915802", "🎨": "5190751148704833975",
    "📂": "5257969839313526622", "🌍": "5780471598922337683", "📌": "5318986077455795572",
    "📢": "5789428375261023681", "🆔": "5226929552319594190", "📈": "5352877703043258544",
    "🔔": "5352980533150259581", "🏦": "5429612421977253466", "🧾": "5192739271886282680",
    "👨‍⚖️": "5334763399299506604", "🔍": "5463352748751753567", "🔑": "5197288647275071607",
    "🏆": "5240021484516185513", "🚦": "5429571662737611814", "👥": "5420145051336485498", 
    "🎯": "5352922460897452503", "📶": "5429353834881261942", "⏳": "5337172996211648018", 
    "🔸": "5429576112323732785", "🎉": "5420396762189831222", "💵": "5429612421977253466", 
    "👑": "5352838545826420397", "↳": "5420618897898381296",
    "🇺🇸": "5913463998522592692", "🇺🇦": "5911406692007941050", "🇵🇱": "5913550391789752571",
    "🇰🇿": "5913724621433082323", "🇨🇳": "5913779335021466780", "🇦🇿": "5911197578640233518",
    "🇪🇺": "5911106310585193018", "🇦🇲": "5913272455866093666", "🇷🇺": "5913274246867456342",
    "🇺🇿": "5911051846104912282", "🇩🇪": "5911096835887337583", "🇯🇵": "5913293711659241040",
    "🇹🇷": "5910995113881901195", "🇧🇾": "5911011185649521599", "🇬🇧": "5913443365499703513",
    "🇮🇳": "5913754823643107921", "🇧🇷": "5911148568768418614", "🇿🇲": "5913564754160389778",
    "🇾🇪": "5913346492512341993", "🏴󠁧󠁢󠁷󠁬󠁳󠁿": "5911297801702084799", "🇻🇳": "5913428887164949581",
    "🇻🇦": "5911211932420938860", "🇻🇺": "5913511535220625585", "🇺🇾": "5913623088406204470",
    "🇦🇪": "5913726554168365343", "🇺🇬": "5913488939397681980", "🇹🇲": "5913315521503170180",
    "🇹🇳": "5911332947419468671", "🇹🇹": "5911228635548750294", "🇹🇬": "5913423260757790970",
    "🇹🇭": "5913617968805187987", "🇹🇿": "5911418949844603556", "🇹🇯": "5911287639809463107",
    "🇨🇭": "5913271227505448072", "🇸🇪": "5911156510162949403", "🇸🇿": "5913374525763883286",
    "🇸🇷": "5913275539652611719", "🇸🇩": "5911387497799094470", "🇪🇸": "5911193287967904547",
    "🇱🇰": "5911293163137406640", "🇸🇸": "5911406262511211744", "🇿🇦": "5911203119148044594",
    "🇸🇴": "5911397852965244436", "🇸🇧": "5911482712929080608", "🇸🇮": "5913431983836368644",
    "🇸🇰": "5913751666842145020", "🇸🇬": "5911531460808051849", "🇸🇱": "5911210450657218661",
    "🇸🇨": "5911185183364616913", "🇷🇸": "5913592598433369871", "🇸🇳": "5910995302860461643",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿": "5911460091336331851", "🇸🇹": "5913574331937462345", "🇸🇲": "5913587968458625465",
    "🇼🇸": "5913325971158602854", "🇰🇳": "5913691898077253637", "🇻🇨": "5911318941531116255",
    "🇱🇨": "5911243659344351824", "🇵🇸": "5913684768431541668", "🇷🇼": "5911455229433352234",
    "🇷🇴": "5913460373570195273", "🇶🇦": "5911260864983339619", "🇵🇷": "5911504350974317480",
    "🇵🇹": "5911023653939581472", "🇵🇭": "5911268638874145162", "🇵🇪": "5911207993935925780",
    "🇵🇾": "5911014265141072316", "🇵🇬": "5911107251183030903", "🇵🇦": "5913428968769327174",
    "🇵🇼": "5911283903187915549", "🇵🇰": "5913705895375672082", "🇴🇲": "5913570801474343473",
    "🇳🇴": "5913617397574537046", "🇳🇬": "5911143844304393105", "🇳🇪": "5911270086278124251",
    "🇳🇿": "5913640044937089340", "🇳🇱": "5913367645226275100", "🇳🇵": "5913496520014958723",
    "🇳🇦": "5911108535378252443", "🇲🇿": "5911333419865871464", "🇲🇦": "5911482111633658301",
    "🇲🇪": "5913239436157522151", "🇲🇳": "5911041383564580038", "🇲🇨": "5911245347266500057",
    "🇲🇩": "5913456847402045950", "🇲🇻": "5913501399097806832", "🇲🇱": "5911305266355245916",
    "🇲🇹": "5911023714069123567", "🇧🇲": "5913680005312811090", "🇲🇶": "5911378005921370347",
    "🇲🇭": "5913235935759175692", "🇲🇺": "5913291113204027321", "🇲🇽": "5913687302462246518",
    "🇫🇲": "5911271104185373336", "🇲🇾": "5913654360063087453", "🇰🇪": "5911154710571651231",
    "🇲🇬": "5913766918271012920", "🇲🇰": "5913394029210374721", "🇱🇺": "5913390842344640293",
    "🇱🇹": "5911172315642597775", "🇱🇮": "5911166650580734660", "🇱🇾": "5911236989260140996",
    "🇱🇷": "5913324167272337727", "🇰🇮": "5911294443037660118", "🇽🇰": "5911433681582429010",
    "🇰🇼": "5913290705182134003", "🇰🇬": "5911202161370337549", "🇱🇦": "5913718526874489279",
    "🇱🇻": "5913738489882480243", "🇱🇧": "5911504273664905447", "🇱🇸": "5911059881988723711",
    "🇮🇩": "5913479361620611038", "🇮🇷": "5911308891307643032", "🇮🇶": "5911382442622587735",
    "🇮🇪": "5913440715504881532", "🇮🇱": "5911471936856134692", "🇮🇹": "5913688444923547525",
    "🇯🇲": "5913232280742006526", "🇯🇴": "5913234136167878475", "🇮🇸": "5911047899029967246",
    "🇭🇺": "5913767635530551104", "🇭🇳": "5911406889576436289", "🇭🇹": "5913459789454643194",
    "🇬🇾": "5913579412883771480", "🇬🇼": "5911398694778836149", "🇬🇳": "5913471858312744319",
    "🇬🇹": "5913324858762072330", "🇬🇩": "5913228063084121946", "🇬🇷": "5911210399117611448",
    "🇬🇭": "5913391155877252952", "🇬🇪": "5913434771270144023", "🇬🇲": "5913657267755945883",
    "🇬🇦": "5911037896051137264", "🇫🇷": "5913605586414473124", "🇫🇮": "5911041344909873378",
    "🇫🇯": "5911393832875856716", "🇪🇹": "5911078333168227043", "🇩🇴": "5911152099231536123",
    "🇹🇱": "5911141915864076479", "🇪🇨": "5911273865849347408", "🇪🇬": "5913694831539916769",
    "🇸🇻": "5913238624408703010", "🏴󠁧󠁢󠁥󠁮󠁧󠁿": "5913475719488344315", "🇪🇪": "5910986042910969906",
    "🇩🇲": "5911377121158107430", "🇩🇯": "5911407709915190157", "🇩🇰": "5911206009661034712",
    "🇨🇾": "5911023550860366409", "🇭🇷": "5913692684056269311", "🇨🇷": "5911261745451635030",
    "🇨🇬": "5911338788574990168", "🇨🇩": "5913770362834783827", "🇰🇲": "5911338582416560604",
    "🇰🇭": "5913699998385573485", "🇨🇲": "5911172109484167745", "🇨🇦": "5913623736946265914",
    "🇨🇻": "5913571501554012193", "🇨🇫": "5913443245240619222", "🇹🇩": "5913299849167507310",
    "🇨🇿": "5911198691036764307", "🇨🇱": "5911470957603592832", "🇨🇴": "5913773060074246009",
    "🇧🇮": "5913766441529642752", "🇧🇼": "5911513782722499475", "🇧🇦": "5913700002680541032",
    "🇧🇴": "5913638795101606133", "🇧🇹": "5913236734623093021", "🇧🇯": "5913735869952430547",
    "🇦🇷": "5913573356979884082", "🇦🇺": "5913632326880858455", "🇦🇹": "5911338831524664592",
    "🇧🇸": "5911451643135660214", "🇧🇭": "5913581663446634403", "🇧🇩": "5911365056594973179",
    "🇧🇧": "5911016996740272263", "🇧🇪": "5913529642802745141", "🇧🇿": "5913355005137522807",
    "🇦🇬": "5913389025573475085", "🇦🇴": "5913753316109586411", "🇦🇩": "5911314702398396902",
    "🇩🇿": "5913782968563800236", "🇦🇱": "5911357458797826163", "🇦🇫": "5913492040364068694",
    "🇿🇼": "5911092502265336396", "🇨🇺": "5431551436502611633", "🇰🇵": "5434142701941437163",
    "🇻🇪": "5434009132753499322", "🇸🇾": "5433910876786670092", "🇲🇲": "5433666360003540231",
    "🇳🇮": "5334807849418003620", "🇰🇷": "5913371673905598425", "🇬🇶": "5911306279967529251",
    "🇬🇱": "5292014752283774878", "🇫🇴": "5296469342039327674", "🇨🇮": "5222233374948602940",
    "🇧🇳": "5911336409163109113", "🇧🇬": "5294329219965272288", "🇧🇫": "5913407764515786948",
    "🇪🇷": "5433723401464198287", "🇲🇼": "5433968339154122439", "🇲🇷": "5433859405898594234",
    "🇳🇷": "5434131139889478358", "🇸🇦": "4985897134424328239", "🇹🇴": "5433640100573491806",
    "🇹🇻": "5433684690923961019", "🇹🇼": "5366187256937726720", "🇭🇰": "5292166459118606932",
    "🇲🇴": "6323557758096377611"
}

def apply_emojis(text):
    hidden = []
    def hide(match):
        hidden.append(match.group(0))
        return f"__TG_EMOJI_{len(hidden)-1}__"
    text = re.sub(r'<tg-emoji[^>]*>.*?</tg-emoji>', hide, text)
    for char, eid in GLOBAL_BODY_EMOJIS.items():
        text = text.replace(char, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>')
    for i, h in enumerate(hidden):
        text = text.replace(f"__TG_EMOJI_{i}__", h)
    return text

# ==========================================
# Premium Apps & Service Keywords Setup
# ==========================================
PREMIUM_APPS = {
    "Facebook": {"emoji": "📘", "id": "5429172110520003976"},
    "WhatsApp": {"emoji": "💬", "id": "5429612632430654504"},
    "Telegram": {"emoji": "✈️", "id": "5429136513831057777"},
    "Instagram": {"emoji": "📸", "id": "5429478178479447442"},
    "Google": {"emoji": "🔍", "id": "5429558795015593080"},
    "Microsoft": {"emoji": "🪟", "id": "5979047775470358891"},
    "TikTok": {"emoji": "🎵", "id": "5429132656950419591"},
    "Bkash": {"emoji": "🏦", "id": "5431552076452766597"},
    "Binance": {"emoji": "💱", "id": "5429438106434575354"},
    "Snapchat": {"emoji": "👻", "id": "5429398137468919845"},
    "Uber": {"emoji": "🚗", "id": "5298715455316303708"},
    "Discord": {"emoji": "🎬", "id": "5429594374524676604"},
    "Amazon": {"emoji": "🌟", "id": "5431358656895568355"},
    "Viber": {"emoji": "💜", "id": "5429470576387335368"},
    "Twitter": {"emoji": "🐦", "id": "5431899135580087595"},
    "Netflix": {"emoji": "🎥", "id": "5431641055290235797"},
    "Spotify": {"emoji": "🎵", "id": "5429235839244739644"},
    "Foodpanda": {"emoji": "🐼", "id": "5336879280578138635"},
    "Pathao": {"emoji": "🛵", "id": "5336879280578138635"},
    "ChatGPT": {"emoji": "🤖", "id": "5429503209548847635"},
    "Imo": {"emoji": "💭", "id": "5431378937731129128"},
    "Other": {"emoji": "📶", "id": "5429353834881261942"}
}

SERVICE_SMS_KEYWORDS = {
    "Facebook": ["facebook", "fb code", "fb", "meta"],
    "WhatsApp": ["whats", "whatsapp", "whatsapp code"],
    "Telegram": ["telegram", "tg code"],
    "Instagram": ["instagram", "ig code"],
    "Google": ["google", "Googl"],
    "Microsoft": ["microsoft", "micro", "Microsof", "xbox"],
    "TikTok": ["tiktok", "tik tok"],
    "Bkash": ["bkash"],
    "Binance": ["binance", "bnb"],
    "Snapchat": ["snapchat", "snap"],
    "Uber": ["uber"],
    "Discord": ["discord"],
    "Amazon": ["amazon", "aws"],
    "Viber": ["viber"],
    "Twitter": ["twitter", "x.com"],
    "Netflix": ["netflix"],
    "Spotify": ["spotify"],
    "Foodpanda": ["foodpanda", "panda"],
    "Pathao": ["pathao"],
    "ChatGPT": ["openai", "chatgpt"],
    "Imo": ["imo code", "imo"]
}

COUNTRY_CODES = {
    "1": "🇺🇸 USA/Canada", "380": "🇺🇦 Ukraine", "48": "🇵🇱 Poland", "7": "🇰🇿 Kazakhstan",
    "86": "🇨🇳 China", "994": "🇦🇿 Azerbaijan", "374": "🇦🇲 Armenia", "79": "🇷🇺 Russia",
    "998": "🇺🇿 Uzbekistan", "49": "🇩🇪 Germany", "81": "🇯🇵 Japan", "90": "🇹🇷 Turkey",
    "375": "🇧🇾 Belarus", "44": "🇬🇧 United Kingdom", "91": "🇮🇳 India", "55": "🇧🇷 Brazil",
    "260": "🇿🇲 Zambia", "967": "🇾🇪 Yemen", "84": "🇻🇳 Vietnam", "379": "🇻🇦 Vatican City",
    "678": "🇻🇺 Vanuatu", "598": "🇺🇾 Uruguay", "971": "🇦🇪 UAE", "256": "🇺🇬 Uganda",
    "993": "🇹🇲 Turkmenistan", "216": "🇹🇳 Tunisia", "228": "🇹🇬 Togo", "66": "🇹🇭 Thailand",
    "255": "🇹🇿 Tanzania", "992": "🇹🇯 Tajikistan", "41": "🇨🇭 Switzerland", "46": "🇸🇪 Sweden",
    "268": "🇸🇿 Eswatini", "597": "🇸🇷 Suriname", "249": "🇸🇩 Sudan", "34": "🇪🇸 Spain",
    "94": "🇱🇰 Sri Lanka", "211": "🇸🇸 South Sudan", "27": "🇿🇦 South Africa", "252": "🇸🇴 Somalia",
    "677": "🇸🇧 Solomon Islands", "386": "🇸🇮 Slovenia", "421": "🇸🇰 Slovakia", "65": "🇸🇬 Singapore",
    "232": "🇸🇱 Sierra Leone", "248": "🇸🇨 Seychelles", "381": "🇷🇸 Serbia", "221": "🇸🇳 Senegal",
    "239": "🇸🇹 Sao Tome", "378": "🇸🇲 San Marino", "685": "🇼🇸 Samoa", "970": "🇵🇸 Palestine",
    "250": "🇷🇼 Rwanda", "40": "🇷🇴 Romania", "974": "🇶🇦 Qatar", "351": "🇵🇹 Portugal",
    "63": "🇵🇭 Philippines", "51": "🇵🇪 Peru", "595": "🇵🇾 Paraguay", "675": "🇵🇬 Papua New Guinea",
    "507": "🇵🇦 Panama", "680": "🇵🇼 Palau", "92": "🇵🇰 Pakistan", "968": "🇴🇲 Oman",
    "47": "🇳🇴 Norway", "234": "🇳🇬 Nigeria", "227": "🇳🇪 Niger", "64": "🇳🇿 New Zealand",
    "31": "🇳🇱 Netherlands", "977": "🇳🇵 Nepal", "264": "🇳🇦 Namibia", "258": "🇲🇿 Mozambique",
    "212": "🇲🇦 Morocco", "382": "🇲🇪 Montenegro", "976": "🇲🇳 Mongolia", "377": "🇲🇨 Monaco",
    "373": "🇲🇩 Moldova", "960": "🇲🇻 Maldives", "223": "🇲🇱 Mali", "356": "🇲🇹 Malta",
    "596": "🇲🇶 Martinique", "692": "🇲🇭 Marshall Islands", "230": "🇲🇺 Mauritius", "52": "🇲🇽 Mexico",
    "691": "🇫🇲 Micronesia", "60": "🇲🇾 Malaysia", "254": "🇰🇪 Kenya", "261": "🇲🇬 Madagascar",
    "389": "🇲🇰 North Macedonia", "352": "🇱🇺 Luxembourg", "370": "🇱🇹 Lithuania", "423": "🇱🇮 Liechtenstein",
    "218": "🇱🇾 Libya", "231": "🇱🇷 Liberia", "686": "🇰🇮 Kiribati", "383": "🇽🇰 Kosovo",
    "965": "🇰🇼 Kuwait", "996": "🇰🇬 Kyrgyzstan", "856": "🇱🇦 Laos", "371": "🇱🇻 Latvia",
    "961": "🇱🇧 Lebanon", "266": "🇱🇸 Lesotho", "62": "🇮🇩 Indonesia", "98": "🇮🇷 Iran",
    "964": "🇮🇶 Iraq", "353": "🇮🇪 Ireland", "972": "🇮🇱 Israel", "39": "🇮🇹 Italy",
    "962": "🇯🇴 Jordan", "354": "🇮🇸 Iceland", "36": "🇭🇺 Hungary", "504": "🇭🇳 Honduras",
    "509": "🇭🇹 Haiti", "592": "🇬🇾 Guyana", "245": "🇬🇼 Guinea-Bissau", "224": "🇬🇳 Guinea",
    "502": "🇬🇹 Guatemala", "30": "🇬🇷 Greece", "233": "🇬🇭 Ghana", "995": "🇬🇪 Georgia",
    "220": "🇬🇲 Gambia", "241": "🇬🇦 Gabon", "33": "🇫🇷 France", "358": "🇫🇮 Finland",
    "679": "🇫🇯 Fiji", "251": "🇪🇹 Ethiopia", "670": "🇹🇱 Timor-Leste", "593": "🇪🇨 Ecuador",
    "20": "🇪🇬 Egypt", "503": "🇸🇻 El Salvador", "372": "🇪🇪 Estonia", "253": "🇩🇯 Djibouti",
    "45": "🇩🇰 Denmark", "357": "🇨🇾 Cyprus", "385": "🇭🇷 Croatia", "506": "🇨🇷 Costa Rica",
    "242": "🇨🇬 Congo", "243": "🇨🇩 DR Congo", "269": "🇰🇲 Comoros", "855": "🇰🇭 Cambodia",
    "237": "🇨🇲 Cameroon", "238": "🇨🇻 Cape Verde", "236": "🇨🇫 CAR", "235": "🇹🇩 Chad",
    "420": "🇨🇿 Czechia", "56": "🇨🇱 Chile", "57": "🇨🇴 Colombia", "257": "🇧🇮 Burundi",
    "267": "🇧🇼 Botswana", "387": "🇧🇦 Bosnia", "591": "🇧🇴 Bolivia", "975": "🇧🇹 Bhutan",
    "229": "🇧🇯 Benin", "54": "🇦🇷 Argentina", "61": "🇦🇺 Australia", "43": "🇦🇹 Austria",
    "973": "🇧🇭 Bahrain", "880": "🇧🇩 Bangladesh", "32": "🇧🇪 Belgium", "501": "🇧🇿 Belize",
    "244": "🇦🇴 Angola", "376": "🇦🇩 Andorra", "213": "🇩🇿 Algeria", "355": "🇦🇱 Albania",
    "93": "🇦🇫 Afghanistan", "263": "🇿🇼 Zimbabwe", "53": "🇨🇺 Cuba", "850": "🇰🇵 North Korea",
    "58": "🇻🇪 Venezuela", "963": "🇸🇾 Syria", "95": "🇲🇲 Myanmar", "505": "🇳🇮 Nicaragua",
    "82": "🇰🇷 South Korea", "240": "🇬🇶 Equatorial Guinea", "299": "🇬🇱 Greenland", "298": "🇫🇴 Faroe Islands",
    "225": "🇨🇮 Ivory Coast", "673": "🇧🇳 Brunei", "359": "🇧🇬 Bulgaria", "226": "🇧🇫 Burkina Faso",
    "291": "🇪🇷 Eritrea", "265": "🇲🇼 Malawi", "222": "🇲🇷 Mauritania", "674": "🇳🇷 Nauru",
    "966": "🇸🇦 Saudi Arabia", "676": "🇹🇴 Tonga", "688": "🇹🇻 Tuvalu", "886": "🇹🇼 Taiwan",
    "852": "🇭🇰 Hong Kong", "853": "🇲🇴 Macau", "297": "🇦🇼 Aruba", "599": "🇨🇼 Curacao",
    "500": "🇫🇰 Falkland Islands", "594": "🇬🇫 French Guiana", "590": "🇬🇵 Guadeloupe", "262": "🇷🇪 Reunion",
    "687": "🇳🇨 New Caledonia", "683": "🇳🇺 Niue", "672": "🇳🇫 Norfolk Island", "681": "🇼🇫 Wallis and Futuna",
    "682": "🇨🇰 Cook Islands", "689": "🇵🇫 French Polynesia", "350": "🇬🇮 Gibraltar", "508": "🇵🇲 Saint Pierre"
}

def get_country_info(range_str):
    clean_range = str(range_str or "").replace("X", "")
    for code, name in sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True):
        if clean_range.startswith(code): return code, name
    return clean_range[:3], f"🏳️ Other (+{clean_range[:3]})"

# ==========================================
# OTP Forwarding Pipeline 
# ==========================================

def detect_service(message_text, raw_sid=""):
    msg_lower = str(message_text).lower()
    sid_lower = str(raw_sid).lower()
    
    for service, keywords in SERVICE_SMS_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', msg_lower) or kw in msg_lower:
                return service
                
    for service in PREMIUM_APPS.keys():
        if service.lower() in sid_lower:
            return service
            
    return "Other"

def get_service_info_html(service_name):
    app_info = PREMIUM_APPS.get(service_name, PREMIUM_APPS["Other"])
    emoji_id = app_info["id"]
    normal_emoji = app_info["emoji"]
    short_name = service_name.upper()
    if short_name == "FACEBOOK": short_name = "FB"
    if short_name == "WHATSAPP": short_name = "WS"
    if short_name == "INSTAGRAM": short_name = "IG"
    
    return f'<tg-emoji emoji-id="{emoji_id}">{normal_emoji}</tg-emoji> <b>{html.escape(short_name)}</b>', emoji_id

def extract_otp_code(message_text):
    # 🌟 স্পেস বা হাইফেনসহ ৩-৮ ডিজিটের কোড ধরার লজিক
    match = re.search(r'\b(\d{3}[\s-]?\d{3,4}|\d{4,8})\b', str(message_text))
    if match: return match.group(1)
    return "COPY"

def deliver_to_inbox(user_id, service_name, raw_number, msg_text, current_balance, reward):
    c_code, c_name = get_country_info(raw_number)
    service_html, srv_eid = get_service_info_html(service_name)
    clean_raw_number = str(raw_number).lstrip('+') 
    
    text = (
        f"— — — — — — — — — —\n"
        f"<blockquote>{service_html} <code>+{clean_raw_number}</code></blockquote>\n"
        f"<blockquote><tg-emoji emoji-id=\"5420323438508155202\">➕</tg-emoji> <b>ADDED</b>  ➜ {reward:.2f} TK</blockquote>\n"
        f"<blockquote><tg-emoji emoji-id=\"5190899075968441286\">💳</tg-emoji> <b>BALANCE</b> ➜ {current_balance:.2f} TK</blockquote>\n"
        f"— — — — — — — — — —"
    )
    otp = extract_otp_code(msg_text)
    markup = {"inline_keyboard": [[{"text": f"{otp}", "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"}]]}
    send_message(user_id, text, reply_markup=markup)

def generate_otp_display(service_name, raw_number, message_text):
    c_code, c_name = get_country_info(raw_number)
    
    parts = c_name.split(" ", 1)
    country_emoji = parts[0]
    
    if len(raw_number) > 6:
        masked_number = f"{raw_number[:3]}DXA{raw_number[-3:]}"
    else:
        masked_number = raw_number
        
    service_html, srv_eid = get_service_info_html(service_name)
    
    text = (
        f"━━━━━━━━━━━━━━━━━\n"
        f"{service_html} ➜ {country_emoji} <code>{html.escape(masked_number)}</code>\n"
        f"━━━━━━━━━━━━━━━━━"
    )
    
    otp = extract_otp_code(message_text)
    
    # 🌟 রেঞ্জ বের করার লজিক (ডিফল্ট ৫ ডিজিট)
    clean_range = str(raw_number)[:5] if len(str(raw_number)) >= 5 else str(raw_number)
    deep_link = f"https://t.me/{BOT_USERNAME}?start=alloc_{clean_range}_{service_name.lower()}"
    
    markup = {"inline_keyboard": []}
    
    # 🌟 প্রথম লাইন (CHANNEL এবং OTP)
    row1 = []
    main_channel_link = bot_settings.get("main_channel_link", "")
    if main_channel_link:
        row1.append({"text": "𝗖𝗛𝗔𝗡𝗡𝗘𝗟", "url": main_channel_link, "icon_custom_emoji_id": "5429353834881261942", "style": "primary"})
        
    row1.append({"text": f"{otp}", "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"})
    
    markup["inline_keyboard"].append(row1)
    
    # 🌟 দ্বিতীয় লাইন (GET NUMBER)
    markup["inline_keyboard"].append([
        {"text": "GET NUMBER", "url": deep_link, "icon_custom_emoji_id": "5429167978761461870", "style": "danger"}
    ])
    
    return text, markup

def send_otp_to_groups(formatted_text, markup):
    global otp_forward_groups
    if not otp_forward_groups: return False
        
    sent_any = False
    for group_id in otp_forward_groups:
        resp = send_message(group_id, formatted_text, reply_markup=markup)
        if resp and resp.get("ok"): sent_any = True
        time.sleep(1) 
        
    return sent_any

# ==========================================
# 2oo9 API & Background Listeners
# ==========================================
def fetch_live_access():
    headers = {"mauthapi": get_api_key()}
    try:
        res = requests.get(f"{API_2OO9_BASE}/liveaccess", headers=headers, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200:
            return data.get("data", {}).get("services", [])
    except: pass
    return []

def fetch_live_number(rid):
    headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
    payload = {"rid": str(rid)}
    try:
        res = requests.post(f"{API_2OO9_BASE}/getnum", headers=headers, json=payload, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200:
            return data.get("data", {})
    except: pass
    return None

def voltx_console_listener():
    global recent_traffic, voltx_dynamic_data
    cycle_count = 0
    while True:
        try:
            headers = {"mauthapi": get_api_key()}
            res = requests.get(f"{API_2OO9_BASE}/console", headers=headers, timeout=10)
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                hits = data.get("data", {}).get("hits", [])
                new_traffic, seen_signatures = [], set()
                current_time = int(time.time())
                
                for h in hits:
                    sig = f"{h.get('time', 0)}_{h.get('range', '')}"
                    if sig not in seen_signatures:
                        h['local_receive_time'] = current_time 
                        new_traffic.append(h)
                        seen_signatures.add(sig)
                        
                        raw_sid = h.get("sid") or "Unknown"
                        raw_msg = h.get("message") or ""
                        raw_range = str(h.get("range", "")).replace("X", "")
                        
                        if raw_range:
                            detected_sid = detect_service(raw_msg, raw_sid)
                            app_info = PREMIUM_APPS.get(detected_sid, PREMIUM_APPS["Other"])
                            emoji_id, normal_emoji = app_info["id"], app_info["emoji"]
                            
                            if detected_sid not in voltx_dynamic_data:
                                voltx_dynamic_data[detected_sid] = {"emoji_id": emoji_id, "normal_emoji": normal_emoji, "ranges": {}}
                            if raw_range not in voltx_dynamic_data[detected_sid]["ranges"]:
                                voltx_dynamic_data[detected_sid]["ranges"][raw_range] = {"last_seen": current_time, "hits": 0}
                            voltx_dynamic_data[detected_sid]["ranges"][raw_range]["last_seen"] = current_time
                            voltx_dynamic_data[detected_sid]["ranges"][raw_range]["hits"] += 1

                fifteen_mins_ago = current_time - 900
                for h in recent_traffic:
                    if h.get('local_receive_time', 0) >= fifteen_mins_ago:
                        sig = f"{h.get('time', 0)}_{h.get('range', '')}"
                        if sig not in seen_signatures:
                            new_traffic.append(h)
                            seen_signatures.add(sig)
                        
                new_traffic.sort(key=lambda x: x.get('local_receive_time', 0), reverse=True)
                recent_traffic = new_traffic

                services_to_delete = []
                for sid, s_data in voltx_dynamic_data.items():
                    ranges_to_delete = []
                    for r, r_data in s_data["ranges"].items():
                        if current_time - r_data["last_seen"] > 300: ranges_to_delete.append(r)
                    for r in ranges_to_delete: del s_data["ranges"][r]
                    if not s_data["ranges"]: services_to_delete.append(sid)
                for sid in services_to_delete: del voltx_dynamic_data[sid]

                cycle_count += 1
                if cycle_count % 3 == 0: save_local_data()

        except Exception: pass
        time.sleep(10)

def voltx_sms_listener():
    global recent_success_otps, otp_forward_groups, user_active_sessions
    group_sent_otps = set() 
    while True:
        try:
            headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
            res = requests.get(f"{API_2OO9_BASE}/success-otp", headers=headers, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                otps = []
                
                if isinstance(data, dict):
                    if "data" in data and isinstance(data["data"], list): 
                        otps = data["data"]
                    elif "data" in data and isinstance(data["data"], dict):
                        if "otps" in data["data"]: 
                            otps = data["data"]["otps"]
                        elif "hits" in data["data"]: 
                            otps = data["data"]["hits"]
                    elif "otps" in data: 
                        otps = data["otps"]
                    elif "hits" in data: 
                        otps = data["hits"]
                elif isinstance(data, list):
                    otps = data
                    
                for otp_data in reversed(otps):
                    msg_text = str(otp_data.get("message", otp_data.get("sms", otp_data.get("code", ""))))
                    raw_number = str(otp_data.get("number", otp_data.get("phone", "")))
                    raw_service = str(otp_data.get("sid", otp_data.get("service", "Unknown")))
                    
                    if not msg_text or not raw_number: continue
                    
                    sig = f"{raw_number}_{msg_text}"
                    detected_service = detect_service(msg_text, raw_service)
                    
                    # 1. Forward to Groups (RAM only tracking - resets on restart)
                    if sig not in group_sent_otps:
                        group_sent_otps.add(sig)
                        if otp_forward_groups:
                            formatted_message, markup = generate_otp_display(detected_service, raw_number, msg_text)
                            send_otp_to_groups(formatted_message, markup)
                    
                    # 2. Check Inbox Ownership (Strictly persistent tracking)
                    if sig not in recent_success_otps:
                        recent_success_otps.add(sig)
                        
                        owner_id = None
                        last_8_digits = raw_number[-8:] if len(raw_number) > 8 else raw_number
                        for active_num, uid in list(user_active_sessions.items()):
                            if active_num.endswith(last_8_digits):
                                owner_id = uid
                                del user_active_sessions[active_num]
                                break
                                
                        if owner_id:
                            reward = get_otp_reward(detected_service)
                            update_user_stats(owner_id, reward, 0)
                            
                            # 🌟 ইনবক্সে মেসেজ পাঠানোর ফাংশন কল করা হলো
                            user_balance = get_user(owner_id).get("balance", 0.0)
                            deliver_to_inbox(owner_id, detected_service, raw_number, msg_text, user_balance, reward)
                            
                            today_date = time.strftime("%Y-%m-%d")
                            if daily_user_otps.get("date") != today_date:
                                daily_user_otps["date"] = today_date
                                daily_user_otps["users"] = {}
                            uid_str = str(owner_id)
                            daily_user_otps["users"][uid_str] = daily_user_otps["users"].get(uid_str, 0) + 1
                        
                        update_daily_stat("otps", 1)
                        save_local_data()
                        time.sleep(1) 
                        
            if len(recent_success_otps) > 2000:
                recent_success_otps = set(list(recent_success_otps)[-1000:])
                save_local_data()
            if len(group_sent_otps) > 2000:
                group_sent_otps = set(list(group_sent_otps)[-1000:])
        except Exception:
            pass
        time.sleep(10)

# ==========================================
# Hybrid Database Initialization
# ==========================================
def init_sqlite():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT DEFAULT 'User', balance REAL DEFAULT 0.0, total_invites INTEGER DEFAULT 0)")
    try: cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT 'User'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN total_otps INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

def migrate_sqlite_to_firebase():
    global db_firebase, user_cache
    if not db_firebase: return
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name, balance, total_invites FROM users")
        rows = cursor.fetchall()
        if not rows: return conn.close()
        
        count = 0
        batch = db_firebase.batch()
        for row in rows:
            uid, fname, bal, inv = row
            doc_ref = db_firebase.collection('users').document(str(uid))
            batch.set(doc_ref, {"user_id": uid, "first_name": fname, "balance": firestore.Increment(bal), "total_invites": firestore.Increment(inv)}, merge=True)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db_firebase.batch()
        if count % 400 != 0: batch.commit()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        user_cache.clear()
    except Exception as e: print(f"Migration Error: {e}")

def init_firebase_from_file():
    global current_db_mode, db_firebase, bot_settings, force_join_status, force_join_channels, otp_forward_groups, otp_button_link, voltx_keys, voltx_auto_mode
    if os.path.exists("temp_firebase.json"):
        try:
            if not firebase_admin._apps: 
                firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
            db_firebase = firestore.client()
            current_db_mode = "firebase"
            print("✅ Firebase Auto-Connected on Startup!")
            
            doc = db_firebase.collection('settings').document('bot_config').get()
            if doc.exists:
                data = doc.to_dict()
                if "bot_settings" in data: bot_settings.update(data["bot_settings"])
                if "force_join_status" in data: force_join_status = data["force_join_status"]
                if "force_join_channels" in data: force_join_channels = data["force_join_channels"]
                if "otp_forward_groups" in data: otp_forward_groups = data["otp_forward_groups"]
                if "otp_button_link" in data: otp_button_link = data["otp_button_link"]
                if "voltx_keys" in data: voltx_keys = data["voltx_keys"]
                if "voltx_auto_mode" in data: voltx_auto_mode = data["voltx_auto_mode"]
                print("✅ Settings synced from Firebase!")

            # 🌟 One-Time Sync on Startup (বট চালু হওয়ার সময় অটো সিঙ্ক)
            try:
                local_users = set()
                if os.path.exists(USERS_LIST_FILE):
                    with open(USERS_LIST_FILE, "r") as f:
                        local_users = set(json.load(f))
                
                docs = db_firebase.collection('users').select([]).stream()
                fb_users = set(int(doc.id) for doc in docs)
                
                combined_users = local_users.union(fb_users)
                if len(combined_users) > len(local_users):
                    with open(USERS_LIST_FILE, "w") as f:
                        json.dump(list(combined_users), f)
                    print(f"✅ Auto-Synced {len(fb_users)} users on Startup!")
            except Exception as e:
                print(f"Startup Sync Error: {e}")

        except Exception as e:
            print(f"❌ Firebase Auto-Connect Error: {e}")

def get_user(user_id):
    global current_db_mode, db_firebase, user_cache
    if user_id in user_cache: return user_cache[user_id]
    if current_db_mode == "firebase" and db_firebase:
        doc = db_firebase.collection('users').document(str(user_id)).get()
        if doc.exists:
            user_data = doc.to_dict()
            user_cache[user_id] = user_data 
            return user_data
        return None
    else: 
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, balance, total_invites FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row: 
            user_data = {"user_id": user_id, "first_name": row[0], "balance": row[1], "total_invites": row[2]}
            user_cache[user_id] = user_data 
            return user_data
        return None

def add_user(user_id, first_name="User"):
    global current_db_mode, db_firebase, user_cache
    add_to_broadcast_list(user_id) 
    if user_id in user_cache and user_cache[user_id]["first_name"] == first_name: return 
    
    if current_db_mode == "firebase" and db_firebase:
        doc_ref = db_firebase.collection('users').document(str(user_id))
        if not doc_ref.get().exists:
            new_data = {"user_id": user_id, "first_name": first_name, "balance": 0.0, "total_invites": 0}
            doc_ref.set(new_data)
            user_cache[user_id] = new_data
        else: 
            doc_ref.update({"first_name": first_name})
            if user_id in user_cache: user_cache[user_id]["first_name"] = first_name
    else: 
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, balance, total_invites) VALUES (?, ?, 0.0, 0)", (user_id, first_name))
        cursor.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
        conn.commit()
        conn.close()
        if user_id not in user_cache: user_cache[user_id] = {"user_id": user_id, "first_name": first_name, "balance": 0.0, "total_invites": 0}
        else: user_cache[user_id]["first_name"] = first_name

def update_user_stats(user_id, balance_add, invite_add):
    global current_db_mode, db_firebase, user_cache
    bal_add = float(balance_add)
    inv_add = int(invite_add)
    
    if user_id not in user_cache:
        get_user(user_id) # Ensure user is loaded
        
    if user_id in user_cache:
        user_cache[user_id]["balance"] = round(user_cache[user_id]["balance"] + bal_add, 2) # 🌟 Fix: Round balance
        user_cache[user_id]["total_invites"] += inv_add
        
    if current_db_mode == "firebase" and db_firebase:
        db_firebase.collection('users').document(str(user_id)).update({"balance": firestore.Increment(bal_add), "total_invites": firestore.Increment(inv_add)})
    else: 
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ?, total_invites = total_invites + ? WHERE user_id = ?", (bal_add, inv_add, user_id))
        conn.commit()
        conn.close()

def get_total_users(): return len(get_all_user_ids()) 

def get_top_users(limit=5):
    global current_db_mode, db_firebase
    if current_db_mode == "firebase" and db_firebase:
        docs = db_firebase.collection('users').order_by('balance', direction=firestore.Query.DESCENDING).limit(limit).stream()
        return [(doc.to_dict().get("user_id"), doc.to_dict().get("first_name", "User"), doc.to_dict().get("balance")) for doc in docs]
    else:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

# ==========================================
# Sub-Menu Builders
# ==========================================
def get_otp_group_keyboard():
    kb = {"inline_keyboard": []}
    
    link_display = otp_button_link if otp_button_link else "Not Set"
    if len(link_display) > 25: link_display = link_display[:25] + "..."
    kb["inline_keyboard"].append([{"text": f"Link: {link_display}", "callback_data": "edit_otp_link", "icon_custom_emoji_id": "5420517437885943844", "style": "primary"}])
    
    mc_link = bot_settings.get("main_channel_link", "")
    mc_display = mc_link if mc_link else "Not Set"
    if len(mc_display) > 25: mc_display = mc_display[:25] + "..."
    kb["inline_keyboard"].append([{"text": f"Main Channel: {mc_display}", "callback_data": "edit_main_channel", "icon_custom_emoji_id": "5429353834881261942", "style": "primary"}])
    
    if otp_forward_groups:
        grp = otp_forward_groups[0]
        kb["inline_keyboard"].append([{"text": f"Delete Group: {grp}", "callback_data": "del_otp_group_0", "icon_custom_emoji_id": "5422557736330106570", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "Set Forward Group", "callback_data": "add_otp_group", "icon_custom_emoji_id": "5429501315468270290", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5267490665117275176", "style": "danger"}])
    return kb

def get_force_join_keyboard():
    kb = {"inline_keyboard": []}
    status_text = "STATUS: ON" if force_join_status else "STATUS: OFF"
    status_icon = "5352694861990501856" if force_join_status else "5420130255174145507"
    
    kb["inline_keyboard"].append([{"text": status_text, "callback_data": "toggle_fj", "icon_custom_emoji_id": status_icon, "style": "primary" if force_join_status else "danger"}])
    
    for idx, ch in enumerate(force_join_channels):
        name = ch.get("username", ch.get("title", f"Channel {idx}"))
        kb["inline_keyboard"].append([{"text": f"Delete: {name}", "callback_data": f"del_fj_{idx}", "icon_custom_emoji_id": "5438178416421544431", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "Add Channel", "callback_data": "add_fj", "icon_custom_emoji_id": "5429501315468270290", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "Back", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5438541186539232243", "style": "primary"}])
    return kb

def get_force_join_alert_keyboard():
    kb = {"inline_keyboard": []}
    for ch in force_join_channels:
        name = ch.get("title", ch.get("username", "Our Channel"))
        url = ch.get("invite_link", "")
        if not url and ch.get("username"): url = f"https://t.me/{ch['username'].replace('@', '')}"
        # 🌟 Join বাটনে প্রিমিয়াম লিংক ইমোজি
        kb["inline_keyboard"].append([{"text": f"JOIN {name}", "url": url, "icon_custom_emoji_id": "5420517437885943844", "style": "danger"}])
    
    # 🌟 Verify বাটনে প্রিমিয়াম টিকমার্ক ইমোজি
    kb["inline_keyboard"].append([{"text": "VERIFY", "callback_data": "check_fj_joined", "icon_custom_emoji_id": "5352694861990501856", "style": "success"}])
    return kb

def get_voltx_keys_keyboard():
    kb = {"inline_keyboard": []}
    status_text = "VOLTX AUTO: ON" if voltx_auto_mode else "VOLTX AUTO: OFF"
    status_icon = "5352694861990501856" if voltx_auto_mode else "5420130255174145507"
    
    kb["inline_keyboard"].append([{"text": status_text, "callback_data": "toggle_vk", "icon_custom_emoji_id": status_icon, "style": "primary" if voltx_auto_mode else "danger"}])
    
    for idx, key in enumerate(voltx_keys):
        masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else key
        kb["inline_keyboard"].append([{"text": f"Delete: {masked_key}", "callback_data": f"del_vk_{idx}", "icon_custom_emoji_id": "5438178416421544431", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "Add Voltx Key", "callback_data": "add_vk", "icon_custom_emoji_id": "5429501315468270290", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "Back", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5438541186539232243", "style": "primary"}])
    return kb

def get_main_keyboard(user_id):
    keyboard_layout = [
        [
            {"text": "LIVE NUMBER", "icon_custom_emoji_id": "5456259593082522998", "style": "danger"},
            {"text": "LIVE TRAFFIC", "icon_custom_emoji_id": "5429571662737611814", "style": "primary"}
        ],
        [
            {"text": "INVITE FRIEND", "icon_custom_emoji_id": "5384394344859974865", "style": "success"},
            {"text": "WALLET", "icon_custom_emoji_id": "5429105001655999635", "style": "danger"}
        ],
        [
            {"text": "LEADERBOARD", "icon_custom_emoji_id": "5240021484516185513", "style": "primary"}
        ]
    ]
    if user_id == ADMIN_ID:
        keyboard_layout.append([{"text": "OWNER PANEL", "icon_custom_emoji_id": "5429427051188756948", "style": "success"}])
    return {"keyboard": keyboard_layout, "resize_keyboard": True}

def get_admin_inline_keyboard():
    global current_db_mode
    db_status = "SQLITE ACTIVE" if current_db_mode == "sqlite" else "FIREBASE ACTIVE"
    
    return {
        "inline_keyboard": [
            [
                {
                    "text": "VOLTX SETTINGS", 
                    "callback_data": "manage_voltx", 
                    "icon_custom_emoji_id": "5240122519326860770", 
                    "style": "danger"
                }
            ],
            [
                {
                    "text": "BROADCAST", 
                    "callback_data": "broadcast_menu", 
                    "icon_custom_emoji_id": "5296633779157243809", 
                    "style": "primary"
                },
                {
                    "text": "FORCE JOIN", 
                    "callback_data": "manage_fj", 
                    "icon_custom_emoji_id": "5429353834881261942", 
                    "style": "success"
                }
            ],
            [
                {
                    "text": "OTP GROUP", 
                    "callback_data": "manage_otp_group", 
                    "icon_custom_emoji_id": "5429208347159077664", 
                    "style": "danger"
                },
                {
                    "text": "USER CONTROL", 
                    "callback_data": "user_control", 
                    "icon_custom_emoji_id": "5429274992166609833", 
                    "style": "primary"
                }
            ],
            [
                {
                    "text": "DXA CONTROL", 
                    "callback_data": "dxa_control", 
                    "icon_custom_emoji_id": "5240451569656308978", 
                    "style": "danger"
                }
            ],
            [
                {
                    "text": "UPLOAD FIREBASE", 
                    "callback_data": "upload_firebase", 
                    "icon_custom_emoji_id": "5429362935916962442", 
                    "style": "primary"
                }
            ],
            [
                {
                    "text": db_status, 
                    "callback_data": "db_status", 
                    "icon_custom_emoji_id": "5429591316507963112", 
                    "style": "success"
                }
            ],
            [
                {
                    "text": "CLOSE", 
                    "callback_data": "close_panel", 
                    "icon_custom_emoji_id": "5438541186539232243", 
                    "style": "danger"
                }
            ]
        ]
    }

def dxa_control_keyboard():
    grp = bot_settings.get("w_group", "")
    grp_status = grp if grp else "NOT SET"
    return {"inline_keyboard": [
        [{"text": f"MIN WITHDRAW: {bot_settings['min_withdraw']}", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "dxa_min_w", "style": "success"},
         {"text": "OTP CONTROL", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "dxa_otp_control", "style": "primary"}],
        [{"text": f"REFER REWARD: {bot_settings.get('refer_reward', 0.2)}", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "dxa_ref_r", "style": "success"},
         {"text": f"COOLDOWN: {bot_settings['cooldown']}s", "icon_custom_emoji_id": "5337172996211648018", "callback_data": "dxa_cool", "style": "primary"}],
        [{"text": f"NUM/REQ: {bot_settings['num_req']}", "icon_custom_emoji_id": "5337132498965010628", "callback_data": "dxa_num_req", "style": "success"},
         {"text": "W. METHODS", "icon_custom_emoji_id": "5190899075968441286", "callback_data": "manage_w_methods", "style": "primary"}],
        [{"text": f"W. GROUP: {grp_status}", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "dxa_w_group", "style": "success"}],
        [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]
    ]}

def dxa_otp_control_keyboard():
    kb = {"inline_keyboard": [
        [{"text": f"Default Rate: {bot_settings['otp_default_rate']}", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "dxa_def_rate", "style": "primary"}],
        [{"text": "Set Service Rate", "icon_custom_emoji_id": "5395444784611480792", "callback_data": "dxa_srv_rate", "style": "success"}]
    ]}
    
    # অ্যাড করা স্পেসিফিক সার্ভিস রেটগুলো ডায়নামিক ইনলাইন বাটন হিসেবে দেখানোর জন্য
    for srv_name, rate in bot_settings.get("otp_service_rates", {}).items():
        app_info = PREMIUM_APPS.get(srv_name, PREMIUM_APPS["Other"])
        
        # 🌟 BUG FIX: Added emoji inside text for DXA control settings too
        kb["inline_keyboard"].append([{"text": f"Delete: {app_info['emoji']} {srv_name} ({rate})", "icon_custom_emoji_id": app_info["id"], "callback_data": f"del_srv_rate_{srv_name}", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_control", "style": "danger"}])
    return kb
    
def dxa_manage_w_methods_keyboard():
    kb = {"inline_keyboard": []}
    for idx, method in enumerate(bot_settings.get("w_methods", [])):
        kb["inline_keyboard"].append([{"text": f"Delete: {method}", "callback_data": f"del_w_method_{idx}", "style": "danger"}])
    kb["inline_keyboard"].append([{"text": "Add Method", "callback_data": "add_w_method", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "dxa_control", "style": "primary"}])
    return kb

def get_user_control_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "USER PROFILE", "icon_custom_emoji_id": "5352861489541714456", "callback_data": "uc_profile", "style": "primary"}],
            [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]
        ]
    }

def get_user_profile_keyboard(target_uid):
    return {
        "inline_keyboard": [
            [{"text": "BALANCE", "icon_custom_emoji_id": "5429612421977253466", "callback_data": f"uc_balance_{target_uid}", "style": "success"}],
            [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "user_control", "style": "danger"}]
        ]
    }

def get_upload_firebase_keyboard():
    return {"inline_keyboard": [[{"text": "CANCEL", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5420130255174145507", "style": "danger"}]]}

def get_back_only_keyboard():
    return {"inline_keyboard": [[{"text": "BACK", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}]]}

def get_leaderboard_keyboard():
    return {"inline_keyboard": [[{"text": "REFRESH", "callback_data": "refresh_leaderboard", "icon_custom_emoji_id": "5229111790842952353", "style": "success"}]]}

def get_owner_panel_text():
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date") != today:
        daily_stats["date"] = today
        daily_stats["numbers"] = 0
        daily_stats["otps"] = 0
        
    return (
        "<b>📊 OWNER ZONE 📊</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<b>📊 DATABASE OVERVIEW</b>\n"
        "— — — — — — — — — —\n"
        f"<blockquote><b>👤 TOTAL USER         » {get_total_users()}</b></blockquote>\n"
        f"<blockquote><b>📱 TODAY NUMBER  » {daily_stats['numbers']}</b></blockquote>\n"
        f"<blockquote><b>💬 TODAY OTP           » {daily_stats['otps']}</b></blockquote>\n"
        "━━━━━━━━━━━━━━━━━━"
    )

def get_leaderboard_text():
    global cached_leaderboard_text
    if cached_leaderboard_text:
        return cached_leaderboard_text
    return "⏳ <b>Loading leaderboard, please wait...</b>"

def get_live_traffic_content():
    global recent_traffic
    hits_to_show = recent_traffic
    markup = {"inline_keyboard": [[{"text": "REFRESH", "callback_data": "refresh_traffic", "icon_custom_emoji_id": "5229111790842952353", "style": "primary"}]]}
    
    if not hits_to_show:
        return "╔═════════════════╗\n║  <tg-emoji emoji-id=\"5352877703043258544\">📈</tg-emoji> <b>15M LIVE TRAFFIC</b>\n╚═════════════════╝\n<i>No traffic data available.</i>\n━━━━━━━━━━━━━━━━━━━", markup

    service_counts = {}
    for h in hits_to_show:
        raw_sid = h.get("sid") or "Unknown"
        raw_msg = h.get("message") or ""
        detected_sid = detect_service(raw_msg, raw_sid)
        app_info = PREMIUM_APPS.get(detected_sid, PREMIUM_APPS["Other"])
        
        if detected_sid not in service_counts: service_counts[detected_sid] = {"count": 0, "emoji_id": app_info["id"], "normal_emoji": app_info["emoji"]}
        service_counts[detected_sid]["count"] += 1

    sorted_services = sorted(service_counts.items(), key=lambda item: item[1]["count"], reverse=True)[:6]

    msg = "╔═════════════════╗\n║  <tg-emoji emoji-id=\"5352877703043258544\">📈</tg-emoji> <b>15M LIVE TRAFFIC</b>\n╚═════════════════╝\n"
    fire_emoji_id = "5337267511261960341"
    
    for i, (sid, data) in enumerate(sorted_services):
        msg += f"<tg-emoji emoji-id=\"{data['emoji_id']}\">{data['normal_emoji']}</tg-emoji> {html.escape(str(sid))} ➜ <tg-emoji emoji-id=\"{fire_emoji_id}\">🔥</tg-emoji> {data['count']} OTP\n"
        if i < len(sorted_services) - 1: msg += "— — — — — — — — — —\n"
    msg += "━━━━━━━━━━━━━━━━━━━"
    return msg, markup

def get_services_content():
    global cached_services_kb
    if cached_services_kb:
        return "📱 <b>Select Top Service:</b>", cached_services_kb
    return "⏳ <b>Loading services, please try again in a few seconds...</b>", None

def get_countries_content(sid_short):
    global cached_countries_kb
    if sid_short in cached_countries_kb:
        return f"🌍 <b>Select Country:</b>", cached_countries_kb[sid_short], None
    return None, None, "❌ <b>No active countries for this service. (Out of Stock)</b>"

def get_number_allocation_content(sid_short, c_code, user_id=None):
    global voltx_auto_mode, voltx_dynamic_data, user_active_sessions, bot_settings, otp_button_link
    target_ranges = []
    full_sid = sid_short
    
    if voltx_auto_mode:
        for sid, data in voltx_dynamic_data.items():
            if sid.lower().startswith(sid_short.lower()):
                full_sid = sid
                for r, r_data in data["ranges"].items():
                    if c_code.startswith(r) or r.startswith(c_code): 
                        target_ranges.append((r, r_data["hits"]))
                break
        target_ranges.sort(key=lambda x: x[1], reverse=True)
        best_ranges = [x[0] for x in target_ranges[:3]]
    else:
        services_data = fetch_live_access()
        for s in services_data:
            sid_val = s.get('sid') or ""
            if sid_val.lower().startswith(sid_short.lower()):
                full_sid = sid_val
                for r in s.get('ranges', []):
                    clean_r = str(r).replace("X", "")
                    if c_code.startswith(clean_r) or clean_r.startswith(c_code):
                        if clean_r not in target_ranges:
                            target_ranges.append(clean_r)
                break
        best_ranges = target_ranges[:3]
            
    # 🌟 এপিআই লিস্টে না থাকলেও লিংকের রেঞ্জ দিয়ে সরাসরি রিকোয়েস্ট করবে
    if not best_ranges: 
        best_ranges = [c_code]
        
    req_count = bot_settings.get("num_req", 1)
    fetched_numbers = []
    
    for _ in range(req_count):
        selected_rid = random.choice(best_ranges)
        num_data = fetch_live_number(selected_rid)
        if num_data:
            full_number = html.escape(str(num_data.get("full_number", "")))
            country = html.escape(str(num_data.get("country", "Unknown")))
            operator = html.escape(str(num_data.get("operator", "Unknown")))
            fetched_numbers.append((full_number, country, operator))
            
            if user_id and full_number:
                user_active_sessions[str(full_number)] = user_id
    
    if fetched_numbers:
        update_daily_stat("numbers", len(fetched_numbers))
        save_local_data()
        
        service_html, srv_eid = get_service_info_html(full_sid)
        _, country_with_flag = get_country_info(c_code)
        
        msg = (
            f"━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id=\"5337172996211648018\">⌛</tg-emoji> <b>ACTIVE NUMBER 15M</b>\n"
            f"— — — — — — — — — —\n"
            f"{service_html} ➜ {country_with_flag}\n"
            f"━━━━━━━━━━━━━━━"
        )
        
        kb = {"inline_keyboard": []}
        
        for f_num, ctry, op in fetched_numbers:
            clean_f_num = str(f_num).lstrip('+') 
            kb["inline_keyboard"].append([
                {"text": f"+{clean_f_num}", "icon_custom_emoji_id": "5226929552319594190", "copy_text": {"text": f"+{clean_f_num}"}, "style": "primary"}
            ])
            
        kb["inline_keyboard"].append([
            {"text": "Change Number", "icon_custom_emoji_id": "5429386648431405093", "callback_data": f"cc_{sid_short}_{c_code}", "style": "danger"},
            {"text": "OTP Group", "icon_custom_emoji_id": "5314366268898300483", "url": otp_button_link, "style": "success"}
        ])
        kb["inline_keyboard"].append([
            {"text": "BACK", "icon_custom_emoji_id": "5438541186539232243", "callback_data": f"srv_{sid_short}", "style": "danger"}
        ])
        
        return msg, kb
    else:
        return f"❌ <b>Out of stock in these ranges. Please try again.</b>", {"inline_keyboard": [[{"text": "BACK", "callback_data": f"srv_{sid_short}", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}]]}

# ==========================================
# Background Broadcaster Tool 
# ==========================================
def broadcast_worker(from_chat_id, message_id, target_msg_id):
    users = get_all_user_ids() 
    success_count = 0
    for uid in users:
        try:
            res = copy_message(uid, from_chat_id, message_id)
            if res and res.get("ok"): success_count += 1
            time.sleep(0.05) 
        except: pass
        
    send_message(from_chat_id, f"✅ <b>Broadcast Completed!</b>\nSuccessfully sent to {success_count} users out of {len(users)}.")
    
    if target_msg_id:
        edit_message(from_chat_id, target_msg_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())

# ==========================================
# Message Handlers
# ==========================================
def handle_message(message):
    global waiting_for_firebase, current_db_mode, db_firebase, user_states, voltx_keys, force_join_channels, otp_forward_groups, otp_button_link, bot_settings
    
    # 🌟 বট শুধুমাত্র ইনবক্সের মেসেজে রিপ্লাই দিবে (গ্রুপ ইগনোর করবে)
    if message.get("chat", {}).get("type") != "private":
        return
        
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "")
    message_id = message["message_id"]
    first_name = message["from"].get("first_name", "User")

    if text == "🔙 BACK" and user_id == ADMIN_ID:
        send_message(chat_id, "❌ <b>Action Cancelled!</b>", reply_markup=get_main_keyboard(user_id)) 
        if user_id in user_states: del user_states[user_id]
        send_message(chat_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        return

    # Native Chat Selection Listener
    if "chat_shared" in message:
        shared_chat_id = message["chat_shared"]["chat_id"]
        if user_id == ADMIN_ID and user_id in user_states:
            state_data = user_states[user_id]
            state = state_data.get("state")
            target_msg_id = state_data.get("msg_id")
            
            send_message(chat_id, "✅ <b>Successfully Selected!</b>", reply_markup=get_main_keyboard(user_id)) 
            
            if state == "waiting_otp_group":
                otp_forward_groups.clear() 
                otp_forward_groups.append(str(shared_chat_id))
                
                inv_res = requests.post(BASE_URL + "exportChatInviteLink", json={"chat_id": shared_chat_id}).json()
                if inv_res.get("ok"):
                    otp_button_link = inv_res["result"]
                
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
                del user_states[user_id]
                return
                
            elif state == "waiting_dxa_w_group":
                bot_settings["w_group"] = str(shared_chat_id)
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
                del user_states[user_id]
                return
                
            elif state == "waiting_fj_channel":
                chat_details = get_chat_details(str(shared_chat_id))
                if chat_details:
                    force_join_channels.append(chat_details)
                    save_local_data()
                    if target_msg_id: edit_message(chat_id, target_msg_id, "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
                else:
                    if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Failed to verify channel! Make sure bot is admin.</b>", reply_markup=get_back_only_keyboard())
                del user_states[user_id]
                return

    if not is_user_joined(user_id):
        fj_msg = (
            "<b>════《 <tg-emoji emoji-id=\"5337267511261960341\">🔥</tg-emoji> ACCESS REQUIRED 》════</b>\n\n"
            "<b><tg-emoji emoji-id=\"5420517437885943844\">🔗</tg-emoji> JOIN ALL CHANNELS BELOW TO USE THIS BOT.</b>\n\n"
            "<b><tg-emoji emoji-id=\"5352694861990501856\">✅</tg-emoji> JOIN ALL CHANNELS, THEN CLICK VERIFY.</b>"
        )
        send_message(chat_id, fj_msg, reply_markup=get_force_join_alert_keyboard())
        return

    # Handle Admin Input States
    if user_id == ADMIN_ID and user_id in user_states:
        state_data = user_states[user_id]
        if isinstance(state_data, dict):
            state = state_data.get("state")
            target_msg_id = state_data.get("msg_id")
        else:
            state = state_data
            target_msg_id = None
            
        if state == "waiting_vk_key":
            voltx_keys.append(text.strip())
            save_local_data()
            if target_msg_id: edit_message(chat_id, target_msg_id, "🔑 <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_otp_link":
            if text.startswith("http"):
                otp_button_link = text.strip()
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
            else:
                if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Invalid URL format. Must start with http/https.</b>", reply_markup=get_back_only_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_main_channel_link":
            if text.startswith("http"):
                bot_settings["main_channel_link"] = text.strip()
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
            else:
                if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Invalid URL format. Must start with http/https.</b>", reply_markup=get_back_only_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_broadcast":
            if target_msg_id: edit_message(chat_id, target_msg_id, "⏳ <b>Broadcasting message to all users...</b>")
            threading.Thread(target=broadcast_worker, args=(chat_id, message_id, target_msg_id), daemon=True).start()
            del user_states[user_id]
            return
            
        elif state == "waiting_firebase":
            try:
                # 🌟 ফাইল আপলোড সাপোর্ট অ্যাড করা হলো
                if "document" in message:
                    file_id = message["document"]["file_id"]
                    file_info = requests.get(BASE_URL + f"getFile?file_id={file_id}").json()
                    file_path = file_info["result"]["file_path"]
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    text = requests.get(file_url).text
                
                # 🌟 স্মার্ট কোট (Smart Quotes) বা ভুল টেক্সট ফিক্স
                text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

                firebase_cred = json.loads(text)
                with open("temp_firebase.json", "w") as f: json.dump(firebase_cred, f)
                try:
                    if not firebase_admin._apps: firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
                    db_firebase = firestore.client()
                    current_db_mode = "firebase"
                    waiting_for_firebase = False
                    
                    # 🌟 One-Time Sync: Firebase থেকে সব ইউজার ID লোকালে সেভ করা (লিমিট বাঁচাতে)
                    try:
                        local_users = set()
                        if os.path.exists(USERS_LIST_FILE):
                            with open(USERS_LIST_FILE, "r") as f:
                                local_users = set(json.load(f))
                        
                        # শুধুমাত্র ID গুলো আনা হচ্ছে, পুরো ডাটা নয় (এতে ব্যান্ডউইথ ও লিমিট বাঁচবে)
                        docs = db_firebase.collection('users').select([]).stream()
                        fb_users = set(int(doc.id) for doc in docs)
                        
                        combined_users = local_users.union(fb_users)
                        if len(combined_users) > len(local_users):
                            with open(USERS_LIST_FILE, "w") as f:
                                json.dump(list(combined_users), f)
                            print(f"✅ Synced {len(fb_users)} users from Firebase to Local List!")
                    except Exception as e:
                        print(f"User Sync Error: {e}")

                    # 🌟 Firebase এ সেটিংস চেক এবং সেভ/সিঙ্ক করার লজিক
                    try:
                        config_ref = db_firebase.collection('settings').document('bot_config')
                        doc = config_ref.get()
                        if not doc.exists:
                            config_data = {
                                "bot_settings": bot_settings,
                                "force_join_status": force_join_status,
                                "force_join_channels": force_join_channels,
                                "otp_forward_groups": otp_forward_groups,
                                "otp_button_link": otp_button_link,
                                "voltx_keys": voltx_keys,
                                "voltx_auto_mode": voltx_auto_mode
                            }
                            config_ref.set(config_data)
                        else:
                            data = doc.to_dict()
                            if "bot_settings" in data: bot_settings.update(data["bot_settings"])
                            if "force_join_status" in data: force_join_status = data["force_join_status"]
                            if "force_join_channels" in data: force_join_channels = data["force_join_channels"]
                            if "otp_forward_groups" in data: otp_forward_groups = data["otp_forward_groups"]
                            if "otp_button_link" in data: otp_button_link = data["otp_button_link"]
                            if "voltx_keys" in data: voltx_keys = data["voltx_keys"]
                            if "voltx_auto_mode" in data: voltx_auto_mode = data["voltx_auto_mode"]
                            save_local_data()
                    except Exception as e:
                        pass
                    
                    if target_msg_id: edit_message(chat_id, target_msg_id, "⏳ <b>Syncing SQLite data to Firebase... Please wait.</b>")
                    migrate_sqlite_to_firebase()
                    
                    if target_msg_id: edit_message(chat_id, target_msg_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
                    send_message(chat_id, "✅ <b>Firebase successfully connected & Synced!</b>")
                except Exception as e:
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"❌ <b>Failed to connect to Firebase:</b>\n<code>{html.escape(str(e))}</code>", reply_markup=get_back_only_keyboard())
            except Exception:
                if target_msg_id: edit_message(chat_id, target_msg_id, "⚠️ <b>Invalid JSON format. Please upload the .json file directly.</b>", reply_markup=get_back_only_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif isinstance(state, str) and state.startswith("waiting_withdraw_amount_"):
            method = state[24:]
            user_data = get_user(user_id)
            bal = user_data.get("balance", 0)
            min_w = bot_settings.get("min_withdraw", 10.0)
            
            try:
                amount = float(text.strip())
                if amount < min_w:
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"❌ <b>Minimum withdraw is {min_w} BDT.</b>\nTry again:", reply_markup=get_back_only_keyboard())
                elif amount > bal:
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"❌ <b>Insufficient balance! You only have {bal:.2f} BDT.</b>\nTry again:", reply_markup=get_back_only_keyboard())
                else:
                    user_states[user_id] = {"state": f"waiting_withdraw_number_{method}_{amount}", "msg_id": target_msg_id}
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"✅ <b>Amount Set: {amount:.2f} BDT</b>\n\n💳 <b>Method:</b> {method}\n💬 <b>Now send your {method} account number:</b>", reply_markup=get_back_only_keyboard())
            except ValueError:
                if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Invalid amount. Send numbers only.</b>\nTry again:", reply_markup=get_back_only_keyboard())
            delete_message(chat_id, message_id)
            return

        elif isinstance(state, str) and state.startswith("waiting_withdraw_number_"):
            parts = state.split("_")
            method = parts[3]
            amount = float(parts[4])
            
            user_data = get_user(user_id)
            bal = user_data.get("balance", 0)
            
            if bal < amount:
                if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Insufficient balance!</b>", reply_markup=get_main_keyboard(user_id))
            else:
                account_number = text.strip()
                update_user_stats(user_id, -amount, 0)
                
                w_group = bot_settings.get("w_group", "")
                if w_group:
                    w_msg = (
                        f"<tg-emoji emoji-id=\"5420396762189831222\">🆕</tg-emoji> <b>NEW WITHDRAW REQUEST</b>\n"
                        f"━━━━━━━━━━━━━━━━━\n"
                        f"<tg-emoji emoji-id=\"5352861489541714456\">👤</tg-emoji> <b>User:</b> <a href='tg://user?id={user_id}'>{html.escape(first_name)}</a>\n"
                        f"— — — — — — — — — —\n"
                        f"<tg-emoji emoji-id=\"5226929552319594190\">🆔</tg-emoji> <b>ID:</b> <code>{user_id}</code>\n"
                        f"— — — — — — — — — —\n"
                        f"<tg-emoji emoji-id=\"5429612421977253466\">💵</tg-emoji> <b>Amount:</b> <b>{amount:.2f} BDT</b>\n"
                        f"— — — — — — — — — —\n"
                        f"<tg-emoji emoji-id=\"5190899075968441286\">💳</tg-emoji> <b>Method:</b> {method}\n"
                        f"— — — — — — — — — —\n"
                        f"<tg-emoji emoji-id=\"5337132498965010628\">📞</tg-emoji> <b>Number:</b> <code>{account_number}</code>\n"
                        f"━━━━━━━━━━━━━━━━━"
                    )
                    
                    w_markup = {
                        "inline_keyboard": [
                            [
                                {"text": "APPROVE", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"admin_w_approve_{user_id}_{amount}_{account_number}", "style": "success"},
                                {"text": "REJECT", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"admin_w_reject_{user_id}_{amount}_{account_number}", "style": "danger"}
                            ]
                        ]
                    }
                    send_message(w_group, w_msg, reply_markup=w_markup)
                
                success_msg = (
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"<tg-emoji emoji-id=\"5429612421977253466\">💵</tg-emoji> <b>Amount:</b> {amount:.2f} BDT\n"
                    f"— — — — — — — — — —\n"
                    f"<tg-emoji emoji-id=\"5190899075968441286\">💳</tg-emoji> <b>Method:</b> {method}\n"
                    f"— — — — — — — — — —\n"
                    f"<tg-emoji emoji-id=\"5337132498965010628\">📞</tg-emoji> <b>Number:</b> <code>{account_number}</code>\n"
                    f"━━━━━━━━━━━━━━━━━"
                )
                if target_msg_id:
                    delete_message(chat_id, target_msg_id)
                send_message(chat_id, success_msg, reply_markup=get_main_keyboard(user_id))
                    
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_dxa_ref_r":
            try:
                bot_settings["refer_reward"] = float(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_dxa_min_w":
            try:
                bot_settings["min_withdraw"] = float(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_cool":
            try:
                bot_settings["cooldown"] = int(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_num_req":
            try:
                bot_settings["num_req"] = int(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_w_method":
            bot_settings["w_methods"].append(text.strip())
            save_local_data()
            if target_msg_id: edit_message(chat_id, target_msg_id, "💳 <b>WITHDRAW METHODS</b>\nManage methods below:", reply_markup=dxa_manage_w_methods_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_def_rate":
            try:
                bot_settings["otp_default_rate"] = float(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_srv_rate":
            try:
                parts = text.split("-")
                srv_name = parts[0].strip()
                srv_rate = float(parts[1].strip())
                bot_settings["otp_service_rates"][srv_name] = srv_rate
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
            except Exception:
                send_message(chat_id, "❌ Invalid format. Use: ServiceName - Rate (e.g. Telegram - 5.0)")
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_uc_id":
            try:
                target_uid = int(text.strip())
                target_data = get_user(target_uid)
                
                if target_data:
                    msg = (
                        f"<tg-emoji emoji-id=\"5352861489541714456\">👤</tg-emoji> <b>USER PROFILE</b>\n"
                        f"━━━━━━━━━━━━━━━━━\n"
                        f"<b>Name:</b> {html.escape(target_data['first_name'])}\n"
                        f"<b>ID:</b> <code>{target_uid}</code>\n"
                        f"<b>Balance:</b> {target_data['balance']:.2f} BDT\n"
                        f"<b>Total Invites:</b> {target_data['total_invites']}\n"
                        f"━━━━━━━━━━━━━━━━━"
                    )
                    if target_msg_id: edit_message(chat_id, target_msg_id, msg, reply_markup=get_user_profile_keyboard(target_uid))
                else:
                    if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>User not found in database!</b>", reply_markup=get_user_control_keyboard())
            except ValueError:
                if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Invalid User ID format!</b>", reply_markup=get_user_control_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif isinstance(state, str) and state.startswith("waiting_uc_balance_"):
            target_uid = int(state[19:])
            try:
                amount_to_add = float(text.strip())
                update_user_stats(target_uid, amount_to_add, 0)
                
                target_data = get_user(target_uid)
                msg = (
                    f"✅ <b>Balance Updated Successfully!</b>\n\n"
                    f"<tg-emoji emoji-id=\"5352861489541714456\">👤</tg-emoji> <b>Name:</b> {html.escape(target_data['first_name'])}\n"
                    f"<tg-emoji emoji-id=\"5429612421977253466\">💵</tg-emoji> <b>New Balance:</b> {target_data['balance']:.2f} BDT"
                )
                if target_msg_id: edit_message(chat_id, target_msg_id, msg, reply_markup=get_user_profile_keyboard(target_uid))
            except ValueError:
                if target_msg_id: edit_message(chat_id, target_msg_id, "❌ <b>Invalid amount format! Use numbers (e.g. 50 or -10).</b>", reply_markup=get_user_profile_keyboard(target_uid))
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

    if text in ["LIVE NUMBER", "LIVE TRAFFIC", "INVITE FRIEND", "WALLET", "LEADERBOARD", "OWNER PANEL"]:
        if user_id in user_states: del user_states[user_id]

    # 🌟 চেক করা হচ্ছে ইউজার আগে থেকেই ডাটাবেসে আছে কি না
    is_new_user = (get_user(user_id) is None)

    add_user(user_id, first_name)
    user_data = get_user(user_id)

    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1:
            param = parts[1]
            if param.startswith("alloc_"):
                try:
                    _, req_range, req_sid = param.split("_", 2)
                    
                    last_req = user_cooldowns.get(user_id, 0)
                    now = time.time()
                    if now - last_req < bot_settings.get("cooldown", 0):
                        send_message(chat_id, f"⌛ <b>Please wait {int(bot_settings['cooldown'] - (now - last_req))} seconds before requesting again.</b>")
                        return
                    user_cooldowns[user_id] = now
                    
                    # 🌟 মেসেজ পাঠিয়ে মেসেজ আইডি ক্যাচ করা
                    wait_msg = send_message(chat_id, f"⏳ <b>Fetching number for {req_sid.title().replace('_', ' ')}...</b>")
                    
                    msg, markup = get_number_allocation_content(req_sid, req_range, user_id=user_id)
                    
                    # 🌟 নতুন মেসেজ না দিয়ে আগেরটাতেই এডিট করা
                    if wait_msg and "result" in wait_msg:
                        edit_message(chat_id, wait_msg["result"]["message_id"], msg, reply_markup=markup)
                    else:
                        send_message(chat_id, msg, reply_markup=markup)
                    return
                except Exception:
                    pass
            else:
                try:
                    inviter_id = int(param)
                    # 🌟 শুধুমাত্র নতুন ইউজার হলেই রেফারেল কাউন্ট হবে!
                    if is_new_user and inviter_id != user_id and get_user(inviter_id):
                        ref_amount = bot_settings.get("refer_reward", 0.2)
                        update_user_stats(inviter_id, ref_amount, 1)
                        send_message(inviter_id, f"🎉 <b>New Referral!</b>\nSomeone joined using your link. You received {ref_amount} BDT.")
                except ValueError: pass
        send_message(chat_id, f"🔥 <b>PREMIUM NUMBER BOT </b>\n\nWelcome {html.escape(str(first_name))}, please select an option from the menu.", reply_markup=get_main_keyboard(user_id))
        
    elif text == "LIVE NUMBER":
        msg, markup = get_services_content()
        if markup:
            send_message(chat_id, msg, reply_markup=markup)
        else:
            send_message(chat_id, msg)
        
    elif text == "LIVE TRAFFIC":
        msg, markup = get_live_traffic_content()
        send_message(chat_id, msg, reply_markup=markup)
            
    elif text == "INVITE FRIEND":
        invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        ref_reward = bot_settings.get("refer_reward", 0.2)
        msg = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id=\"5420145051336485498\">👥</tg-emoji> <b>Referral Program</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id=\"5420517437885943844\">🔗</tg-emoji> <b>Your Invite Link:</b>\n"
            f"<code>{invite_link}</code>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5420396762189831222\">🎁</tg-emoji> <b>PER INVITE : {ref_reward} TK</b>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5353032893096567467\">📊</tg-emoji> <b>Total Invites:</b> {user_data['total_invites']}\n"
            f"━━━━━━━━━━━━━━━━━"
        )
        send_message(chat_id, msg, reply_markup={"inline_keyboard": [[{"text": "COPY LINK", "icon_custom_emoji_id": "5379889727325350343", "copy_text": {"text": invite_link}, "style": "success"}]]})
        
    elif text == "WALLET":
        wallet_txt = (
            f"<tg-emoji emoji-id=\"5429105001655999635\">💰</tg-emoji> <b>YOUR WALLET</b>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5352861489541714456\">👤</tg-emoji> <b>NAME :</b> {html.escape(str(first_name))}\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5226929552319594190\">🆔</tg-emoji> <b>ID :</b> <code>{user_id}</code>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5429612421977253466\">💵</tg-emoji> <b>BALANCE : {user_data['balance']:.2f} BDT</b>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5190899075968441286\">💳</tg-emoji> <b>WITHDRAWAL METHODS :</b>"
        )
        kb = {"inline_keyboard": []}
        for method in bot_settings.get("w_methods", []):
            kb["inline_keyboard"].append([{"text": method, "icon_custom_emoji_id": "5431783519355444455", "callback_data": f"user_withdraw_{method}", "style": "primary"}])
        send_message(chat_id, wallet_txt, reply_markup=kb)
        
    elif text == "LEADERBOARD":
        send_message(chat_id, get_leaderboard_text(), reply_markup=get_leaderboard_keyboard())

    elif text == "OWNER PANEL":
        if user_id == ADMIN_ID:
            send_message(chat_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        else:
            send_message(chat_id, "⚠️ <b>Access Denied!</b>\nThis menu is restricted to the admin.")

def handle_callback(callback_query):
    global user_states, voltx_auto_mode, current_db_mode, force_join_status, force_join_channels, voltx_keys, otp_forward_groups, bot_settings
    query_id = callback_query["id"]
    user_id = callback_query["from"]["id"]
    data = callback_query["data"]
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]

    if data == "check_fj_joined":
        if is_user_joined(user_id):
            delete_message(chat_id, message_id)
            send_message(chat_id, "✅ <b>Thank you for joining! You can now use the bot.</b>", reply_markup=get_main_keyboard(user_id))
        else:
            answer_callback_query(query_id, "❌ You haven't joined all channels!", show_alert=True)
        return

    if not is_user_joined(user_id):
        answer_callback_query(query_id, "Join channels first!", show_alert=True)
        return

    if data == "refresh_traffic":
        msg, markup = get_live_traffic_content()
        edit_message(chat_id, message_id, msg, reply_markup=markup)
        answer_callback_query(query_id, "Traffic Refreshed!")
        return

    if data == "back_to_services":
        msg, markup = get_services_content()
        edit_message(chat_id, message_id, msg, reply_markup=markup)
        answer_callback_query(query_id)
        return

    if data.startswith("srv_"):
        sid_short = data[4:]
        msg, markup, err = get_countries_content(sid_short)
        if err: answer_callback_query(query_id, err, show_alert=True)
        else:
            edit_message(chat_id, message_id, msg, reply_markup=markup)
            answer_callback_query(query_id)
        return

    if data.startswith("cc_"):
        parts = data.split("_")
        sid_short = parts[1]
        c_code = parts[2]
        
        last_req = user_cooldowns.get(user_id, 0)
        now = time.time()
        if now - last_req < bot_settings.get("cooldown", 0):
            answer_callback_query(query_id, f"Please wait {int(bot_settings['cooldown'] - (now - last_req))} seconds.", show_alert=True)
            return
        user_cooldowns[user_id] = now
        
        answer_callback_query(query_id, "Allocating number...")
        edit_message(chat_id, message_id, f"⏳ <b>Fetching best top range and allocating number...</b>")
        
        msg, markup = get_number_allocation_content(sid_short, c_code, user_id=user_id)
        
        edit_message(chat_id, message_id, msg, reply_markup=markup)
        return

    if data == "refresh_leaderboard":
        edit_message(chat_id, message_id, get_leaderboard_text(), reply_markup=get_leaderboard_keyboard())
        answer_callback_query(query_id, "Leaderboard Refreshed!")
        return

    # Admin Operations Only
    if user_id != ADMIN_ID:
        answer_callback_query(query_id, "Access Denied!", show_alert=True)
        return
        
    if data.startswith("admin_w_approve_") or data.startswith("admin_w_reject_"):
        if user_id != ADMIN_ID:
            answer_callback_query(query_id, "⚠️ Access Denied! You cannot perform this action.", show_alert=True)
            return

        parts = data.split("_")
        action = parts[2]
        req_user_id = int(parts[3])
        amount = float(parts[4])
        acc_number = parts[5]
        
        masked_number = f"{acc_number[:3]}DXA{acc_number[-3:]}" if len(acc_number) >= 6 else acc_number
        
        msg_text = callback_query.get("message", {}).get("text", "")
        fname_match = re.search(r"User:\s*(.+)", msg_text)
        req_first_name = fname_match.group(1) if fname_match else "User"
        method_match = re.search(r"Method:\s*(.+)", msg_text)
        req_method = method_match.group(1) if method_match else "Unknown"
        
        if action == "approve":
            btn_text = "APPROVED BY ADMIN"
            btn_style = "success"
            btn_icon = "5352694861990501856"
            send_message(req_user_id, f"<tg-emoji emoji-id=\"5420396762189831222\">🎉</tg-emoji> <b>Withdrawal Approved!</b>\nYour request of {amount:.2f} BDT has been sent to <code>{masked_number}</code>.")
        else:
            btn_text = "REJECTED BY ADMIN"
            btn_style = "danger"
            btn_icon = "5420130255174145507"
            update_user_stats(req_user_id, amount, 0)
            send_message(req_user_id, f"<tg-emoji emoji-id=\"5336944168944047463\">⚠️</tg-emoji> <b>Withdrawal Rejected!</b>\nYour request of {amount:.2f} BDT to <code>{masked_number}</code> was rejected and refunded.")
            
        updated_msg = (
            f"<tg-emoji emoji-id=\"5420396762189831222\">🆕</tg-emoji> <b>WITHDRAW REQUEST PROCESSED</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id=\"5352861489541714456\">👤</tg-emoji> <b>User:</b> <a href='tg://user?id={req_user_id}'>{html.escape(req_first_name)}</a>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5226929552319594190\">🆔</tg-emoji> <b>ID:</b> <code>{req_user_id}</code>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5429612421977253466\">💵</tg-emoji> <b>Amount:</b> <b>{amount:.2f} BDT</b>\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5190899075968441286\">💳</tg-emoji> <b>Method:</b> {req_method}\n"
            f"— — — — — — — — — —\n"
            f"<tg-emoji emoji-id=\"5431783519355444455\">📞</tg-emoji> <b>Number:</b> <code>{masked_number}</code>\n"
            f"━━━━━━━━━━━━━━━━━"
        )
        
        updated_markup = {
            "inline_keyboard": [
                [{"text": btn_text, "icon_custom_emoji_id": btn_icon, "callback_data": "ignore_action", "style": btn_style}]
            ]
        }
        
        edit_message(chat_id, message_id, updated_msg, reply_markup=updated_markup)
        answer_callback_query(query_id, f"Request {action.title()}d!")
        return

    # ===== Voltx Key Manager =====
    if data == "manage_voltx":
        edit_message(chat_id, message_id, "🔑 <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
        answer_callback_query(query_id)
    elif data == "toggle_vk":
        voltx_auto_mode = not voltx_auto_mode
        save_local_data()
        edit_message(chat_id, message_id, "🔑 <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
        answer_callback_query(query_id, f"Voltx Mode: {'ON' if voltx_auto_mode else 'OFF'}")
    elif data == "add_vk":
        user_states[user_id] = {"state": "waiting_vk_key", "msg_id": message_id}
        edit_message(chat_id, message_id, "🔑 <b>Please reply to this message with the new Voltx API Key.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data.startswith("del_vk_"):
        idx = int(data[7:])
        if idx < len(voltx_keys): 
            if len(voltx_keys) > 1:
                voltx_keys.pop(idx)
                save_local_data()
                edit_message(chat_id, message_id, "🔑 <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
                answer_callback_query(query_id, "Key Deleted!")
            else:
                answer_callback_query(query_id, "Cannot delete the only key!", show_alert=True)

    # ===== Force Join Manager =====
    elif data == "manage_fj":
        edit_message(chat_id, message_id, "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
        answer_callback_query(query_id)
    elif data == "toggle_fj":
        force_join_status = not force_join_status
        save_local_data()
        edit_message(chat_id, message_id, "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
        answer_callback_query(query_id, f"Force Join: {'ON' if force_join_status else 'OFF'}")
    elif data == "add_fj":
        user_states[user_id] = {"state": "waiting_fj_channel", "msg_id": message_id}
        select_kb = {"keyboard": [[{"text": "Select Force Join Channel", "request_chat": {"request_id": 3, "chat_is_channel": True}}], [{"text": "🔙 BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "👇 <b>Select Channel from below:</b>\n<i>(Make sure bot is an admin there)</i>", reply_markup=select_kb)
        answer_callback_query(query_id)
    elif data.startswith("del_fj_"):
        idx = int(data[7:])
        if idx < len(force_join_channels): force_join_channels.pop(idx)
        save_local_data()
        edit_message(chat_id, message_id, "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
        answer_callback_query(query_id, "Channel Deleted!")

    # ===== OTP Group Manager =====
    elif data == "manage_otp_group":
        edit_message(chat_id, message_id, "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
        answer_callback_query(query_id)
    elif data == "add_otp_group":
        user_states[user_id] = {"state": "waiting_otp_group", "msg_id": message_id}
        select_kb = {"keyboard": [[{"text": "Select OTP Group", "request_chat": {"request_id": 1, "chat_is_channel": False}}], [{"text": "🔙 BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "👇 <b>Select OTP Group from below:</b>", reply_markup=select_kb)
        answer_callback_query(query_id)
    elif data.startswith("del_otp_group_"):
        idx = int(data[14:])
        if idx < len(otp_forward_groups): otp_forward_groups.pop(idx)
        save_local_data()
        edit_message(chat_id, message_id, "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
        answer_callback_query(query_id, "Group Deleted!")
    elif data == "edit_otp_link":
        user_states[user_id] = {"state": "waiting_otp_link", "msg_id": message_id}
        edit_message(chat_id, message_id, "🔗 <b>Please send the new URL for the inline button attached to forwarded OTPs.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "edit_main_channel":
        user_states[user_id] = {"state": "waiting_main_channel_link", "msg_id": message_id}
        edit_message(chat_id, message_id, "🔗 <b>Please send the URL for the MAIN CHANNEL inline button.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)

    # ===== DXA Control Panel =====
    elif data == "dxa_control":
        edit_message(chat_id, message_id, "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_min_w":
        user_states[user_id] = {"state": "waiting_dxa_min_w", "msg_id": message_id}
        edit_message(chat_id, message_id, "💸 <b>Enter new Minimum Withdraw Amount (e.g. 50):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_ref_r":
        user_states[user_id] = {"state": "waiting_dxa_ref_r", "msg_id": message_id}
        edit_message(chat_id, message_id, "💸 <b>Enter new Referral Reward Amount (e.g. 5.0):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_otp_control":
        edit_message(chat_id, message_id, "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_def_rate":
        user_states[user_id] = {"state": "waiting_dxa_def_rate", "msg_id": message_id}
        edit_message(chat_id, message_id, "💰 <b>Enter new Default OTP Rate (e.g. 0.5):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        
    elif data.startswith("del_srv_rate_"):
        srv_name = data[13:]
        if srv_name in bot_settings["otp_service_rates"]:
            del bot_settings["otp_service_rates"][srv_name]
            save_local_data()
        edit_message(chat_id, message_id, "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
        answer_callback_query(query_id, f"Rate for {srv_name} deleted!")
    elif data == "dxa_srv_rate":
        user_states[user_id] = {"state": "waiting_dxa_srv_rate", "msg_id": message_id}
        edit_message(chat_id, message_id, "💰 <b>Enter Specific Service Rate.</b>\nFormat: <code>ServiceName - Rate</code>\nExample: <code>Telegram - 2.5</code>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_cool":
        user_states[user_id] = {"state": "waiting_dxa_cool", "msg_id": message_id}
        edit_message(chat_id, message_id, "⏳ <b>Enter new Cooldown time in seconds (e.g. 10):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_num_req":
        user_states[user_id] = {"state": "waiting_dxa_num_req", "msg_id": message_id}
        edit_message(chat_id, message_id, "📱 <b>Enter how many numbers a user gets per request (e.g. 3):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "manage_w_methods":
        edit_message(chat_id, message_id, "💳 <b>WITHDRAW METHODS</b>\nManage methods below:", reply_markup=dxa_manage_w_methods_keyboard())
        answer_callback_query(query_id)
    elif data == "add_w_method":
        user_states[user_id] = {"state": "waiting_w_method", "msg_id": message_id}
        edit_message(chat_id, message_id, "💳 <b>Enter new Withdraw Method Name (e.g. bKash):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data.startswith("del_w_method_"):
        idx = int(data[13:])
        if idx < len(bot_settings["w_methods"]): bot_settings["w_methods"].pop(idx)
        save_local_data()
        edit_message(chat_id, message_id, "💳 <b>WITHDRAW METHODS</b>\nManage methods below:", reply_markup=dxa_manage_w_methods_keyboard())
        answer_callback_query(query_id, "Method Deleted!")
    elif data == "dxa_w_group":
        user_states[user_id] = {"state": "waiting_dxa_w_group", "msg_id": message_id}
        select_kb = {"keyboard": [[{"text": "Select Withdraw Group", "request_chat": {"request_id": 2, "chat_is_channel": False}}], [{"text": "🔙 BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "👇 <b>Select Withdraw Group from below:</b>", reply_markup=select_kb)
        answer_callback_query(query_id)

    # ===== Broadcast System =====
    elif data == "broadcast_menu":
        user_states[user_id] = {"state": "waiting_broadcast", "msg_id": message_id}
        edit_message(chat_id, message_id, "📣 <b>BROADCAST SYSTEM</b>\n\nSend any text, photo, video, or audio message you want to broadcast to all users.", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)

    elif data == "upload_firebase":
        user_states[user_id] = {"state": "waiting_firebase", "msg_id": message_id}
        edit_message(chat_id, message_id, "🔥 <b>FIREBASE SETUP</b>\n\nPlease reply with the <b>entire JSON content</b> of your Firebase Service Account file.", reply_markup=get_upload_firebase_keyboard())
        answer_callback_query(query_id, "Send JSON Now")

    # ===== User Control =====
    elif data == "user_control":
        msg = f"👥 <b>USER CONTROL</b>\n━━━━━━━━━━━━━━━━━\n📊 <b>Total Users:</b> {get_total_users()}\n\n👇 Manage users below:"
        edit_message(chat_id, message_id, msg, reply_markup=get_user_control_keyboard())
        answer_callback_query(query_id)
        
    elif data == "uc_profile":
        user_states[user_id] = {"state": "waiting_uc_id", "msg_id": message_id}
        edit_message(chat_id, message_id, "🆔 <b>Send the Telegram User ID to view profile:</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        
    elif data.startswith("uc_balance_"):
        target_uid = int(data[11:])
        user_states[user_id] = {"state": f"waiting_uc_balance_{target_uid}", "msg_id": message_id}
        edit_message(chat_id, message_id, f"💵 <b>Send the amount to Add or Subtract.</b>\n<i>(Examples: To add use 50, to deduct use -10)</i>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        
    elif data == "back_to_admin":
        if user_id in user_states: del user_states[user_id]
        edit_message(chat_id, message_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        answer_callback_query(query_id)
        
    elif data == "db_status": 
        answer_callback_query(query_id, f"Current DB: {current_db_mode.upper()}", show_alert=True)
        
    elif data == "close_panel":
        answer_callback_query(query_id, "Closed")
        delete_message(chat_id, message_id)
        
    elif data.startswith("user_withdraw_"):
        method = data[14:]
        user_data = get_user(user_id)
        bal = user_data.get("balance", 0)
        min_w = bot_settings.get("min_withdraw", 10.0)
        
        if bal < min_w:
            answer_callback_query(query_id, f"❌ Minimum withdraw is {min_w} BDT. You have {bal:.2f} BDT.", show_alert=True)
            return
            
        user_states[user_id] = {"state": f"waiting_withdraw_amount_{method}", "msg_id": message_id}
        edit_message(chat_id, message_id, f"💳 <b>Withdraw via {method}</b>\n\n💵 Your Balance: {bal:.2f} BDT\n💬 <b>Enter the amount you want to withdraw:</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        return
        
    else:
        answer_callback_query(query_id, f"{data} clicked!", show_alert=True)

# ==========================================
# Main
# ==========================================
def main():
    global BOT_USERNAME
    
    load_local_data()
    init_sqlite()
    init_firebase_from_file()
    
    BOT_USERNAME = get_bot_info()
    set_bot_commands()
    
    threading.Thread(target=voltx_console_listener, daemon=True).start()
    threading.Thread(target=voltx_sms_listener, daemon=True).start()
    threading.Thread(target=auto_cache_menu_thread, daemon=True).start()
    
    print(f"Bot @{BOT_USERNAME} is running with Voltx, DXA Control & OTP Forwarding...")
    
    offset = None
    while True:
        try:
            url = BASE_URL + "getUpdates"
            res = requests.get(url, params={"timeout": 30, "offset": offset}).json()
            if res.get("ok"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update: 
                        threading.Thread(target=handle_message, args=(update["message"],)).start()
                    elif "callback_query" in update: 
                        threading.Thread(target=handle_callback, args=(update["callback_query"],)).start()
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    main()
