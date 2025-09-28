"""WhatsApp Cloud API helper utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List

import requests

from .config import BotConfig

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PollMessage:
    """Metadata about a poll message posted to WhatsApp."""

    id: str
    question: str
    options: List[str]


@dataclass(slots=True)
class PollVote:
    """A single vote for a poll option."""

    voter: str
    option: str


class WhatsAppPollClient:
    """Client for sending polls and retrieving vote aggregates."""

    def __init__(self, config: BotConfig) -> None:
        self._config = config
        self._base_url = f"https://graph.facebook.com/{config.whatsapp.graph_api_version}"
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {config.whatsapp.token}",
                "Content-Type": "application/json",
            }
        )

    def send_poll(self, question: str, options: Iterable[str]) -> PollMessage:
        """Send a poll to the configured chat and return the resulting message id."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self._config.whatsapp.chat_id,
            "type": "interactive",
            "interactive": {
                "type": "poll",
                "body": {"text": question},
                "action": {
                    "name": "vote",
                    "parameters": {
                        "title": question,
                        "options": list(options),
                        "allow_multiple_answers": False,
                    },
                },
            },
        }

        url = f"{self._base_url}/{self._config.whatsapp.phone_number_id}/messages"
        LOGGER.info("Sending poll to chat %s", self._config.whatsapp.chat_id)
        response = self._session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        messages = data.get("messages", [])
        if not messages:
            raise RuntimeError("WhatsApp API did not return a message id")
        message_id = messages[0]["id"]
        return PollMessage(id=message_id, question=question, options=list(options))

    def fetch_poll_votes(self, poll_message_id: str) -> List[PollVote]:
        """Fetch poll votes for a given poll message."""
        params = {
            "fields": "reactions.limit(100){reaction,actor},votes.limit(100){option_text,selected_options,participant}",
        }
        url = f"{self._base_url}/{poll_message_id}"
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        votes: List[PollVote] = []
        raw_votes = data.get("votes", {}).get("data", [])
        for vote in raw_votes:
            voter = vote.get("participant", {}).get("wa_id")
            if not voter:
                continue
            selected = vote.get("selected_options") or []
            for option in selected:
                votes.append(PollVote(voter=voter, option=option.get("text", "")))

        return votes


__all__ = ["PollMessage", "PollVote", "WhatsAppPollClient"]
