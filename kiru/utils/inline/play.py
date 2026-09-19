"""
kiru/utils/inline.py  ->  v0.2 PREMIUM

Kya naya hai
------------
* 4 premium themes: royal / neon / minimal / vinyl  (ek line me badlo)
* Live equalizer  ▁▃▆█▅▂  - har timer refresh par bar "naach" te hain, pause par flat
* Vinyl theme me ghoomta record  ◐ ◓ ◑ ◒
* Smooth progress bar + remaining time + percentage
* Live stream par ● ʟɪᴠᴇ badge (ZeroDivisionError fix)
* Telegram 64-byte callback limit safe + "|" safe search query
* Buttons bilkul ORIGINAL jaise: ▷  II  ↻  ‣‣I  ▢  aur lang-file wale labels
* Purane callbacks hi use hote hain -> naya handler likhne ki zarurat nahi

Purane function signatures same hain, purana code bina change chalega.
"""

import math
from typing import Dict, List, Optional

from pyrogram.types import InlineKeyboardButton

from kiru.utils.formatters import time_to_seconds

__version__ = "0.2-premium"

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
THEME = "royal"  # royal | neon | minimal | vinyl  (sirf display ka look)
SMALL_CAPS = True  # sirf status text: ɴᴏᴡ ᴘʟᴀʏɪɴɢ / ʟɪᴠᴇ
SMALL_CAPS_BUTTONS = False  # True karoge to Audio/Video/Close bhi ᴀᴜᴅɪᴏ ban jayenge
SHOW_PLAYLIST_BUTTON = False  # True = extra "Playlist" button (add_playlist callback)
EXTENDED_CONTROLS = False  # True = Loop/Shuffle/Mute row (handlers chahiye)

MAX_CALLBACK_BYTES = 64  # Telegram limit

# Original buttons (jaise pehle the)
CONTROLS = ("▷", "II", "↻", "‣‣I", "▢")  # resume, pause, replay, skip, stop
ARROWS = ("◁", "▷")  # slider back / forward

THEMES: Dict[str, dict] = {
    "royal": dict(bar=("━", "●", "┈"), length=11, deco=("❖", "❖"), eq=True),
    "neon": dict(bar=("▰", "▰", "▱"), length=10, deco=("✦", "✦"), eq=True),
    "minimal": dict(bar=("─", "◉", "─"), length=10, deco=("·", "·"), eq=False),
    "vinyl": dict(bar=("●", "◉", "○"), length=10, deco=None, spin="◐◓◑◒", eq=False),
}

_EQ = "▁▂▃▄▅▆▇█"

_SC_LOWER = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
_SC_TABLE = {}
for _i, _c in enumerate(_SC_LOWER):
    _SC_TABLE[ord("a") + _i] = _c
    _SC_TABLE[ord("A") + _i] = _c


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _theme(name: Optional[str]) -> dict:
    return THEMES.get(name or THEME, THEMES["royal"])


def _label(text) -> str:
    """Status text ke liye small-caps."""
    text = str(text)
    return text.translate(_SC_TABLE) if SMALL_CAPS else text


def _btn(text) -> str:
    """Button label: default me bilkul original (badlaav nahi)."""
    text = str(text)
    return text.translate(_SC_TABLE) if SMALL_CAPS_BUTTONS else text


def _secs(value) -> int:
    try:
        return int(time_to_seconds(value))
    except Exception:
        return 0


def _fmt(sec: float) -> str:
    sec = max(int(sec), 0)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _clean(text) -> str:
    """'|' callback separator hai, user text se hata dete hain."""
    return str(text).replace("|", " ").strip()


def _fit_bytes(text: str, max_bytes: int) -> str:
    if max_bytes <= 0:
        return ""
    return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")


def equalizer(sec: float, bars: int = 6, paused: bool = False) -> str:
    """Time ke hisaab se badalta pseudo-equalizer. Paused = flat."""
    if paused:
        return _EQ[0] * bars
    out = []
    for i in range(bars):
        v = (math.sin(sec * 0.8 + i * 1.1) + math.sin(sec * 1.7 + i * 0.6)) / 4 + 0.5
        out.append(_EQ[min(int(v * len(_EQ)), len(_EQ) - 1)])
    return "".join(out)


def build_progress_bar(
    played_sec: float,
    duration_sec: float,
    length: int = 10,
    chars=("━", "●", "┈"),
) -> str:
    """(done, head, rest) chars se bar. 0 duration par safe."""
    done, head, rest = chars
    length = max(length, 2)
    if duration_sec <= 0:
        pos = 0
    else:
        ratio = min(max(played_sec / duration_sec, 0.0), 1.0)
        pos = min(math.floor(ratio * length), length - 1)
    return done * pos + head + rest * (length - pos - 1)


def _top_row(th: dict, sec: int, paused: bool) -> InlineKeyboardButton:
    label = _label("paused" if paused else "now playing")
    if th.get("eq"):
        eq = equalizer(sec, 6, paused)
        left, right = eq, eq[::-1]
    else:
        left = right = ""
    if th.get("spin"):
        frame = th["spin"][0 if paused else sec % len(th["spin"])]
        d_left = d_right = frame
    else:
        d_left, d_right = th["deco"]
    text = " ".join(x for x in (d_left, left, label, right, d_right) if x)
    return InlineKeyboardButton(text=text, callback_data="GetTimer")


def _controls(chat_id, extended: bool) -> List[List[InlineKeyboardButton]]:
    resume, pause, replay, skip, stop = CONTROLS
    rows = [
        [
            InlineKeyboardButton(text=resume, callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text=pause, callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text=replay, callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text=skip, callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text=stop, callback_data=f"ADMIN Stop|{chat_id}"),
        ]
    ]
    if extended:
        rows.append(
            [
                InlineKeyboardButton(text="🔁", callback_data=f"ADMIN Loop|{chat_id}"),
                InlineKeyboardButton(text="🔀", callback_data=f"ADMIN Shuffle|{chat_id}"),
                InlineKeyboardButton(text="🔇", callback_data=f"ADMIN Mute|{chat_id}"),
                InlineKeyboardButton(text="🔊", callback_data=f"ADMIN Unmute|{chat_id}"),
            ]
        )
    return rows


def _close(_, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=_btn(_["CLOSE_BUTTON"]), callback_data=callback_data)


def _playlist_btn() -> str:
    return _btn("✚ Playlist")


# ----------------------------------------------------------------------------
# Markups
# ----------------------------------------------------------------------------
def track_markup(_, videoid, user_id, channel, fplay, playlist_btn: Optional[bool] = None):
    if playlist_btn is None:
        playlist_btn = SHOW_PLAYLIST_BUTTON

    buttons = [
        [
            InlineKeyboardButton(
                text=_btn(_["P_B_1"]),
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_btn(_["P_B_2"]),
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ]
    ]
    if playlist_btn:
        buttons.append(
            [InlineKeyboardButton(text=_playlist_btn(), callback_data=f"add_playlist {videoid}")]
        )
    buttons.append([_close(_, f"forceclose {videoid}|{user_id}")])
    return buttons


def stream_markup_timer(
    _,
    chat_id,
    played,
    dur,
    theme: Optional[str] = None,
    extended: Optional[bool] = None,
    paused: bool = False,
):
    th = _theme(theme)
    extended = EXTENDED_CONTROLS if extended is None else extended

    p, d = _secs(played), _secs(dur)
    bar = build_progress_bar(p, d, th["length"], th["bar"])

    if d > 0:
        pct = min(int(p / d * 100), 100)
        info = f"−{_fmt(d - p)}  ✦  {pct}%"
    else:
        info = "● " + _label("live")

    buttons = [
        [_top_row(th, p, paused)],
        [InlineKeyboardButton(text=f"{played} {bar} {dur}", callback_data="GetTimer")],
    ]
    buttons += _controls(chat_id, extended)
    buttons.append([InlineKeyboardButton(text=info, callback_data="GetTimer")])
    buttons.append([_close(_, "close")])
    return buttons


def stream_markup(_, chat_id, extended: Optional[bool] = None):
    extended = EXTENDED_CONTROLS if extended is None else extended

    buttons = _controls(chat_id, extended)
    buttons.append([_close(_, "close")])
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_btn(_["P_B_1"]),
                callback_data=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_btn(_["P_B_2"]),
                callback_data=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [_close(_, f"forceclose {videoid}|{user_id}")],
    ]


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_btn(_["P_B_3"]),
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            )
        ],
        [_close(_, f"forceclose {videoid}|{user_id}")],
    ]


def slider_markup(
    _,
    videoid,
    user_id,
    query,
    query_type,
    channel,
    fplay,
    index: Optional[int] = None,
    total: Optional[int] = None,
    playlist_btn: Optional[bool] = None,
):
    if playlist_btn is None:
        playlist_btn = SHOW_PLAYLIST_BUTTON
    left, right = ARROWS

    # query ko 64-byte limit ke andar fit karo
    query = _clean(query)[:20]
    nav_tpl = "slider {d}|{qt}|{q}|{uid}|{ch}|{fp}"
    overhead = len(
        nav_tpl.format(d="B", qt=query_type, q="", uid=user_id, ch=channel, fp=fplay).encode()
    )
    close_overhead = len(f"forceclose |{user_id}".encode())
    query = _fit_bytes(query, MAX_CALLBACK_BYTES - max(overhead, close_overhead))

    close_text = _btn(_["CLOSE_BUTTON"])
    if index is not None and total:
        close_text = f"{close_text} · {index}/{total}"

    buttons = [
        [
            InlineKeyboardButton(
                text=_btn(_["P_B_1"]),
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_btn(_["P_B_2"]),
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ]
    ]
    if playlist_btn:
        buttons.append(
            [InlineKeyboardButton(text=_playlist_btn(), callback_data=f"add_playlist {videoid}")]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=left,
                callback_data=nav_tpl.format(
                    d="B", qt=query_type, q=query, uid=user_id, ch=channel, fp=fplay
                ),
            ),
            InlineKeyboardButton(text=close_text, callback_data=f"forceclose {query}|{user_id}"),
            InlineKeyboardButton(
                text=right,
                callback_data=nav_tpl.format(
                    d="F", qt=query_type, q=query, uid=user_id, ch=channel, fp=fplay
                ),
            ),
        ]
    )
    return buttons
