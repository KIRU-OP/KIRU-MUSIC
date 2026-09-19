import asyncio
from typing import Optional, Union

from kiru.misc import db
from kiru.utils.formatters import check_duration, seconds_to_min
from config import autoclean, time_to_seconds


# ─────────────────────────── AUTOQUEUE ───────────────────────────
# chat_id -> True/False (in-memory, restart pe reset ho jayega)
autoqueue_db: dict = {}
# chat_id -> pehle play/queue ho chuke vidids (repeat rokne ke liye)
autoqueue_history: dict = {}
AUTOQUEUE_HISTORY_LIMIT = 50


def is_autoqueue_on(chat_id) -> bool:
    return autoqueue_db.get(chat_id, False)


def set_autoqueue(chat_id, status: bool) -> None:
    autoqueue_db[chat_id] = status
    if not status:
        autoqueue_history.pop(chat_id, None)


def toggle_autoqueue(chat_id) -> bool:
    """Toggle karke naya status return karta hai."""
    status = not is_autoqueue_on(chat_id)
    set_autoqueue(chat_id, status)
    return status


def _search_related(query: str, exclude: set) -> Optional[dict]:
    """Blocking search - hamesha executor me chalana."""
    from youtubesearchpython import VideosSearch

    results = VideosSearch(query, limit=15).result().get("result", [])
    for r in results:
        # live streams (duration None) aur already-played gaane skip
        if r.get("id") in exclude or not r.get("duration"):
            continue
        return r
    return None


async def put_autoqueue(chat_id) -> bool:
    """
    Agar autoqueue ON hai aur queue me sirf current track bacha hai,
    to ek related gaana queue ke end me add kar deta hai.

    Isko track khatam hone par, `check.pop(0)` se PEHLE call karo.
    True return kare to naya gaana add ho gaya hai.
    """
    if not is_autoqueue_on(chat_id):
        return False

    queue = db.get(chat_id)
    if not queue or len(queue) != 1:
        return False

    current = queue[0]
    if current.get("streamtype") in ("live", "index", "telegram"):
        return False

    seen = autoqueue_history.setdefault(chat_id, set())
    if current.get("vidid"):
        seen.add(current["vidid"])

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, _search_related, current["title"], seen
        )
    except Exception:
        return False
    if not result:
        return False

    vidid = result["id"]
    await put_queue(
        chat_id,
        current["chat_id"],
        f"vid_{vidid}",
        result["title"],
        result["duration"],
        "AutoQueue",
        vidid,
        current.get("user_id", 0),
        current.get("streamtype", "audio"),
    )

    seen.add(vidid)
    if len(seen) > AUTOQUEUE_HISTORY_LIMIT:
        seen.pop()
    return True
# ─────────────────────────────────────────────────────────────────


async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
):
    title = title.title()
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except:
        duration_in_seconds = 0
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, put)
        else:
            db[chat_id] = []
            db[chat_id].append(put)
    else:
        db[chat_id].append(put)
    autoclean.append(file)


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
):
    if "20.212.146.162" in vidid:
        try:
            dur = await asyncio.get_event_loop().run_in_executor(
                None, check_duration, vidid
            )
            duration = seconds_to_min(dur)
        except:
            duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
            dur = 0
    else:
        dur = 0
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": dur,
        "played": 0,
    }
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, put)
        else:
            db[chat_id] = []
            db[chat_id].append(put)
    else:
        db[chat_id].append(put)
