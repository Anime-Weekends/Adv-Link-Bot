
import motor.motor_asyncio
import base64
from config import DB_URI, DB_NAME
from datetime import datetime
from typing import List, Optional

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

# Collections
user_data = database['users']
channels_collection = database['channels']
fsub_data = database['fsub']
rqst_fsub_data = database['request_forcesub']
rqst_fsub_Channel_data = database['request_forcesub_channel']
admins_collection = database['admins']

# USER MANAGEMENT

async def add_user(user_id: int) -> bool:
    if not isinstance(user_id, int) or user_id <= 0:
        print(f"Invalid user_id: {user_id}")
        return False
    try:
        existing_user = await user_data.find_one({'_id': user_id})
        if existing_user:
            return False
        await user_data.insert_one({'_id': user_id, 'created_at': datetime.utcnow()})
        return True
    except Exception as e:
        print(f"Error adding user {user_id}: {e}")
        return False

async def present_user(user_id: int) -> bool:
    if not isinstance(user_id, int):
        return False
    return bool(await user_data.find_one({'_id': user_id}))

async def full_userbase() -> List[int]:
    try:
        user_docs = user_data.find()
        return [doc['_id'] async for doc in user_docs]
    except Exception as e:
        print(f"Error fetching userbase: {e}")
        return []

async def del_user(user_id: int) -> bool:
    try:
        result = await user_data.delete_one({'_id': user_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting user {user_id}: {e}")
        return False

# ADMIN MANAGEMENT

async def is_admin(user_id: int) -> bool:
    try:
        user_id = int(user_id)
        return bool(await admins_collection.find_one({'_id': user_id}))
    except Exception as e:
        print(f"Error checking admin status for {user_id}: {e}")
        return False

async def add_admin(user_id: int) -> bool:
    try:
        user_id = int(user_id)
        await admins_collection.update_one({'_id': user_id}, {'$set': {'_id': user_id}}, upsert=True)
        return True
    except Exception as e:
        print(f"Error adding admin {user_id}: {e}")
        return False

async def remove_admin(user_id: int) -> bool:
    try:
        result = await admins_collection.delete_one({'_id': user_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing admin {user_id}: {e}")
        return False

async def list_admins() -> List[int]:
    try:
        admins = await admins_collection.find().to_list(None)
        return [admin['_id'] for admin in admins]
    except Exception as e:
        print(f"Error listing admins: {e}")
        return []

# CHANNEL MANAGEMENT

async def save_channel(channel_id: int) -> bool:
    if not isinstance(channel_id, int):
        print(f"Invalid channel_id: {channel_id}")
        return False
    try:
        await channels_collection.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "channel_id": channel_id,
                    "invite_link_expiry": None,
                    "created_at": datetime.utcnow(),
                    "status": "active"
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving channel {channel_id}: {e}")
        return False

async def get_channels() -> List[int]:
    try:
        channels = await channels_collection.find({"status": "active"}).to_list(None)
        valid_channels = []
        for channel in channels:
            if isinstance(channel, dict) and "channel_id" in channel:
                valid_channels.append(channel["channel_id"])
            else:
                print(f"Invalid channel document: {channel}")
        if not valid_channels:
            print(f"No valid channels found in database. Total documents checked: {len(channels)}")
        return valid_channels
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []

async def delete_channel(channel_id: int) -> bool:
    try:
        result = await channels_collection.delete_one({"channel_id": channel_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting channel {channel_id}: {e}")
        return False

async def save_encoded_link(channel_id: int) -> Optional[str]:
    if not isinstance(channel_id, int):
        print(f"Invalid channel_id: {channel_id}")
        return None
    try:
        encoded_link = base64.urlsafe_b64encode(str(channel_id).encode()).decode()
        await channels_collection.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "encoded_link": encoded_link,
                    "status": "active",
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return encoded_link
    except Exception as e:
        print(f"Error saving encoded link for channel {channel_id}: {e}")
        return None

async def get_channel_by_encoded_link(encoded_link: str) -> Optional[int]:
    if not isinstance(encoded_link, str):
        return None
    try:
        channel = await channels_collection.find_one({"encoded_link": encoded_link, "status": "active"})
        return channel["channel_id"] if channel and "channel_id" in channel else None
    except Exception as e:
        print(f"Error fetching channel by encoded link {encoded_link}: {e}")
        return None

async def save_encoded_link2(channel_id: int, encoded_link: str) -> Optional[str]:
    if not isinstance(channel_id, int) or not isinstance(encoded_link, str):
        print(f"Invalid input: channel_id={channel_id}, encoded_link={encoded_link}")
        return None
    try:
        await channels_collection.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "req_encoded_link": encoded_link,
                    "status": "active",
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return encoded_link
    except Exception as e:
        print(f"Error saving secondary encoded link for channel {channel_id}: {e}")
        return None

async def get_channel_by_encoded_link2(encoded_link: str) -> Optional[int]:
    if not isinstance(encoded_link, str):
        return None
    try:
        channel = await channels_collection.find_one({"req_encoded_link": encoded_link, "status": "active"})
        return channel["channel_id"] if channel and "channel_id" in channel else None
    except Exception as e:
        print(f"Error fetching channel by secondary encoded link {encoded_link}: {e}")
        return None

async def save_invite_link(channel_id: int, invite_link: str, is_request: bool) -> bool:
    if not isinstance(channel_id, int) or not isinstance(invite_link, str):
        print(f"Invalid input: channel_id={channel_id}, invite_link={invite_link}")
        return False
    try:
        await channels_collection.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "current_invite_link": invite_link,
                    "is_request_link": is_request,
                    "invite_link_created_at": datetime.utcnow(),
                    "status": "active"
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving invite link for channel {channel_id}: {e}")
        return False

async def get_current_invite_link(channel_id: int) -> Optional[dict]:
    if not isinstance(channel_id, int):
        return None
    try:
        channel = await channels_collection.find_one({"channel_id": channel_id, "status": "active"})
        if channel and "current_invite_link" in channel:
            return {
                "invite_link": channel["current_invite_link"],
                "is_request": channel.get("is_request_link", False)
            }
        return None
    except Exception as e:
        print(f"Error fetching current invite link for channel {channel_id}: {e}")
        return None

async def set_approval_off(channel_id: int, off: bool = True) -> bool:
    if not isinstance(channel_id, int):
        print(f"Invalid channel_id: {channel_id}")
        return False
    try:
        await channels_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"approval_off": off}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error setting approval_off for channel {channel_id}: {e}")
        return False

async def is_approval_off(channel_id: int) -> bool:
    if not isinstance(channel_id, int):
        return False
    try:
        channel = await channels_collection.find_one({"channel_id": channel_id})
        return bool(channel and channel.get("approval_off", False))
    except Exception as e:
        print(f"Error checking approval_off for channel {channel_id}: {e}")
        return False

# FSUB CHANNEL MANAGEMENT

async def channel_exist(channel_id: int) -> bool:
    found = await fsub_data.find_one({'_id': channel_id})
    return bool(found)

async def add_channel(channel_id: int) -> None:
    if not await channel_exist(channel_id):
        await fsub_data.insert_one({'_id': channel_id})

async def rem_channel(channel_id: int) -> None:
    if await channel_exist(channel_id):
        await fsub_data.delete_one({'_id': channel_id})

async def show_channels() -> List[int]:
    channel_docs = await fsub_data.find().to_list(length=None)
    return [doc['_id'] for doc in channel_docs]

async def get_channel_mode(channel_id: int) -> str:
    data = await fsub_data.find_one({'_id': channel_id})
    return data.get("mode", "off") if data else "off"

async def set_channel_mode(channel_id: int, mode: str) -> None:
    await fsub_data.update_one(
        {'_id': channel_id},
        {'$set': {'mode': mode}},
        upsert=True
    )

# REQUEST FORCE-SUB MANAGEMENT

async def req_user(channel_id: int, user_id: int) -> None:
    try:
        await rqst_fsub_Channel_data.update_one(
            {'_id': int(channel_id)},
            {'$addToSet': {'user_ids': int(user_id)}},
            upsert=True
        )
    except Exception as e:
        print(f"[DB ERROR] Failed to add user to request list: {e}")

async def del_req_user(channel_id: int, user_id: int) -> None:
    await rqst_fsub_Channel_data.update_one(
        {'_id': channel_id},
        {'$pull': {'user_ids': user_id}}
    )

async def req_user_exist(channel_id: int, user_id: int) -> bool:
    try:
        found = await rqst_fsub_Channel_data.find_one({
            '_id': int(channel_id),
            'user_ids': int(user_id)
        })
        return bool(found)
    except Exception as e:
        print(f"[DB ERROR] Failed to check request list: {e}")
        return False

async def add_rqst_channel(channel_id: int) -> None:
    try:
        await rqst_fsub_Channel_data.update_one({'_id': int(channel_id)}, {'$setOnInsert': {'user_ids': []}}, upsert=True)
    except Exception as e:
        print(f"[DB ERROR] Failed to add request channel: {e}")

async def rem_rqst_channel(channel_id: int) -> None:
    try:
        await rqst_fsub_Channel_data.delete_one({'_id': int(channel_id)})
    except Exception as e:
        print(f"[DB ERROR] Failed to remove request channel: {e}")

async def rqst_channel_exist(channel_id: int) -> bool:
    try:
        found = await rqst_fsub_Channel_data.find_one({'_id': int(channel_id)})
        return bool(found)
    except Exception as e:
        print(f"[DB ERROR] Failed to check request channel existence: {e}")
        return False

async def get_all_req_users(channel_id: int) -> List[int]:
    try:
        doc = await rqst_fsub_Channel_data.find_one({'_id': int(channel_id)})
        return doc.get('user_ids', []) if doc else []
    except Exception as e:
        print(f"[DB ERROR] Failed to get all request users: {e}")
        return []

async def del_all_req_users(channel_id: int) -> None:
    try:
        await rqst_fsub_Channel_data.update_one({'_id': int(channel_id)}, {'$set': {'user_ids': []}}, upsert=True)
    except Exception as e:
        print(f"[DB ERROR] Failed to delete all request users: {e}")

async def get_all_rqst_channels() -> List[int]:
    try:
        docs = await rqst_fsub_Channel_data.find().to_list(length=None)
        return [doc['_id'] for doc in docs]
    except Exception as e:
        print(f"[DB ERROR] Failed to get all request channels: {e}")
        return []
                       
#──────────────────────
#────────ᴊᴇғғʏ ᴅᴇᴠ─────────
#──────────────────────
