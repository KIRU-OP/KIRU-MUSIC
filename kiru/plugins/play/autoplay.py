from pyrogram import filters
from pyrogram.types import Message

from kiru import app
from kiru.utils.database import autoplay_off, autoplay_on, is_autoplay
from kiru.utils.decorators.language import language
from config import BANNED_USERS


@app.on_message(
    filters.command(["autoplay"]) & filters.group & ~BANNED_USERS
)
@language
async def autoplay_toggle(client, message: Message, _):
    chat_id = message.chat.id

    if len(message.command) != 2:
        current = await is_autoplay(chat_id)
        status = "ᴏɴ ✅" if current else "ᴏғғ ❌"
        return await message.reply_text(
            f"» Autoplay is currently **{status}** for this chat.\n\n"
            f"Usage: `/autoplay on` or `/autoplay off`"
        )

    state = message.command[1].lower()

    if state in ("on", "enable"):
        await autoplay_on(chat_id)
        await message.reply_text("✅ Autoplay has been turned **ON**.\n\nWhen the queue ends, I'll keep playing related tracks.")
    elif state in ("off", "disable"):
        await autoplay_off(chat_id)
        await message.reply_text("❌ Autoplay has been turned **OFF**.\n\nI'll leave the voice chat once the queue ends.")
    else:
        await message.reply_text("Please use `/autoplay on` or `/autoplay off`.")
