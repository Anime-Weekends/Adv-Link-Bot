# +++ Modified By Yato [telegram username: @i_killed_my_clan & @ProYato] +++
# WARNING: Removing credits is prohibited and disrespectful.

import os
import logging
from logging.handlers import RotatingFileHandler
from os import environ
import re

# === Environment Variables Setup ===

# Telegram Bot Credentials
TG_BOT_TOKEN = environ.get("TG_BOT_TOKEN", "")
APP_ID = int(environ.get("APP_ID", "0"))
API_HASH = environ.get("API_HASH", "")

# Owner & App Configurations
OWNER_ID = int(environ.get("OWNER_ID", "6497757690"))
PORT = environ.get("PORT", "8080")

# Database Configurations
DB_URI = environ.get("DB_URI", "")
DB_NAME = environ.get("DB_NAME", "link")

# Auto Approval Settings
id_pattern = re.compile(r'^\-?\d+$')  # Pattern to detect integer IDs
CHAT_ID_RAW = environ.get('CHAT_ID', '')
CHAT_ID = [
    int(cid) if id_pattern.match(cid) else cid
    for cid in CHAT_ID_RAW.split()
]

APPROVED = environ.get("APPROVED_WELCOME", "on").lower()
TEXT = environ.get(
    "APPROVED_WELCOME_TEXT",
    "<b>{mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {title} ɪs ᴀᴘᴘʀᴏᴠᴇᴅ.\n‣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @Codeflix_Bots</b>"
)

# Bot Workers
TG_BOT_WORKERS = int(environ.get("TG_BOT_WORKERS", "40"))

# === Bot Media & Messages ===

START_IMG = "https://telegra.ph/file/f3d3aff9ec422158feb05-d2180e3665e0ac4d32.jpg"
START_PIC_FILE_ID = START_IMG

START_MSG = environ.get(
    "START_MESSAGE",
    "<b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ.\n"
    "ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs sᴀғᴇ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.\n\n"
    "<blockquote>‣ ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ : <a href='https://t.me/codeflix_bots'>ʏᴀᴛᴏ</a></blockquote></b>"
)

HELP = environ.get(
    "HELP_MESSAGE",
    "<b><blockquote expandable>"
    "» Creator: <a href=https://t.me/proyato>Yato</a>\n"
    "» Our Community: <a href=https://t.me/otakuflix_network>Flix Network</a>\n"
    "» Anime Channel: <a href=https://t.me/animes_cruise>Anime Cruise</a>\n"
    "» Ongoing Anime: <a href=https://t.me/Ongoing_cruise>Ongoing cruise</a>\n"
    "» Developer: <a href=https://t.me/onlyyuji>Yuji</a>"
    "</blockquote></b>"
)

ABOUT = environ.get(
    "ABOUT_MESSAGE",
    "<b><blockquote expandable>"
    "This bot is developed by Yato (@ProYato) to securely share Telegram channel links with temporary invite links, "
    "protecting your channels from copyright issues."
    "</blockquote></b>"
)

ABOUT_TXT = """<b>›› ᴄᴏᴍᴍᴜɴɪᴛʏ: <a href='https://t.me/otakuflix_network'>ᴏᴛᴀᴋᴜғʟɪx</a>
<blockquote expandable>
›› ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/codeflix_bots'>Cʟɪᴄᴋ ʜᴇʀᴇ</a>
›› ᴏᴡɴᴇʀ: <a href='https://t.me/cosmic_freak'>ʏᴀᴛᴏ</a>
›› ʟᴀɴɢᴜᴀɢᴇ: <a href='https://docs.python.org/3/'>Pʏᴛʜᴏɴ 3</a>
›› ʟɪʙʀᴀʀʏ: <a href='https://docs.pyrogram.org/'>Pʏʀᴏɢʀᴀᴍ ᴠ2</a>
›› ᴅᴀᴛᴀʙᴀsᴇ: <a href='https://www.mongodb.com/docs/'>Mᴏɴɢᴏ ᴅʙ</a>
›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: @ProYato
</blockquote></b>"""  # Respect credits!

CHANNELS_TXT = """<b>›› ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/animes_cruise'>ᴀɴɪᴍᴇ ᴄʀᴜɪsᴇ</a>
<blockquote expandable>
›› ᴍᴏᴠɪᴇs: <a href='https://t.me/movieflixspot'>ᴍᴏᴠɪᴇғʟɪx sᴘᴏᴛ</a>
›› ᴡᴇʙsᴇʀɪᴇs: <a href='https://t.me/webseries_flix'>ᴡᴇʙsᴇʀɪᴇs ғʟɪx</a>
›› ᴀᴅᴜʟᴛ ᴄʜᴀɴɴᴇʟs: <a href='https://t.me/hanime_arena'>ᴄᴏʀɴʜᴜʙ</a>
›› ᴍᴀɴʜᴡᴀ ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/pornhwa_flix'>ᴘᴏʀɴʜᴡᴀ</a>
›› ᴄᴏᴍᴍᴜɴɪᴛʏ: <a href='https://t.me/otakuflix_network'>ᴏᴛᴀᴋᴜғʟɪx</a>
›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: @ProYato
</blockquote></b>"""  # Respect credits!

# === Default Texts ===

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ᴍᴀsᴛᴇʀ. ɢᴏ ᴀᴡᴀʏ, ʙɪᴛᴄʜ 🙃!"

# === Logging Configuration ===

LOG_FILE_NAME = "links-sharingbot.txt"
DATABASE_CHANNEL = int(environ.get("DATABASE_CHANNEL", "0"))  # Channel for storing user links

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50_000_000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)

# Set pyrogram log level to WARNING to reduce verbosity
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    """Returns a logger instance with the specified name."""
    return logging.getLogger(name)


# === Admins Configuration ===

try:
    ADMINS = [int(x) for x in environ.get("ADMINS", "6497757690").split()]
except ValueError:
    raise Exception("Admins list must contain only valid integer user IDs.")

# Ensure OWNER_ID and default admin are always included
if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)
if 6497757690 not in ADMINS:
    ADMINS.append(6497757690)
