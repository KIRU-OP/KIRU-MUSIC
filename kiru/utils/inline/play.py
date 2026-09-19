"""
kiru/utils/inline.py  ->  v0.2

Changelog v0.2
--------------
+ Naya progress bar engine (3 styles: classic / blocks / dots, custom length)
+ Extended player controls: Seek -10s/+10s, Loop, Shuffle, Mute, Unmute
+ "Add to playlist" button track & slider markup me
+ Slider me page indicator (index/total)
+ Telegram 64-byte callback_data limit se safe (auto trim)
+ "|" wale search query se callback parsing nahi tootegi
+ Bug fix: 0% par bar galat (end me) dikhta tha
+ Bug fix: duration 0 (live stream) par ZeroDivisionError
+ Type hints + docstrings

Purane function signatures same hain, isliye purana code bina change ke chalega.
"""

import math
from typing import List, Optional

from pyrogram.types import InlineKeyboardButton

from kiru.utils.formatters import time_to_seconds

__version__ = "0.2"

# ----------------------------------------------------------------------------
# Config (yahan se on/off kar sakte ho)
# ----------------------------------------------------------------------------
EXTENDED_CONTROLS = True  # seek / loop / shuffle / mute rows
DEFAULT_BAR_STYLE = "classic"  # classic | blocks | dots
DEFAULT_BAR_LENGTH = 10
SHOW_PLAYLIST_BUTTON = True  # "Add to playlist" button

MAX_CALLBACK_BYTES = 64  # Telegram limit

# style -> (done, head, rest)
BAR_STYLES = {
    "classic": ("—", "◉", "—"),  # ——◉———————
    "blocks": ("▰", "▰", "▱"),  # ▰▰▰▱▱▱▱▱▱▱
    "dots": ("●", "●", "○"),  # ●●●○○○○○○○
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def build_progress_bar(
    played_sec: float,
    duration_sec: float,
    length: int = DEFAULT_BAR_LENGTH,
    style: str = DEFAULT_BAR_STYLE,
) -> str:
    """Progress bar string return karta hai. Live/0 duration par safe hai."""
    done, head, rest = BAR_STYLES.get(style, BAR_STYLES["classic"])
    length = max(length, 2)

    if duration_sec <= 0:
        pos = 0
    else:
        ratio = min(max(played_sec / duration_sec, 0.0), 1.0)
        pos = min(math.floor(ratio * length), length - 1)

    return done * pos + head + rest * (length - pos - 1)


def _clean(text) -> str:
    """'|' callback separator hai, isliye user text se hata dete hain."""
    return str(text).replace("|", " ").strip()


def _fit_bytes(text: str, max_bytes: int) -> str:
    """Text ko utf-8 bytes ke hisaab se trim karta hai (emoji safe)."""
    if max_bytes <= 0:
        return ""
    return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")


def _control_rows(chat_id, extended: bool) -> List[List[InlineKeyboardButton]]:
    rows = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ]
    ]
    if extended:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⏪ 10s", callback_data=f"ADMIN SeekBack|{chat_id}"
                ),
                InlineKeyboardButton(text="🔁", callback_data=f"ADMIN Loop|{chat_id}"),
                InlineKeyboardButton(
                    text="🔀", callback_data=f"ADMIN Shuffle|{chat_id}"
                ),
                InlineKeyboardButton(
                    text="10s ⏩", callback_data=f"ADMIN SeekFwd|{chat_id}"
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(text="🔇", callback_data=f"ADMIN Mute|{chat_id}"),
                InlineKeyboardButton(
                    text="🔊", callback_data=f"ADMIN Unmute|{chat_id}"
                ),
            ]
        )
    return rows


# ----------------------------------------------------------------------------
# Markups
# ----------------------------------------------------------------------------
def track_markup(_, videoid, user_id, channel, fplay, playlist_btn: Optional[bool] = None):
    if playlist_btn is None:
        playlist_btn = SHOW_PLAYLIST_BUTTON

    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
    ]
    if playlist_btn:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="➕ Playlist", callback_data=f"add_playlist {videoid}"
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ]
    )
    return buttons


def stream_markup_timer(
    _,
    chat_id,
    played,
    dur,
    style: Optional[str] = None,
    extended: Optional[bool] = None,
    bar_length: int = DEFAULT_BAR_LENGTH,
):
    style = style or DEFAULT_BAR_STYLE
    extended = EXTENDED_CONTROLS if extended is None else extended

    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    bar = build_progress_bar(played_sec, duration_sec, bar_length, style)

    buttons = _control_rows(chat_id, extended)
    buttons.append(
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ]
    )
    buttons.append([InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")])
    return buttons


def stream_markup(_, chat_id, extended: Optional[bool] = None):
    extended = EXTENDED_CONTROLS if extended is None else extended

    buttons = _control_rows(chat_id, extended)
    buttons.append([InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")])
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


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

    # query ko itna trim karo ki 64-byte limit ke andar rahe
    query = _clean(query)[:20]
    nav_tpl = "slider {d}|{qt}|{q}|{uid}|{ch}|{fp}"
    overhead = len(
        nav_tpl.format(d="B", qt=query_type, q="", uid=user_id, ch=channel, fp=fplay).encode()
    )
    close_overhead = len(f"forceclose |{user_id}".encode())
    budget = MAX_CALLBACK_BYTES - max(overhead, close_overhead)
    query = _fit_bytes(query, budget)

    close_text = _["CLOSE_BUTTON"]
    if index is not None and total:
        close_text = f"{close_text} ({index}/{total})"

    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
    ]
    if playlist_btn:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="➕ Playlist", callback_data=f"add_playlist {videoid}"
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=nav_tpl.format(
                    d="B", qt=query_type, q=query, uid=user_id, ch=channel, fp=fplay
                ),
            ),
            InlineKeyboardButton(
                text=close_text,
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=nav_tpl.format(
                    d="F", qt=query_type, q=query, uid=user_id, ch=channel, fp=fplay
                ),
            ),
        ]
    )
    return buttons
