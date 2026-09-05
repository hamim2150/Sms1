539302539302import os
import json
import re
import random
import asyncio
import requests
import phonenumbers
from datetime import datetime
from phonenumbers import geocoder

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
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
# ⚠️ ওনার আইডি এবং আপডেট করা বটের টোকেন
BOT_TOKEN = "8919458173:AAFxKL0sE5xhVdQxRCf2aCLHwsHlOPICdTo"
OWNER_ID = 8360805978

# =======================
#    RESELLER API CONFIG
# =======================
API_DOMAIN = "https://numberserver.axmirhost.com"
API_KEY = "524d3752b84b3903489033815bd4ef2dec52e19e"

SMS_API_URLS = [
    f"{API_DOMAIN}/number/api?key={API_KEY}&type=sms"
]

NUMBER_API_URLS = [
    f"{API_DOMAIN}/number/api?key={API_KEY}&type=numbers"
]

# =======================
#    CONFIG STORAGE (Relative Path Rule)
# =======================
CONFIG_FILE = "config.json"
USERS_FILE = "users.json"

def load_config():
    """সার্ভারের নিয়ম অনুযায়ী রিলেティブ পাথে কনফিগ ফাইল রিড করে"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                defaults = {
                    "otp_channel_id": None,
                    "otp_channel_name": "Not Configured Yet",
                    "otp_channel_link": "https://t.me/Crypto_Zone_nexxt",
                    "official_channel_link": "https://t.me/Crypto_Zone_nexxt", # অফিশিয়াল চ্যানেলের নতুন কনফিগ
                    "force_channels": [],  # ফোর্স জয়েন চ্যানেলের তালিকা
                    "bot_username": "Not Configured Yet",
                    "refer_bonus": 10.0,
                    "withdraw_methods": ["BKash", "Nagad"],
                    "min_withdraw": 50.0,
                    "support_link": "https://t.me/junaidaliniz"
                }
                for key, val in defaults.items():
                    if key not in config:
                        config[key] = val
                return config
        except Exception as e:
            print(f"[ERROR] Failed to read config: {e}", flush=True)
    return {
        "otp_channel_id": None,
        "otp_channel_name": "Not Configured Yet",
        "otp_channel_link": "https://t.me/Crypto_Zone_nexxt",
        "official_channel_link": "https://t.me/Crypto_Zone_nexxt",
        "force_channels": [],
        "bot_username": "Not Configured Yet",
        "refer_bonus": 10.0,
        "withdraw_methods": ["BKash", "Nagad"],
        "min_withdraw": 50.0,
        "support_link": "https://t.me/junaidaliniz"
    }

def save_config(config_data):
    """সার্ভারের নিয়ম অনুযায়ী রিলেティブ পাথে কনফিগ ফাইল সেভ করে"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f)
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}", flush=True)


def load_users():
    """ব্যবহারকারীদের ব্যালেন্স ও রেফার ট্র্যাক করার জন্য ফাইল রিড করে"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read users: {e}", flush=True)
    return {}

def save_users(users_data):
    """ব্যবহারকারীদের ব্যালেন্স ও রেফার ডাটা সেভ করে"""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users_data, f)
    except Exception as e:
        print(f"[ERROR] Failed to save users: {e}", flush=True)


# =======================
#    LANGUAGE LOCALIZATION
# =======================
LANG_STRINGS = {
    "en": {
        "welcome": "Welcome {name}! Choose your options below.",
        "choose_lang": "Please select your preferred language:",
        "force_join": "⚠️ <b>You must join our required channels to use this bot!</b>\n\nJoin all channels below and click 'Verify'.",
        "verify_btn": "🟩 Verify Join",
        "verified_success": "✅ Verification successful! You can now use the bot.",
        "verified_failed": "❌ Verification failed. Please make sure you have joined all the required channels.",
        "menu_my_account": "🔴 My Account",
        "menu_refer": "🟢 Refer",
        "menu_withdraw": "🔵 Withdraw",
        "menu_support": "👑 Support",
        "menu_language": "🟠 Language",
        "menu_get_number": "🟡 Get Number",
        "account_info": "👤 <b>My Account Info</b>\n\n🆔 Telegram ID: <code>{user_id}</code>\n🏷 Name: {name}\n🌐 Username: @{username}\n💰 <b>Balance: {balance} BDT</b>\n\nEnjoy our services!",
        "refer_info": "👥 <b>Referral Program</b>\n\n🎁 Refer Bonus: <b>{bonus} BDT</b> per active refer.\n🔗 Your Referral Link:\n<code>{link}</code>\n\n⚠️ Note: Referrals must join our force-join channels for you to get the bonus!",
        "my_refer_btn": "📊 My Refer",
        "top_refer_btn": "🏆 Top Refer",
        "my_refer_info": "📊 <b>Your Referral Stats</b>\n\n👥 Total Refers: {count}\n\nHere is your refer list:\n{list}",
        "top_refer_info": "🏆 <b>Top 5 Referrers</b>\n\n{list}",
        "withdraw_info": "💳 <b>Withdraw Funds</b>\n\n💰 Current Balance: {balance} BDT\n📉 Minimum Withdraw: {min_withdraw} BDT\n🏦 Methods: {methods}\n\nSelect a method below to withdraw:",
        "withdraw_enter_details": "Please send your {method} account number:",
        "withdraw_enter_amount": "Please enter the amount to withdraw\n(Min: {min_withdraw} BDT, Max: {balance} BDT):",
        "withdraw_success": "✅ Withdrawal request of {amount} BDT to {method} ({number}) has been sent to admin for approval!",
        "withdraw_insufficient": "❌ Insufficient balance. You need at least {min_withdraw} BDT.",
        "invalid_amount": "❌ Invalid amount. Please try again.",
        "support_info": "📞 <b>Support Center</b>\n\nIf you face any issues, contact our support team here:\n🌐 Support: {link}",
        "lang_changed": "✅ Language changed to English!",
        "select_service": "📱 <b>Select Service</b>\n\nPlease select the service you want a virtual number for:",
        "generated_num_service": "{flag} <b>Your Virtual Number for {service}</b>\n\n<blockquote>🌍 Country: {country}</blockquote>\n<blockquote>📞 Number: <code>{number}</code> (Tap to copy)</blockquote>\n\n🔥 Use it quickly before others get it!",
        "back_to_services": "⬅️ Back to Services",
        "join_otp_btn": "📢 Join OTP Channel"
    },
    "bn": {
        "welcome": "স্বাগতম {name}! নিচের অপশনগুলো থেকে আপনার প্রয়োজনীয়টি বেছে নিন।",
        "choose_lang": "অনুগ্রহ করে আপনার পছন্দের ভাষা নির্বাচন করুন:",
        "force_join": "⚠️ <b>বটের সেবা ব্যবহার করতে আপনাকে অবশ্যই নিচের চ্যানেলগুলোতে জয়েন করতে হবে!</b>\n\nচ্যানেলগুলোতে জয়েন করার পর নিচের 'Verify' বাটনে ক্লিক করুন।",
        "verify_btn": "🟩 যাচাই করুন",
        "verified_success": "✅ যাচাইকরণ সফল হয়েছে! আপনি এখন বট ব্যবহার করতে পারবেন।",
        "verified_failed": "❌ যাচাইকরণ ব্যর্থ হয়েছে। অনুগ্রহ করে নিশ্চিত করুন যে আপনি সবগুলো চ্যানেলে জয়েন করেছেন।",
        "menu_my_account": "🔴 আমার অ্যাকাউন্ট",
        "menu_refer": "🟢 রেফার করুন",
        "menu_withdraw": "🔵 উইথড্র",
        "menu_support": "👑 সাপোর্ট",
        "menu_language": "🟠 ভাষা পরিবর্তন",
        "menu_get_number": "🟡 নম্বর নিন",
        "account_info": "👤 <b>আমার অ্যাকাউন্টের তথ্য</b>\n\n🆔 টেলিগ্রাম আইডি: <code>{user_id}</code>\n🏷 নাম: {name}\n🌐 ইউজারনেম: @{username}\n💰 <b>ব্যালেন্স: {balance} BDT</b>\n\nআমাদের সেবাগুলো উপভোগ করুন!",
        "refer_info": "👥 <b>রেফারেল প্রোগ্রাম</b>\n\n🎁 রেফার বোনাস: প্রতি সক্রিয় রেফারে পাবেন <b>{bonus} BDT</b>।\n🔗 আপনার রেফারেল লিংক:\n<code>{link}</code>\n\n⚠️ দ্রষ্টব্য: বোনাস পেতে হলে আপনার রেফারকৃত ইউজারকে অবশ্যই আমাদের ফোর্স জয়েন চ্যানেলগুলোতে জয়েন করতে হবে!",
        "my_refer_btn": "📊 আমার রেফার",
        "top_refer_btn": "🏆 টপ রেফার",
        "my_refer_info": "📊 <b>আপনার রেফারেল পরিসংখ্যান</b>\n\n👥 মোট রেফার: {count}\n\nআপনার রেফারের তালিকা:\n{list}",
        "top_refer_info": "🏆 <b>সর্বোচ্চ ৫ জন রেফারার</b>\n\n{list}",
        "withdraw_info": "💳 <b>টাকা উত্তোলন</b>\n\n💰 বর্তমান ব্যালেন্স: {balance} BDT\n📉 সর্বনিম্ন উইথড্র: {min_withdraw} BDT\n🏦 মাধ্যমসমূহ: {methods}\n\nউইথড্র করার জন্য নিচের যেকোনো একটি মাধ্যম সিলেক্ট করুন:",
        "withdraw_enter_details": "অনুগ্রহ করে আপনার {method} অ্যাকাউন্ট নম্বরটি পাঠান:",
        "withdraw_enter_amount": "উইথড্রর পরিমাণ লিখুন\n(সর্বনিম্ন: {min_withdraw} BDT, সর্বোচ্চ: {balance} BDT):",
        "withdraw_success": "✅ {method} ({number}) অ্যাকাউন্টে {amount} BDT উইথড্রর অনুরোধ অ্যাডমিনের কাছে পাঠানো হয়েছে!",
        "withdraw_insufficient": "❌ অপর্যাপ্ত ব্যালেন্স। আপনার কমপক্ষে {min_withdraw} BDT প্রয়োজন।",
        "invalid_amount": "❌ ভুল বা অমান্য পরিমাণ। অনুগ্রহ করে আবার চেষ্টা করুন।",
        "support_info": "📞 <b>সহায়তা কেন্দ্র</b>\n\nযেকোনো সমস্যার জন্য আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন:\n🌐 সাপোর্ট লিংক: {link}",
        "lang_changed": "✅ ভাষা পরিবর্তন করে বাংলা করা হয়েছে!",
        "select_service": "📱 <b>সার্ভিস নির্বাচন করুন</b>\n\nআপনি কোন সার্ভিসের জন্য ভার্চুয়াল নম্বর নিতে চান তা সিলেক্ট করুন:",
        "generated_num_service": "{flag} <b>{service}-এর জন্য আপনার ভার্চুয়াল নম্বর</b>\n\n<blockquote>🌍 দেশ: {country}</blockquote>\n<blockquote>📞 নম্বর: <code>{number}</code> (কপি করতে আলতো চাপুন)</blockquote>\n\n🔥 অন্যদের আগে দ্রুত এটি ব্যবহার করুন!",
        "back_to_services": "⬅️ সার্ভিসে ফিরুন",
        "join_otp_btn": "📢 ওটিপি চ্যানেলে জয়েন করুন"
    },
    "hi": {
        "welcome": "आपका स्वागत है {name}! नीचे दिए गए विकल्पों में से अपना पसंदीदा विकल्प चुनें।",
        "choose_lang": "कृपया अपनी पसंदीदा भाषा चुनें:",
        "force_join": "⚠️ <b>बॉट का उपयोग करने के लिए आपको हमारे आवश्यक चैनलों से जुड़ना होगा!</b>\n\nनीचे दिए गए सभी चैनलों से जुड़ें और 'सत्यापित करें' बटन पर क्लिक करें।",
        "verify_btn": "🟩 सत्यापित करें",
        "verified_success": "✅ सत्यापन सफल रहा! अब आप बॉट का उपयोग कर सकते हैं।",
        "verified_failed": "❌ सत्यापन विफल रहा। कृपया सुनिश्चित करें कि आप सभी आवश्यक चैनलों से जुड़े हैं।",
        "menu_my_account": "🔴 मेरा खाता",
        "menu_refer": "🟢 रेफ़र करें",
        "menu_withdraw": "🔵 निकास (Withdraw)",
        "menu_support": "👑 सहायता (Support)",
        "menu_language": "🟠 भाषा बदलें",
        "menu_get_number": "🟡 नंबर प्राप्त करें",
        "account_info": "👤 <b>मेरे खाते की जानकारी</b>\n\n🆔 टेलीग्राम आईडी: <code>{user_id}</code>\n🏷 नाम: {name}\n🌐 उपयोगकर्ता नाम: @{username}\n💰 <b>शेष राशि: {balance} BDT</b>\n\nहमारी सेवाओं का आनंद लें!",
        "refer_info": "👥 <b>रेफ़रल प्रोग्राम</b>\n\n🎁 रेफ़र बोनस: प्रत्येक सक्रिय रेफ़र पर आपको <b>{bonus} BDT</b> मिलेगा।\n🔗 आपका रेफ़रल लिंक:\n<code>{link}</code>\n\n⚠️ ध्यान दें: बोनस प्राप्त करने के लिए आपके रेफ़र किए गए यूज़र को हमारे आवश्यक चैनलों से जुड़ना होगा!",
        "my_refer_btn": "📊 मेरे रेफ़र",
        "top_refer_btn": "🏆 शीर्ष रेफ़रर",
        "my_refer_info": "📊 <b>आपके रेफ़रल आंकड़े</b>\n\n👥 कुल रेफ़र: {count}\n\nआपकी रेफ़र सूची:\n{list}",
        "top_refer_info": "🏆 <b>शीर्ष 5 रेफ़रर</b>\n\n{list}",
        "withdraw_info": "💳 <b>धन निकासी (Withdraw)</b>\n\n💰 वर्तमान शेष राशि: {balance} BDT\n📉 न्यूनतम निकासी: {min_withdraw} BDT\n🏦 उपलब्ध माध्यम: {methods}\n\nनिकासी के लिए नीचे से कोई एक माध्यम चुनें:",
        "withdraw_enter_details": "कृपया अपना {method} खाता नंबर भेजें:",
        "withdraw_enter_amount": "कृपया निकासी राशि दर्ज करें\n(न्यूनतम: {min_withdraw} BDT, अधिकतम: {balance} BDT):",
        "withdraw_success": "✅ {method} ({number}) खाते में {amount} BDT की निकासी का अनुरोध एडमिन को भेज दिया गया है!",
        "withdraw_insufficient": "❌ अपर्याप्त शेष राशि। आपको कम से कम {min_withdraw} BDT की आवश्यकता है।",
        "invalid_amount": "❌ अमान्य राशि। कृपया पुनः प्रयास करें।",
        "support_info": "📞 <b>सहायता केंद्र</b>\n\nयदि आपको कोई समस्या आती है, तो हमारे सपोर्ट टीम से संपर्क करें:\n🌐 सपोर्ट लिंक: {link}",
        "lang_changed": "✅ भाषा बदलकर हिंदी कर दी गई है!",
        "select_service": "📱 <b>सेवा चुनें</b>\n\nकृपया वह सेवा चुनें जिसके लिए आप वर्चुअल नंबर चाहते हैं:",
        "generated_num_service": "{flag} <b>{service} के लिए आपका वर्चुअल नंबर</b>\n\n<blockquote>🌍 देश: {country}</blockquote>\n<blockquote>📞 नंबर: <code>{number}</code> (कॉपी करने के लिए टैप करें)</blockquote>\n\n🔥 दूसरों से पहले इसका तुरंत उपयोग करें!",
        "back_to_services": "⬅️ सेवाओं पर वापस जाएं",
        "join_otp_btn": "📢 ओटीपी चैनल से जुड़ें"
    }
}

def get_menu_keyboard(lang):
    strings = LANG_STRINGS.get(lang, LANG_STRINGS["en"])
    keyboard = [
        [strings["menu_my_account"], strings["menu_get_number"]],
        [strings["menu_refer"], strings["menu_withdraw"]],
        [strings["menu_support"], strings["menu_language"]]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def get_unjoined_channels(bot, user_id):
    config = load_config()
    force_channels = config.get("force_channels", [])
    unjoined = []
    
    for chan in force_channels:
        chan_id = chan.get("id")
        if not chan_id:
            continue
        try:
            member = await bot.get_chat_member(chat_id=chan_id, user_id=user_id)
            if member.status not in ["member", "administrator", "creator", "restricted"]:
                unjoined.append(chan)
        except Exception as e:
            print(f"[CHECK FORCE JOIN ERROR] Channel {chan_id}: {e}", flush=True)
            unjoined.append(chan)
            
    return unjoined


async def send_force_join_message(update_or_query, context, lang, user_id):
    config = load_config()
    force_channels = config.get("force_channels", [])
    strings = LANG_STRINGS[lang]
    
    buttons = []
    for i, chan in enumerate(force_channels, 1):
        buttons.append(
            InlineKeyboardButton(
                text=f"🔵 {chan.get('title', f'Channel {i}')}", 
                url=chan.get("link", "https://t.me")
            )
        )
        
    grid = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    grid.append([InlineKeyboardButton(strings["verify_btn"], callback_data="verify_channel_join")])
    
    keyboard = InlineKeyboardMarkup(grid)
    text = strings["force_join"]
    
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update_or_query.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


# =======================
#    DATA PARSING FUNCTIONS (Dual-Mode)
# =======================

def fetch_latest_otp(api_url):
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            print(f"[API ERROR] SMS Status: {response.status_code} for {api_url}", flush=True)
            return None
        
        try:
            data = response.json()
        except ValueError:
            return None

        if isinstance(data, dict) and data.get("status") == "success" and "message" in data:
            return {
                "time": data.get("time"),
                "country": data.get("country"),
                "number": data.get("number"),
                "service": data.get("service"),
                "message": data.get("message"),
            }

        records = data.get("aaData", [])
        valid = [r for r in records if isinstance(r[0], str) and ":" in r[0]]
        if not valid:
            return None
        latest = valid[0]
        return {
            "time": latest[0],
            "country": latest[1],
            "number": latest[2],
            "service": latest[3],
            "message": latest[4],
        }
    except Exception as e:
        print(f"[API EXCEPTION] {api_url}: {e}", flush=True)
        return None


def fetch_latest_numbers(api_url):
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            print(f"[API ERROR] Number Status: {response.status_code} for {api_url}", flush=True)
            return []
        
        try:
            data = response.json()
        except ValueError:
            return []

        if isinstance(data, dict) and data.get("status") == "success" and "number" in data:
            return [{
                "number": data.get("number"),
                "country": data.get("country")
            }]

        records = data.get("aaData", [])
        parsed_numbers = []
        for row in records:
            number = None
            country = "Unknown"
            for item in row:
                if isinstance(item, str):
                    clean = re.sub(r'\D', '', item)
                    if 7 <= len(clean) <= 15 and clean.isdigit():
                        number = clean
                    elif len(item) > 2 and not item.isdigit() and item.lower() not in ["online", "offline", "active"]:
                        country = item
            if number:
                parsed_numbers.append({
                    "number": number,
                    "country": country
                })
        return parsed_numbers
    except Exception as e:
        print(f"[API EXCEPTION] Numbers from {api_url}: {e}", flush=True)
        return []


def extract_otp(message):
    for pat in [r'\d{3}-\d{3}', r'\d{6}', r'\d{4}']:
        match = re.search(pat, message)
        if match:
            return match.group(0)
    return "N/A"


def mask_number(number_str):
    """আপনার প্রেরিত স্ক্রিপ্টের রুল অনুযায়ী নম্বর মাস্কিং"""
    try:
        if not number_str.startswith("+"):
            number_str = f"+{number_str}"
        length = len(number_str)

        if length < 10:
            show_first = 4
            show_last = 2
        else:
            show_first = 5
            show_last = 4

        stars = '*' * (length - show_first - show_last)
        if len(stars) < 0:
            return number_str

        return f"{number_str[:show_first]}{stars}{number_str[-show_last:]}"
    except:
        return f"+{number_str}"


def get_country_info_from_number(number_str):
    try:
        if not number_str.startswith("+"):
            number_str = f"+{number_str}"
        parsed = phonenumbers.parse(number_str)
        country_name = geocoder.description_for_number(parsed, "en")
        region_code = phonenumbers.region_code_for_number(parsed)
        if region_code:
            base = 127462 - ord("A")
            flag = chr(base + ord(region_code[0])) + chr(base + ord(region_code[1]))
        else:
            flag = "🌍"
        return country_name or "Unknown", flag
    except:
        return "Unknown", "🌍"


def normalize_channel(input_str):
    input_str = input_str.strip()
    if "t.me/" in input_str:
        parts = input_str.split("t.me/")
        username = parts[-1].strip("/")
        if not username.startswith("@") and not username.startswith("-"):
            username = f"@{username}"
        return username
    elif not input_str.startswith("@") and not input_str.startswith("-"):
        return f"@{input_str}"
    return input_str


def parse_channel_input(text):
    text = text.strip()
    chan_id = None
    chan_link = None
    
    if "|" in text:
        parts = text.split("|")
        chan_id = parts[0].strip()
        chan_link = parts[1].strip()
    else:
        if "t.me/" in text:
            username = text.split("t.me/")[-1].strip().split("?")[0].strip("/")
            chan_id = f"@{username}"
            chan_link = text
        elif text.startswith("@"):
            chan_id = text
            chan_link = f"https://t.me/{text[1:]}"
        elif text.startswith("-100"):
            chan_id = text
            chan_link = None
        else:
            chan_id = f"@{text}"
            chan_link = f"https://t.me/{text}"
            
    return chan_id, chan_link


# =======================
#    MESSAGE FORMATTERS (নতুন blockquote ডিজাইন অনুযায়ী)
# =======================

def format_sms_message(record):
    raw = record["message"]
    otp = extract_otp(raw)
    msg = raw.replace("<", "&lt;").replace(">", "&gt;")

    country_name, flag = get_country_info_from_number(record["number"])
    formatted_number = mask_number(record["number"])

    service_icon = "📱"
    s = record["service"].lower()
    if "whatsapp" in s:
        service_icon = "🟢"
    elif "telegram" in s:
        service_icon = "🔵"
    elif "facebook" in s:
        service_icon = "📘"

    time_str = record.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    formatted_msg = f"""
<b>{flag} New {country_name} {record['service']} OTP!</b>

<blockquote>🕰 Time: {time_str}</blockquote>
<blockquote>{flag} Country: {country_name}</blockquote>
<blockquote>{service_icon} Service: {record['service']}</blockquote>
<blockquote>📞 Number: {formatted_number}</blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>

<blockquote>📩 Full Message:</blockquote>
<pre>{msg}</pre>

Powered by Mr Niz
"""
    return formatted_msg, otp


def format_new_number_message(number_data):
    country_name, flag = get_country_info_from_number(number_data["number"])
    raw_number = f"+{number_data['number']}" if not number_data['number'].startswith("+") else number_data['number']
    
    formatted_msg = f"""
<b>{flag} New {country_name} Virtual Number Added!</b>

<blockquote>🌍 Country: {country_name}</blockquote>
<blockquote>📞 Number: <code>{raw_number}</code> (Tap to copy)</blockquote>

<blockquote>🔥 Status: Active & Fresh</blockquote>

🔥 <i>Use this fresh number quickly before others get it!</i>

Powered by Mr Niz
"""
    return formatted_msg


# =======================
#   DYNAMIC BROADCASTER (কপি বাটন সম্পূর্ণ বাদ দেওয়া হয়েছে)
# =======================

async def send_to_configured_channel(bot, message):
    config = load_config()
    channel_id = config.get("otp_channel_id")
    if not channel_id:
        print(f"[{datetime.now()}] Configured OTP Send Channel not set. Skipping send.", flush=True)
        return
        
    official_link = config.get("official_channel_link", "https://t.me/Crypto_Zone_nexxt")
    bot_username = config.get("bot_username", "MyBot")
    
    # রো ১: [ 📱 Channel ] এবং [ 🤖 OTP Bot ] (কপি বাটন নেই)
    row1 = [
        InlineKeyboardButton(text="📱 Channel", url=official_link),
        InlineKeyboardButton(text="🤖 OTP Bot", url=f"https://t.me/{bot_username}")
    ]
    
    keyboard = InlineKeyboardMarkup([row1])

    try:
        await bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[BROADCAST ERROR] Failed to send to {channel_id}: {e}", flush=True)


# =======================
#     BOT HANDLERS
# =======================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id_str = str(user.id)
    users = load_users()

    if user_id_str not in users:
        users[user_id_str] = {
            "balance": 0.0,
            "lang": None,
            "referrer": None,
            "bonus_given": False,
            "refers": [],
            "name": user.first_name,
            "username": user.username if user.username else "None"
        }
        
        if context.args:
            ref_id = context.args[0]
            if ref_id.isdigit() and int(ref_id) != user.id:
                users[user_id_str]["referrer"] = int(ref_id)
        
        save_users(users)

    user_data = users[user_id_str]

    if not user_data.get("lang"):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇧🇩 বাংলা", callback_data="set_lang_bn"),
                InlineKeyboardButton("🇮🇳 हिंदी", callback_data="set_lang_hi")
            ]
        ])
        await update.message.reply_text(
            "Welcome! Please select your language:\nস্বাগতম! অনুগ্রহ করে ভাষা নির্বাচন করুন:\nस्वागत है! कृपया भाषा चुनें:",
            reply_markup=keyboard
        )
        return

    lang = user_data["lang"]

    unjoined = await get_unjoined_channels(context.bot, user.id)
    if unjoined:
        await send_force_join_message(update, context, lang, user.id)
        return

    strings = LANG_STRINGS[lang]
    welcome_text = strings["welcome"].format(name=user.first_name)
    await update.message.reply_text(welcome_text, reply_markup=get_menu_keyboard(lang))


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Access Denied. Only the owner can configure settings.")
        return
        
    config = load_config()
    otp_channel_name = config.get("otp_channel_name", "Not Set")
    official_channel_link = config.get("official_channel_link", "https://t.me/Crypto_Zone_nexxt")
    bot_username = config.get("bot_username", "Not Set")
    refer_bonus = config.get("refer_bonus", 10.0)
    min_withdraw = config.get("min_withdraw", 50.0)
    methods = ", ".join(config.get("withdraw_methods", []))
    support = config.get("support_link", "Not Set")
    force_count = len(config.get("force_channels", []))
    
    text = (
        f"⚙️ <b>Admin Configuration</b>\n\n"
        f"📡 OTP Send Channel: <code>{otp_channel_name}</code>\n"
        f"📢 Official Channel Link: <code>{official_channel_link}</code>\n"
        f"📢 Force Join Channels: <code>{force_count} channels</code>\n"
        f"🤖 Bot Username: @{bot_username}\n"
        f"💰 Refer Bonus: {refer_bonus} BDT\n"
        f"📉 Min Withdraw: {min_withdraw} BDT\n"
        f"🏦 Methods: {methods}\n"
        f"📞 Support: {support}\n"
    )
    # অ্যাডমিন প্যানেলে Office Channel সেট করার নতুন বাটন
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Set OTP Send Channel", callback_data="admin_set_otp_chan")],
        [InlineKeyboardButton("📢 Set Official Channel", callback_data="admin_set_official_chan")],
        [InlineKeyboardButton("📢 Manage Force Join", callback_data="admin_manage_force_chans")],
        [InlineKeyboardButton("👥 Set Refer Setting", callback_data="admin_set_refer")],
        [InlineKeyboardButton("💳 Set Withdraw Setting", callback_data="admin_set_withdraw")],
        [InlineKeyboardButton("📞 Set Support Link", callback_data="admin_set_support")]
    ])
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = update.message.text.strip()
    
    if context.user_data.get("admin_state") and user_id == OWNER_ID:
        await process_admin_input(update, context)
        return

    if context.user_data.get("withdraw_state"):
        await handle_withdraw_input(update, context)
        return

    users = load_users()
    if user_id_str not in users:
        await start_command(update, context)
        return

    user_data = users[user_id_str]
    lang = user_data.get("lang", "en")
    strings = LANG_STRINGS[lang]

    unjoined = await get_unjoined_channels(context.bot, user_id)
    if unjoined:
        await send_force_join_message(update, context, lang, user_id)
        return

    if text == strings["menu_my_account"]:
        balance = user_data.get("balance", 0.0)
        profile_text = strings["account_info"].format(
            user_id=user_id,
            name=update.effective_user.first_name,
            username=update.effective_user.username if update.effective_user.username else 'None',
            balance=balance
        )
        await update.message.reply_text(profile_text, parse_mode="HTML")
        
    elif text == strings["menu_refer"]:
        config = load_config()
        bot_username = config.get("bot_username", "Not Set")
        refer_bonus = config.get("refer_bonus", 10.0)
        link = f"https://t.me/{bot_username}?start={user_id}"
        
        refer_text = strings["refer_info"].format(bonus=refer_bonus, link=link)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(strings["my_refer_btn"], callback_data="my_refer_stats"),
                InlineKeyboardButton(strings["top_refer_btn"], callback_data="top_refer_stats")
            ]
        ])
        await update.message.reply_text(refer_text, reply_markup=keyboard, parse_mode="HTML")

    elif text == strings["menu_withdraw"]:
        config = load_config()
        min_withdraw = config.get("min_withdraw", 50.0)
        methods_list = config.get("withdraw_methods", ["BKash", "Nagad"])
        methods_str = ", ".join(methods_list)
        balance = user_data.get("balance", 0.0)
        
        withdraw_text = strings["withdraw_info"].format(
            balance=balance,
            min_withdraw=min_withdraw,
            methods=methods_str
        )
        
        buttons = []
        for method in methods_list:
            buttons.append(InlineKeyboardButton(method, callback_data=f"withdraw_select_{method}"))
        
        keyboard_buttons = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.message.reply_text(withdraw_text, reply_markup=keyboard, parse_mode="HTML")

    elif text == strings["menu_support"]:
        config = load_config()
        support_link = config.get("support_link", "Not Set")
        support_text = strings["support_info"].format(link=support_link)
        await update.message.reply_text(support_text, parse_mode="HTML")

    elif text == strings["menu_language"]:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="change_lang_en"),
                InlineKeyboardButton("🇧🇩 বাংলা", callback_data="change_lang_bn"),
                InlineKeyboardButton("🇮🇳 हिंदी", callback_data="change_lang_hi")
            ]
        ])
        await update.message.reply_text(strings["choose_lang"], reply_markup=keyboard)

    elif text == strings["menu_get_number"]:
        await send_active_number_card(update, context)


async def send_active_number_card(update: Update, context: ContextTypes.DEFAULT_TYPE, service: str = None, query=None):
    user_id = query.from_user.id if query else update.effective_user.id
    user_id_str = str(user_id)
    users = load_users()
    user_data = users.get(user_id_str, {})
    lang = user_data.get("lang", "en")
    strings = LANG_STRINGS[lang]

    if service is None:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 WhatsApp", callback_data="getnum_whatsapp"),
                InlineKeyboardButton("🔵 Telegram", callback_data="getnum_telegram")
            ],
            [
                InlineKeyboardButton("📘 Facebook", callback_data="getnum_facebook"),
                InlineKeyboardButton("📸 Instagram", callback_data="getnum_instagram")
            ]
        ])
        
        if query:
            try:
                await query.edit_message_text(strings["select_service"], parse_mode="HTML", reply_markup=keyboard)
            except Exception:
                pass
        else:
            await update.message.reply_text(strings["select_service"], parse_mode="HTML", reply_markup=keyboard)
        return

    loop = asyncio.get_running_loop()
    all_numbers = []
    for url in NUMBER_API_URLS:
        nums = await loop.run_in_executor(None, fetch_latest_numbers, url)
        all_numbers.extend(nums)
        
    if not all_numbers:
        msg = "❌ No active numbers found at the moment."
        if query:
            await query.message.reply_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    selected = random.choice(all_numbers)
    country_name, flag = get_country_info_from_number(selected["number"])
    raw_number = f"+{selected['number']}" if not selected['number'].startswith("+") else selected['number']

    text = strings["generated_num_service"].format(
        flag=flag,
        service=service,
        country=country_name,
        number=raw_number
    )
    
    config = load_config()
    official_link = config.get("official_channel_link", "https://t.me/Crypto_Zone_nexxt")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 New Number", callback_data=f"getnum_{service.lower()}"),
            InlineKeyboardButton(strings["back_to_services"], callback_data="get_new_number")
        ],
        [
            InlineKeyboardButton(strings["join_otp_btn"], url=official_link)
        ]
    ])

    if query:
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
        except Exception:
            pass
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def show_manage_force_channels(query, context):
    config = load_config()
    force_list = config.get("force_channels", [])
    
    if not force_list:
        text = "📋 <b>Manage Force Join Channels</b>\n\n⚠️ No channels are currently added to the required force-join list."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Force Channel", callback_data="admin_add_force_chan")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="admin_back_to_menu")]
        ])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
        return
        
    text = "📋 <b>Manage Force Join Channels</b>\n\nClick on ❌ to remove a channel from the required list:"
    keyboard_list = []
    for idx, chan in enumerate(force_list):
        keyboard_list.append([
            InlineKeyboardButton(text=f"📣 {chan['title']}", url=chan['link']),
            InlineKeyboardButton(text="❌ Remove", callback_data=f"remove_force_{idx}")
        ])
    keyboard_list.append([InlineKeyboardButton("➕ Add Force Channel", callback_data="admin_add_force_chan")])
    keyboard_list.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="admin_back_to_menu")])
    
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard_list))


async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id_str = str(query.from_user.id)
    users = load_users()
    
    if query.data == "get_new_number":
        await send_active_number_card(update, context, query=query)
        
    elif query.data in ["getnum_whatsapp", "getnum_telegram", "getnum_facebook", "getnum_instagram"]:
        service_map = {
            "getnum_whatsapp": "WhatsApp",
            "getnum_telegram": "Telegram",
            "getnum_facebook": "Facebook",
            "getnum_instagram": "Instagram"
        }
        selected_service = service_map[query.data]
        await send_active_number_card(update, context, service=selected_service, query=query)

    # ল্যাঙ্গুয়েজ সেট করার জন্য (স্টার্ট সময়)
    elif query.data.startswith("set_lang_"):
        lang_code = query.data.split("_")[-1]
        if user_id_str in users:
            users[user_id_str]["lang"] = lang_code
            save_users(users)
        
        strings = LANG_STRINGS[lang_code]
        await query.message.reply_text(strings["lang_changed"])
        
        unjoined = await get_unjoined_channels(context.bot, query.from_user.id)
        if not unjoined:
            await query.message.reply_text(strings["welcome"].format(name=query.from_user.first_name), reply_markup=get_menu_keyboard(lang_code))
        else:
            await send_force_join_message(query, context, lang_code, query.from_user.id)
            
        try:
            await query.message.delete()
        except:
            pass

    # ল্যাঙ্গুয়েজ পরিবর্তনের জন্য
    elif query.data.startswith("change_lang_"):
        lang_code = query.data.split("_")[-1]
        if user_id_str in users:
            users[user_id_str]["lang"] = lang_code
            save_users(users)
        
        strings = LANG_STRINGS[lang_code]
        await query.message.reply_text(strings["lang_changed"], reply_markup=get_menu_keyboard(lang_code))
        try:
            await query.message.delete()
        except:
            pass

    # ফোর্স জয়েন ভেরিফিকেশন বাটন
    elif query.data == "verify_channel_join":
        unjoined = await get_unjoined_channels(context.bot, query.from_user.id)
        user_data = users.get(user_id_str, {})
        lang = user_data.get("lang", "en")
        strings = LANG_STRINGS[lang]
        
        if not unjoined:
            if user_data.get("referrer") and not user_data.get("bonus_given"):
                referrer_id = str(user_data["referrer"])
                if referrer_id in users:
                    config = load_config()
                    bonus = config.get("refer_bonus", 10.0)
                    users[referrer_id]["balance"] += bonus
                    
                    users[referrer_id]["refers"].append({
                        "id": query.from_user.id,
                        "name": query.from_user.first_name
                    })
                    user_data["bonus_given"] = True
                    save_users(users)
                    
                    try:
                        ref_lang = users[referrer_id].get("lang", "en")
                        ref_notif_text = {
                            "en": f"🎁 <b>Referral Bonus Added!</b>\n\nYou received <b>{bonus} BDT</b> because {query.from_user.first_name} joined the channels.",
                            "bn": f"🎁 <b>রেফার বোনাস যুক্ত হয়েছে!</b>\n\nআপনি <b>{bonus} BDT</b> বোনাস পেয়েছেন কারণ {query.from_user.first_name} চ্যানেলগুলোতে জয়েন করেছেন।",
                            "hi": f"🎁 <b>रेफ़रल बोनस जोड़ा गया!</b>\n\nआपको <b>{bonus} BDT</b> मिला क्योंकि {query.from_user.first_name} चैनलों से जुड़े हैं।"
                        }
                        await context.bot.send_message(
                            chat_id=int(referrer_id),
                            text=ref_notif_text.get(ref_lang, ref_notif_text["en"]),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"[REFER NOTIFICATION ERROR] {e}", flush=True)

            await query.message.reply_text(strings["verified_success"], reply_markup=get_menu_keyboard(lang))
            try:
                await query.message.delete()
            except:
                pass
        else:
            await query.message.reply_text(strings["verified_failed"])

    # রেফার তথ্য
    elif query.data == "my_refer_stats":
        user_data = users.get(user_id_str, {})
        lang = user_data.get("lang", "en")
        strings = LANG_STRINGS[lang]
        
        refers_list = user_data.get("refers", [])
        formatted_list = []
        for idx, ref in enumerate(refers_list, 1):
            if isinstance(ref, dict):
                formatted_list.append(f"{idx}. {ref.get('name', 'User')} (ID: {ref.get('id')})")
            else:
                formatted_list.append(f"{idx}. ID: {ref}")
        list_str = "\n".join(formatted_list) if formatted_list else "No refers yet."
        
        text = strings["my_refer_info"].format(count=len(refers_list), list=list_str)
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "top_refer_stats":
        user_data = users.get(user_id_str, {})
        lang = user_data.get("lang", "en")
        strings = LANG_STRINGS[lang]
        
        sorted_users = sorted(
            users.items(),
            key=lambda item: len(item[1].get("refers", [])),
            reverse=True
        )
        top_list = []
        for i, (uid, udata) in enumerate(sorted_users[:5], 1):
            name = udata.get("name", "User")
            ref_count = len(udata.get("refers", []))
            top_list.append(f"{i}. {name} - {ref_count} refers")
        list_str = "\n".join(top_list) if top_list else "No referrers yet."
        
        text = strings["top_refer_info"].format(list=list_str)
        await query.message.reply_text(text, parse_mode="HTML")

    # উইথড্র প্রসেসিং মেথড চয়েস
    elif query.data.startswith("withdraw_select_"):
        method = query.data.split("_")[-1]
        user_data = users.get(user_id_str, {})
        lang = user_data.get("lang", "en")
        strings = LANG_STRINGS[lang]
        
        context.user_data["withdraw_method"] = method
        context.user_data["withdraw_state"] = "waiting_for_number"
        
        await query.message.reply_text(strings["withdraw_enter_details"].format(method=method))
        try:
            await query.message.delete()
        except:
            pass

    # অ্যাডমিন প্যানেল নেভিগেশন ও কনফিগারেশন
    elif query.data == "admin_manage_force_chans":
        await show_manage_force_channels(query, context)
        
    elif query.data.startswith("remove_force_"):
        idx = int(query.data.split("_")[-1])
        config = load_config()
        force_list = config.get("force_channels", [])
        if 0 <= idx < len(force_list):
            removed = force_list.pop(idx)
            config["force_channels"] = force_list
            save_config(config)
            await query.answer(f"❌ Removed: {removed['title']}", show_alert=True)
            await show_manage_force_channels(query, context)
        else:
            await query.answer("❌ Invalid Index")
            
    elif query.data == "admin_back_to_menu":
        config = load_config()
        otp_channel_name = config.get("otp_channel_name", "Not Set")
        official_channel_link = config.get("official_channel_link", "https://t.me/Crypto_Zone_nexxt")
        bot_username = config.get("bot_username", "Not Set")
        refer_bonus = config.get("refer_bonus", 10.0)
        min_withdraw = config.get("min_withdraw", 50.0)
        methods = ", ".join(config.get("withdraw_methods", []))
        support = config.get("support_link", "Not Set")
        force_count = len(config.get("force_channels", []))
        
        text = (
            f"⚙️ <b>Admin Configuration</b>\n\n"
            f"📡 OTP Send Channel: <code>{otp_channel_name}</code>\n"
            f"📢 Official Channel Link: <code>{official_channel_link}</code>\n"
            f"📢 Force Join Channels: <code>{force_count} channels</code>\n"
            f"🤖 Bot Username: @{bot_username}\n"
            f"💰 Refer Bonus: {refer_bonus} BDT\n"
            f"📉 Min Withdraw: {min_withdraw} BDT\n"
            f"🏦 Methods: {methods}\n"
            f"📞 Support: {support}\n"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📡 Set OTP Send Channel", callback_data="admin_set_otp_chan")],
            [InlineKeyboardButton("📢 Set Official Channel", callback_data="admin_set_official_chan")],
            [InlineKeyboardButton("📢 Manage Force Join", callback_data="admin_manage_force_chans")],
            [InlineKeyboardButton("👥 Set Refer Setting", callback_data="admin_set_refer")],
            [InlineKeyboardButton("💳 Set Withdraw Setting", callback_data="admin_set_withdraw")],
            [InlineKeyboardButton("📞 Set Support Link", callback_data="admin_set_support")]
        ])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif query.data == "admin_set_otp_chan":
        if query.from_user.id != OWNER_ID:
            return
        context.user_data["admin_state"] = "waiting_for_otp_channel"
        await query.message.reply_text(
            "💬 Please send the OTP Channel ID/Username or Link.\n\n"
            "Example: <code>@Crypto_Zone_nexxt</code> or <code>https://t.me/Crypto_Zone_nexxt</code>",
            parse_mode="HTML"
        )

    elif query.data == "admin_set_official_chan":
        if query.from_user.id != OWNER_ID:
            return
        context.user_data["admin_state"] = "waiting_for_official_channel"
        await query.message.reply_text(
            "💬 Please send the invite link of your Official Channel.\n\n"
            "Example: <code>https://t.me/Crypto_Zone_nexxt</code>",
            parse_mode="HTML"
        )

    elif query.data == "admin_add_force_chan":
        if query.from_user.id != OWNER_ID:
            return
        context.user_data["admin_state"] = "waiting_for_add_force"
        await query.message.reply_text(
            "💬 Please send the Force Join Channel ID/Username or Link.\n\n"
            "Example: <code>@myforcejoinchannel</code> or <code>https://t.me/myforcejoinchannel</code>",
            parse_mode="HTML"
        )

    elif query.data == "admin_set_refer":
        if query.from_user.id != OWNER_ID:
            return
        context.user_data["admin_state"] = "waiting_for_refer"
        await query.message.reply_text(
            "💬 Please send the Refer Bonus and Bot Username separated by a bar (|).\n\n"
            "Example: <code>15 | MyBotUsername</code> (do not write @)",
            parse_mode="HTML"
        )
        
    elif query.data == "admin_set_withdraw":
        if query.from_user.id != OWNER_ID:
            return
        context.user_data["admin_state"] = "waiting_for_withdraw"
        await query.message.reply_text(
            "💬 Please send the Withdraw Methods (comma separated) and Minimum Withdraw separated by a bar (|).\n\n"
            "Example: <code>BKash, Nagad, Rocket | 50</code>",
            parse_mode="HTML"
        )
        
    elif query.data == "admin_set_support":
        if query.from_user.id != OWNER_ID:
            return
        context.user_data["admin_state"] = "waiting_for_support"
        await query.message.reply_text(
            "💬 Please send the Support Link or Telegram Username.\n\n"
            "Example: <code>https://t.me/junaidaliniz</code>",
            parse_mode="HTML"
        )


async def handle_withdraw_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = update.message.text.strip()
    users = load_users()
    user_data = users.get(user_id_str, {})
    lang = user_data.get("lang", "en")
    strings = LANG_STRINGS[lang]
    
    state = context.user_data.get("withdraw_state")
    method = context.user_data.get("withdraw_method")
    
    if state == "waiting_for_number":
        context.user_data["withdraw_number"] = text
        context.user_data["withdraw_state"] = "waiting_for_amount"
        
        config = load_config()
        min_withdraw = config.get("min_withdraw", 50.0)
        balance = user_data.get("balance", 0.0)
        
        await update.message.reply_text(
            strings["withdraw_enter_amount"].format(min_withdraw=min_withdraw, balance=balance)
        )
        
    elif state == "waiting_for_amount":
        try:
            amount = float(text)
            config = load_config()
            min_withdraw = config.get("min_withdraw", 50.0)
            balance = user_data.get("balance", 0.0)
            
            if amount < min_withdraw:
                await update.message.reply_text(strings["invalid_amount"])
                context.user_data["withdraw_state"] = None
                return
                
            if amount > balance:
                await update.message.reply_text(strings["withdraw_insufficient"].format(min_withdraw=min_withdraw))
                context.user_data["withdraw_state"] = None
                return
            
            user_data["balance"] = balance - amount
            save_users(users)
            
            number = context.user_data.get("withdraw_number")
            
            withdraw_msg = (
                f"🚨 <b>New Withdrawal Request!</b>\n\n"
                f"👤 User: {update.effective_user.first_name} (ID: <code>{user_id}</code>)\n"
                f"🏦 Method: {method}\n"
                f"📞 Account Number: <code>{number}</code>\n"
                f"💰 Amount: {amount} BDT"
            )
            try:
                await context.bot.send_message(chat_id=OWNER_ID, text=withdraw_msg, parse_mode="HTML")
            except Exception as e:
                print(f"[WITHDRAW ADMIN ERROR] {e}", flush=True)
                
            await update.message.reply_text(
                strings["withdraw_success"].format(amount=amount, method=method, number=number),
                reply_markup=get_menu_keyboard(lang)
            )
            
            context.user_data["withdraw_state"] = None
            context.user_data["withdraw_method"] = None
            context.user_data["withdraw_number"] = None
        except ValueError:
            await update.message.reply_text(strings["invalid_amount"])
            context.user_data["withdraw_state"] = None


async def process_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return

    state = context.user_data.get("admin_state")
    text = update.message.text.strip()

    if state == "waiting_for_otp_channel":
        try:
            chan_id, chan_link = parse_channel_input(text)
            if not chan_id:
                raise ValueError("Could not resolve a valid Channel ID/Username.")

            await update.message.reply_text("⏳ Verifying bot permissions inside the channel...")
            chat = await context.bot.get_chat(chan_id)
            
            try:
                member = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
                is_admin = member.status in ["administrator", "creator"]
            except Exception:
                is_admin = False
            
            if is_admin:
                if not chan_link:
                    if chat.username:
                        chan_link = f"https://t.me/{chat.username}"
                    else:
                        chan_link = "https://t.me"

                config = load_config()
                config["otp_channel_id"] = chat.id
                config["otp_channel_name"] = chat.title or chan_id
                config["otp_channel_link"] = chan_link
                save_config(config)
                
                context.user_data["admin_state"] = None
                await update.message.reply_text(
                    f"✅ <b>OTP Send Channel Saved!</b>\n\n"
                    f"📡 Name: <b>{chat.title}</b>\n"
                    f"🆔 ID: <code>{chat.id}</code>\n"
                    f"🔗 Link: {chan_link}\n\n"
                    f"👑 <b>Admin Check:</b> Bot is verified as an Administrator!",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Setup Failed!</b>\n\n"
                    f"The bot is NOT an Administrator inside <b>{chat.title}</b>.\n"
                    f"Please add the bot to that channel first, give it Admin status with posting rights, and try again.",
                    parse_mode="HTML"
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Failed to verify channel!</b>\n\n"
                f"Error: <code>{e}</code>\n\n"
                f"Please make sure:\n"
                f"1. You entered the correct link/username.\n"
                f"2. The bot is already added to that channel as an Admin.",
                parse_mode="HTML"
            )

    elif state == "waiting_for_official_channel":
        try:
            config = load_config()
            config["official_channel_link"] = text
            save_config(config)
            
            context.user_data["admin_state"] = None
            await update.message.reply_text(
                f"✅ <b>Official Channel Invite Link Saved!</b>\n\n"
                f"🔗 Link: <code>{text}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to save link. Error: {e}")

    elif state == "waiting_for_add_force":
        try:
            chan_id, chan_link = parse_channel_input(text)
            if not chan_id:
                raise ValueError("Could not resolve a valid Channel ID/Username.")

            await update.message.reply_text("⏳ Verifying bot permissions inside the channel...")
            chat = await context.bot.get_chat(chan_id)
            
            try:
                member = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
                is_admin = member.status in ["administrator", "creator"]
            except Exception:
                is_admin = False
            
            if is_admin:
                if not chan_link:
                    if chat.username:
                        chan_link = f"https://t.me/{chat.username}"
                    else:
                        chan_link = "https://t.me"

                config = load_config()
                force_list = config.get("force_channels", [])
                
                if any(c["id"] == chat.id for c in force_list):
                    await update.message.reply_text("⚠️ This channel is already in the Force Join list.")
                    return
                
                force_list.append({
                    "id": chat.id,
                    "title": chat.title or chan_id,
                    "link": chan_link
                })
                config["force_channels"] = force_list
                save_config(config)
                
                context.user_data["admin_state"] = None
                await update.message.reply_text(
                    f"✅ <b>Required Force Channel Added!</b>\n\n"
                    f"📡 Name: <b>{chat.title}</b>\n"
                    f"🆔 ID: <code>{chat.id}</code>\n"
                    f"🔗 Link: {chan_link}\n\n"
                    f"👑 <b>Admin Check:</b> Bot is verified as an Administrator!",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Setup Failed!</b>\n\n"
                    f"The bot is NOT an Administrator inside <b>{chat.title}</b>.\n"
                    f"Please add the bot to that channel first, give it Admin status, and try again.",
                    parse_mode="HTML"
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Failed to verify channel!</b>\n\n"
                f"Error: <code>{e}</code>\n\n"
                f"Please make sure:\n"
                f"1. You entered the correct link/username.\n"
                f"2. The bot is already added to that channel as an Admin.",
                parse_mode="HTML"
            )

    elif state == "waiting_for_refer":
        try:
            parts = text.split("|")
            bonus = float(parts[0].strip())
            username = parts[1].strip().replace("@", "")
            
            config = load_config()
            config["refer_bonus"] = bonus
            config["bot_username"] = username
            save_config(config)
            
            context.user_data["admin_state"] = None
            await update.message.reply_text(f"✅ <b>Refer settings saved!</b>\n\n💰 Bonus: {bonus} BDT\n🤖 Username: @{username}", parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to parse. Example: <code>15 | BotUsername</code>. Error: {e}", parse_mode="HTML")
    
    elif state == "waiting_for_withdraw":
        try:
            parts = text.split("|")
            methods = [m.strip() for m in parts[0].strip().split(",")]
            min_w = float(parts[1].strip())
            
            config = load_config()
            config["withdraw_methods"] = methods
            config["min_withdraw"] = min_w
            save_config(config)
            
            context.user_data["admin_state"] = None
            await update.message.reply_text(f"✅ <b>Withdraw settings saved!</b>\n\n🏦 Methods: {', '.join(methods)}\n📉 Min Limit: {min_w} BDT", parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to parse. Example: <code>BKash, Nagad | 50</code>. Error: {e}", parse_mode="HTML")
    
    elif state == "waiting_for_support":
        config = load_config()
        config["support_link"] = text
        save_config(config)
        
        context.user_data["admin_state"] = None
        await update.message.reply_text(f"✅ <b>Support Link saved!</b>\n\n🌐 Support: {text}", parse_mode="HTML")


# =======================
#    BACKGROUND TASKS
# =======================

async def sms_worker(api_url, bot):
    print(f"[STARTED] SMS Worker loop for {api_url}", flush=True)
    last_number = None
    loop = asyncio.get_running_loop()

    while True:
        otp_data = await loop.run_in_executor(None, fetch_latest_otp, api_url)
        if otp_data:
            if otp_data["number"] != last_number:
                last_number = otp_data["number"]
                msg_text, otp_code = format_sms_message(otp_data)
                # ওটিপি ব্রডকাস্ট পাঠানো হচ্ছে
                await send_to_configured_channel(bot, msg_text)
                print(f"[{datetime.now()}] Broadcasted OTP from {otp_data['number']} | API: {api_url}", flush=True)
        
        await asyncio.sleep(3)


async def numbers_worker(api_url, bot):
    print(f"[STARTED] Numbers Worker loop for {api_url}", flush=True)
    known_numbers = set()
    loop = asyncio.get_running_loop()

    initial_numbers = await loop.run_in_executor(None, fetch_latest_numbers, api_url)
    for n in initial_numbers:
        known_numbers.add(n["number"])
    print(f"[INFO] Initialized {len(known_numbers)} numbers for {api_url}", flush=True)

    while True:
        await asyncio.sleep(10)
        current_numbers = await loop.run_in_executor(None, fetch_latest_numbers, api_url)
        
        for n in current_numbers:
            num = n["number"]
            if num not in known_numbers:
                known_numbers.add(num)
                
                country_name, flag = get_country_info_from_number(num)
                
                if country_name.lower() == "unknown":
                    print(f"[{datetime.now()}] Ignored new number {num} (Country: Unknown)", flush=True)
                    continue
                
                msg = format_new_number_message(n)
                # নতুন নম্বর ব্রডকাস্ট পাঠানো হচ্ছে
                await send_to_configured_channel(bot, msg)
                print(f"[{datetime.now()}] Broadcasted new virtual number: {num} ({country_name}) | API: {api_url}", flush=True)


# =======================
#      APPLICATION START
# =======================

async def post_init(application):
    bot = application.bot
    for api in SMS_API_URLS:
        asyncio.create_task(sms_worker(api, bot))
    for api in NUMBER_API_URLS:
        asyncio.create_task(numbers_worker(api, bot))


def main():
    print("🚀 Initializing telegram bot core...", flush=True) 
    
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(handle_callback_queries))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    print("🤖 Bot started successfully and now listening for updates (Polling)...", flush=True)
    app.run_polling()


if __name__ == "__main__":
    main()
