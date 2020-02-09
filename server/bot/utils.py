"""
utils.py - Bot utilities

February 2020, Lewis Gaul
"""

__all__ = (
    "BOT_NAME",
    "USER_NAMES",
    "get_message",
    "send_group_message",
    "send_message",
    "send_new_best_message",
    "send_myself_message",
    "set_bot_access_token",
    "user_from_email",
)

import logging

import requests
from requests_toolbelt import MultipartEncoder

from minegauler.shared import highscores as hs


logger = logging.getLogger(__name__)


USER_NAMES = {"legaul": "Siwel G", "fegaul": "Felix"}  # TODO

BOT_NAME = "minegaulerbot"
_BOT_ACCESS_TOKEN = ""
_BOT_EMAIL = f"{BOT_NAME}@webex.bot"
_WEBEX_GROUP_ROOM_ID = (
    "Y2lzY29zcGFyazovL3VzL1JPT00vNzYyNjI4NTAtMzg3Ni0xMWVhLTlhM2ItODMyNzMyZDlkZTg3"
)


# ------------------------------------------------------------------------------
# External
# ------------------------------------------------------------------------------


def set_bot_access_token(token: str) -> None:
    global _BOT_ACCESS_TOKEN
    _BOT_ACCESS_TOKEN = token


def get_message(msg_id: str) -> str:
    response = requests.get(
        f"https://api.ciscospark.com/v1/messages/{msg_id}",
        headers={"Authorization": f"Bearer {_BOT_ACCESS_TOKEN}"},
    )
    response.raise_for_status()
    return response.json()["text"]


def send_message(
    room_id: str, text: str, *, is_person_id=False, markdown=False
) -> requests.Response:
    logger.debug(
        "Sending message to %s:\n%s", "person" if is_person_id else "room", text
    )
    id_field = "toPersonId" if is_person_id else "roomId"
    text_field = "markdown" if markdown else "text"
    multipart = MultipartEncoder({text_field: text, id_field: room_id})
    response = requests.post(
        "https://api.ciscospark.com/v1/messages",
        data=multipart,
        headers={
            "Authorization": f"Bearer {_BOT_ACCESS_TOKEN}",
            "Content-Type": multipart.content_type,
        },
    )
    response.raise_for_status()
    return response


def send_myself_message(text: str) -> requests.Response:
    return send_message(_get_my_id(), text, is_person_id=True)


def send_group_message(text: str) -> requests.Response:
    return send_message(_WEBEX_GROUP_ROOM_ID, text)


def send_new_best_message(h: hs.HighscoreStruct) -> None:
    """Send a group message when a new personal time record is set."""
    if h.difficulty == "B":
        diff = "beginner"
    elif h.difficulty == "I":
        diff = "intermediate"
    elif h.difficulty == "E":
        diff = "expert"
    elif h.difficulty == "M":
        diff = "master"
    else:
        assert False
    send_group_message(
        f"New personal record of {h.elapsed:.2f} set by {h.name} on {diff}!\n"
        f"Settings: drag-select={_strbool(h.drag_select)}, per-cell={h.per_cell}"
    )


def user_from_email(email: str) -> str:
    return email.split("@", maxsplit=1)[0]


# ------------------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------------------


def _strbool(b: bool) -> str:
    return "True" if b else "False"


def _get_person_id(name_or_email: str) -> str:
    if "@" in name_or_email:
        params = {"email": name_or_email}
    else:
        params = {"displayName": name_or_email}
    response = requests.get(
        f"https://api.ciscospark.com/v1/people",
        params=params,
        headers={"Authorization": f"Bearer {_BOT_ACCESS_TOKEN}"},
    )
    response.raise_for_status()
    return response.json()["items"][0]["id"]


def _get_my_id() -> str:
    return _get_person_id("Lewis Gaul")


def _get_bot_id() -> str:
    return _get_person_id("Minegauler Bot")
