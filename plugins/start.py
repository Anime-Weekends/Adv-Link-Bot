 
import asyncio
import base64
from datetime import datetime, timedelta
from collections import defaultdict

from pyrogram import filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto,
)
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

# 🔧 Project-specific imports
from bot import Bot
from config import START_PIC_FILE_ID, START_MSG
from database.database import (
    db,
    get_current_invite_link,
    save_invite_link,
    get_channel_by_encoded_link,
    get_channel_by_encoded_link2,
    get_original_link,
)
from plugins.fsub import is_subscribed, not_joined
from plugins.newpost import revoke_invite_after_5_minutes
from helper_func import delete_after_delay

user_banned_until = {}

# Broadcast variables
cancel_lock = asyncio.Lock()
is_canceled = False

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id

    if user_id in user_banned_until:
        if datetime.now() < user_banned_until[user_id]:
            return await message.reply_text(
                "<b><blockquote expandable>You are temporarily banned from using commands due to spamming. Try again later.</b>",
                parse_mode=ParseMode.HTML
            )

    # ✅ Check Force Subscription
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # Add user if not already present
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            is_request = base64_string.startswith("req_")

            if is_request:
                base64_string = base64_string[4:]
                channel_id = await get_channel_by_encoded_link2(base64_string)
            else:
                channel_id = await get_channel_by_encoded_link(base64_string)

            if not channel_id:
                return await message.reply_text(
                    "<b><blockquote expandable>Invalid or expired invite link.</b>",
                    parse_mode=ParseMode.HTML
                )

         
            # Check if this is a /genlink link (original_link exists)
            from database.database import get_original_link
            original_link = await get_original_link(channel_id)
            if original_link:
                button = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("• Proceed to Link •", url=original_link)]]
                )
                return await message.reply_text(
                    "<b><blockquote expandable>ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</b>",
                    reply_markup=button,
                    parse_mode=ParseMode.HTML
                )

            old_link_info = await get_current_invite_link(channel_id)
            if old_link_info:
                try:
                    await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                    print(f"Revoked old {'request' if old_link_info['is_request'] else 'invite'} link for channel {channel_id}")
                except Exception as e:
                    print(f"Failed to revoke old link for channel {channel_id}: {e}")

            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                expire_date=datetime.now() + timedelta(minutes=5),
                creates_join_request=is_request
            )

            await save_invite_link(channel_id, invite.invite_link, is_request)

            button_text = "• ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ •" if is_request else "• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •"
            button = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, url=invite.invite_link)]])

            wait_msg = await message.reply_text(
                "<b>Please wait...</b>",
                parse_mode=ParseMode.HTML
            )
            
            await asyncio.sleep(0.5)
            
            await wait_msg.delete()
            
            await message.reply_text(
                "<b><blockquote expandable>ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</b>",
                reply_markup=button,
                parse_mode=ParseMode.HTML
            )

            note_msg = await message.reply_text(
                "<u><b>Note: If the link is expired, please click the post link again to get a new one.</b></u>",
                parse_mode=ParseMode.HTML
            )

            # Auto-delete the note message after 5 minutes
            asyncio.create_task(delete_after_delay(note_msg, 300))

            asyncio.create_task(revoke_invite_after_5_minutes(client, channel_id, invite.invite_link, is_request))

        except Exception as e:
            await message.reply_text(
                "<b><blockquote expandable>Invalid or expired invite link.</b>",
                parse_mode=ParseMode.HTML
            )
            print(f"Decoding error: {e}")
    else:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton("• ᴄʜᴀɴɴᴇʟs", callback_data="channels")],
                [InlineKeyboardButton("• Close •", callback_data="close")]
            ]
        )
        
        try:
            await message.reply_photo(
                photo=START_PIC_FILE_ID,
                caption=START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error sending start picture: {e}")
            await message.reply_text(
                START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()

#=====================================================================================##
#──────────────────────
#────────ᴊᴇғғʏ ᴅᴇᴠ─────────
#──────────────────────


# Create a global dictionary to store chat data
chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i><pre>Cʜᴇᴄᴋɪɴɢ sᴜʙsᴄʀɪᴘᴛɪᴏɴ...</pre></i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await db.show_channels()  # Should return list of (chat_id, mode) tuples
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)  # fetch mode 

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    # Cache chat info
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    # Generate proper invite link based on the mode
                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                        link = invite.invite_link

                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None)
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @RexySama</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )

        # Retry Button
        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id, 
                message_effect_id=5104841245755180586  # 🔥
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Final Error: {e}")
        await temp.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @RexySama</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )


WAIT_MSG = "<b>Processing...</b>"

REPLY_ERROR = "<code>Use this command as a reply to any Telegram message without any spaces.</code>"

@Bot.on_message(filters.command('status') & filters.private & is_owner_or_admin)
async def info(client: Bot, message: Message):   
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• Close •", callback_data="close")]])
    
    start_time = time.time()
    temp_msg = await message.reply("<b><i>Processing...</i></b>", quote=True, parse_mode=ParseMode.HTML)
    end_time = time.time()
    
    ping_time = (end_time - start_time) * 1000
    
    users = await full_userbase()
    now = datetime.now()
    delta = now - client.uptime
    bottime = get_readable_time(delta.seconds)
    
    await temp_msg.edit(
        f"<b>Users: {len(users)}\n\nUptime: {bottime}\n\nPing: {ping_time:.2f} ms</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.command('broadcast') & filters.private & is_owner_or_admin)
async def send_text(client: Bot, message: Message):
    global is_canceled
    async with cancel_lock:
        is_canceled = False
    mode = False
    broad_mode = ''
    store = message.text.split()[1:]
    
    if store and len(store) == 1 and store[0] == 'silent':
        mode = True
        broad_mode = 'Silent '

    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = len(query)
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcasting message... This will take some time.</i>", parse_mode=ParseMode.HTML)
        bar_length = 20
        final_progress_bar = "●" * bar_length
        complete_msg = f"🤖 {broad_mode}Broadcast Completed ✅"
        progress_bar = ''
        last_update_percentage = 0
        percent_complete = 0
        update_interval = 0.05

        for i, chat_id in enumerate(query, start=1):
            async with cancel_lock:
                if is_canceled:
                    final_progress_bar = progress_bar
                    complete_msg = f"🤖 {broad_mode}Broadcast Canceled ❌"
                    break
            try:
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1

            percent_complete = i / total

            if percent_complete - last_update_percentage >= update_interval or last_update_percentage == 0:
                num_blocks = int(percent_complete * bar_length)
                progress_bar = "●" * num_blocks + "○" * (bar_length - num_blocks)
    
                status_update = f"""<b>🤖 {broad_mode}Broadcast in Progress...

Progress: [{progress_bar}] {percent_complete:.0%}

Total Users: {total}
Successful: {successful}
Blocked Users: {blocked}
Deleted Accounts: {deleted}
Unsuccessful: {unsuccessful}</b>

<i>To stop the broadcast, use: /cancel</i>"""
                await pls_wait.edit(status_update, parse_mode=ParseMode.HTML)
                last_update_percentage = percent_complete

        final_status = f"""<b>{complete_msg}

Progress: [{final_progress_bar}] {percent_complete:.0%}

Total Users: {total}
Successful: {successful}
Blocked Users: {blocked}
Deleted Accounts: {deleted}
Unsuccessful: {unsuccessful}</b>"""
        return await pls_wait.edit(final_status, parse_mode=ParseMode.HTML)

    else:
        msg = await message.reply(REPLY_ERROR, parse_mode=ParseMode.HTML)
        await asyncio.sleep(8)
        await msg.delete()

user_message_count = {}
user_banned_until = {}

MAX_MESSAGES = 3
TIME_WINDOW = timedelta(seconds=10)
BAN_DURATION = timedelta(hours=1)

"""

@Bot.on_message(filters.private)
async def monitor_messages(client: Bot, message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    if message.text and message.text.startswith("/"):
        return

    if user_id in ADMINS:
        return 

    if user_id in user_banned_until and now < user_banned_until[user_id]:
        await message.reply_text(
            "<b><blockquote expandable>You are temporarily banned from using commands due to spamming. Try again later.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    if user_id not in user_message_count:
        user_message_count[user_id] = []

    user_message_count[user_id].append(now)
    user_message_count[user_id] = [time for time in user_message_count[user_id] if now - time <= TIME_WINDOW]

    if len(user_message_count[user_id]) > MAX_MESSAGES:
        user_banned_until[user_id] = now + BAN_DURATION
        await message.reply_text(
            "<b><blockquote expandable>You are temporarily banned from using commands due to spamming. Try again later.</b>",
            parse_mode=ParseMode.HTML
        )
        return

"""

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data  
    chat_id = query.message.chat.id
    
    if data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
    
    elif data == "about":
        user = await client.get_users(OWNER_ID)
        user_link = f"https://t.me/{user.username}" if user.username else f"tg://openmessage?user_id={OWNER_ID}"
        
        await query.edit_message_media(
            InputMediaPhoto(
                START_IMG,
                ABOUT_TXT
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'), InlineKeyboardButton('ᴄʟᴏsᴇ •', callback_data='close')]
            ]),
        )

    elif data == "channels":
        user = await client.get_users(OWNER_ID)
        user_link = f"https://t.me/{user.username}" if user.username else f"tg://openmessage?user_id={OWNER_ID}" 
        ownername = f"<a href={user_link}>{user.first_name}</a>" if user.first_name else f"<a href={user_link}>no name !</a>"
        await query.edit_message_media(
            InputMediaPhoto(START_IMG, 
                            CHANNELS_TXT
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'), InlineKeyboardButton('home•', callback_data='setting')]
            ]),
        )
    elif data in ["start", "home"]:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton("• ᴄʜᴀɴɴᴇʟs", callback_data="channels")],
                [InlineKeyboardButton("• Close •", callback_data="close")]
            ]
        )
        try:
            await query.edit_message_media(
                InputMediaPhoto(
                    START_IMG,
                    START_MSG
                ),
                reply_markup=inline_buttons
            )
        except Exception as e:
            print(f"Error sending start/home photo: {e}")
            await query.edit_message_text(
                START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )

def delete_after_delay(msg, delay):
    async def inner():
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except:
            pass
    return inner()
