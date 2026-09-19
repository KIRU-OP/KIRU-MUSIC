from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

# ⚠️ Neeche ke 3 import apne project ke hisaab se adjust karo
from kiru import app
from kiru.core.queue import is_autoqueue_on, set_autoqueue, toggle_autoqueue
from kiru.utils.inline.queue import aq_markup


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


def _status_text(status: bool) -> str:
    return "ON ✅" if status else "OFF ❌"


# ───────────────────────── /autoqueue command ─────────────────────────
# Use:
#   /autoqueue        -> toggle
#   /autoqueue on     -> ON
#   /autoqueue off    -> OFF
@app.on_message(filters.command("autoqueue") & filters.group)
async def autoqueue_command(client, message: Message):
    chat_id = message.chat.id

    # normal admin ya anonymous admin (sender_chat == group) dono allowed
    if message.from_user:
        allowed = await _is_admin(chat_id, message.from_user.id)
    else:
        allowed = bool(message.sender_chat and message.sender_chat.id == chat_id)
    if not allowed:
        return await message.reply_text("❌ Sirf admins autoqueue change kar sakte hain.")

    arg = message.command[1].lower() if len(message.command) > 1 else None
    if arg == "on":
        set_autoqueue(chat_id, True)
        status = True
    elif arg == "off":
        set_autoqueue(chat_id, False)
        status = False
    elif arg is None:
        status = toggle_autoqueue(chat_id)
    else:
        return await message.reply_text("Use: /autoqueue [on|off]")

    await message.reply_text(
        f"🔁 AutoQueue {_status_text(status)}\n"
        "Queue khatam hone par related gaana apne aap add hoga."
        if status
        else f"🔁 AutoQueue {_status_text(status)}"
    )


# ───────────────────────── inline button callback ─────────────────────────
@app.on_callback_query(filters.regex(r"^AutoQueue\|"))
async def autoqueue_callback(client, query: CallbackQuery):
    try:
        chat_id = int(query.data.split("|")[1])
    except (IndexError, ValueError):
        return await query.answer("Invalid button.", show_alert=True)

    if not await _is_admin(chat_id, query.from_user.id):
        return await query.answer("❌ Sirf admins ye button use kar sakte hain.", show_alert=True)

    status = toggle_autoqueue(chat_id)
    await query.answer(f"AutoQueue {_status_text(status)}")
    try:
        # `_` (language dict) aq_markup me use nahi hota, isliye None chalega
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(aq_markup(None, chat_id, autoqueue=status))
        )
    except Exception:
        pass  # message purana ho gaya ho ya markup same ho to ignore
