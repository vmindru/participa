"""Persistence helpers for poll metadata and vote aggregation."""
from __future__ import annotations

import csv
import datetime as dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Mapping

from .calendar import TrainingEvent
from .config import BotConfig
from .whatsapp import PollMessage, PollVote


@dataclass(slots=True)
class StoredPoll:
    """Poll metadata stored on disk."""

    event_id: str
    message_id: str
    question: str
    options: List[str]
    start: str
    end: str
    location: str | None

    @classmethod
    def from_event(cls, event: TrainingEvent, poll: PollMessage) -> "StoredPoll":
        return cls(
            event_id=event.id,
            message_id=poll.id,
            question=poll.question,
            options=list(poll.options),
            start=event.start.isoformat(),
            end=event.end.isoformat(),
            location=event.location,
        )


class PollStorage:
    """Utility class for persisting poll metadata."""

    def __init__(self, config: BotConfig) -> None:
        self._config = config

    def _poll_file(self, date_key: str) -> Path:
        return self._config.storage_dir / f"polls_{date_key}.json"

    def record_poll(self, event: TrainingEvent, poll: PollMessage) -> None:
        payload = [asdict(p) for p in self.load_polls(event.start.date())]
        payload.append(asdict(StoredPoll.from_event(event, poll)))
        file_path = self._poll_file(event.start.strftime("%Y-%m-%d"))
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_polls(self, date: dt.date) -> List[StoredPoll]:
        file_path = self._poll_file(date.strftime("%Y-%m-%d"))
        if not file_path.exists():
            return []
        data = json.loads(file_path.read_text(encoding="utf-8"))
        polls: List[StoredPoll] = []
        for entry in data:
            polls.append(
                StoredPoll(
                    event_id=entry["event_id"],
                    message_id=entry["message_id"],
                    question=entry["question"],
                    options=list(entry["options"]),
                    start=entry["start"],
                    end=entry["end"],
                    location=entry.get("location"),
                )
            )
        return polls


def aggregate_votes(
    poll: StoredPoll,
    votes: Iterable[PollVote],
    players: Mapping[str, str],
) -> List[dict]:
    """Aggregate votes and map them to player names."""
    results: List[dict] = []
    for vote in votes:
        player_name = players.get(vote.voter, vote.voter)
        results.append(
            {
                "player": player_name,
                "phone": vote.voter,
                "response": vote.option,
                "event_id": poll.event_id,
                "question": poll.question,
                "start": poll.start,
                "end": poll.end,
                "location": poll.location or "",
            }
        )
    return results


def export_votes_to_csv(
    config: BotConfig,
    date: dt.date,
    rows: Iterable[dict],
) -> Path:
    """Write aggregated rows to a CSV file and return the path."""
    config.results_dir.mkdir(parents=True, exist_ok=True)
    file_path = config.results_dir / f"attendance_{date.strftime('%Y%m%d')}.csv"
    fieldnames = [
        "player",
        "phone",
        "response",
        "event_id",
        "question",
        "start",
        "end",
        "location",
    ]
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return file_path


__all__ = [
    "StoredPoll",
    "PollStorage",
    "aggregate_votes",
    "export_votes_to_csv",
]
