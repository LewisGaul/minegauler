from unittest import mock

import flask
import requests

import server
from bot import routes


app = flask.Flask(__name__)

app.add_url_rule("/bot/message", "bot_message", routes.bot_message, methods=["POST"])


def send_bot_message():
    url = "http://localhost:5000/bot"
    data = {
        # Webhook info
        "id": "Y2lzY29zcGFyazovL3VzL1dFQkhPT0svZjRlNjA1NjAtNjYwMi00ZmIwLWEyNWEtOTQ5ODgxNjA5NDk3",
        "name": "New message in 'Project Unicorn' room",
        "resource": "messages",
        "event": "created",
        "filter": "roomId=Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
        "orgId": "OTZhYmMyYWEtM2RjYy0xMWU1LWExNTItZmUzNDgxOWNkYzlh",
        "createdBy": "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
        "appId": "Y2lzY29zcGFyazovL3VzL0FQUExJQ0FUSU9OL0MyNzljYjMwYzAyOTE4MGJiNGJkYWViYjA2MWI3OTY1Y2RhMzliNjAyOTdjODUwM2YyNjZhYmY2NmM5OTllYzFm",
        "ownedBy": "creator",
        "status": "active",
        "actorId": "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
        # Message data
        "data": {
            "id": "Y2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
            "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
            "personId": "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
            "personEmail": "matt@example.com",
            "created": "2015-10-18T14:26:16.000Z",
        },
    }
    requests.post(url, json=data)


def receive_bot_message(msg: str):
    post_data = {
        "data": {
            "id": "foo",
            "personEmail": "person@foo.com",
            "roomId": "room",
            "personId": "person",
        }
    }
    resp = mock.Mock()
    resp.json.return_value = {
        "id": "msg ID",
        "roomId": "room ID",
        "roomType": "group",
        "toPersonId": "to-person ID",
        "toPersonEmail": "julie@example.com",
        "text": msg,
        "markdown": msg,
        "personId": "person ID",
        "personEmail": "matt@example.com",
        "mentionedPeople": ["person ID 1", "person ID 2"],
        "mentionedGroups": ["all"],
        "attachments": [],
        "files": [],
        "created": "2015-10-18T14:26:16+00:00",
    }
    with server.utils.multiple_contexts(
        app.test_client(), mock.patch("requests.get", return_value=resp)
    ) as ctx:
        tc, _ = ctx
        return tc.post("/bot/message", json=post_data)
