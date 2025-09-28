"""High level orchestration for the training attendance bot."""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Iterable, List, Optional

from .calendar import GoogleCalendarClient, TrainingEvent
from .config import BotConfig, load_config
from .poll_manager import (
    PollStorage,
    StoredPoll,
    aggregate_votes,
    export_votes_to_csv,
)
from .whatsapp import WhatsAppPollClient

LOGGER = logging.getLogger(__name__)


class TrainingAttendanceBot:
    """Coordinates calendar lookups, poll sending, and vote aggregation."""

    def __init__(
        self,
        config: BotConfig,
        calendar_client: Optional[GoogleCalendarClient] = None,
        whatsapp_client: Optional[WhatsAppPollClient] = None,
        storage: Optional[PollStorage] = None,
    ) -> None:
        self.config = config
        self.calendar = calendar_client or GoogleCalendarClient(config.calendar)
        self.whatsapp = whatsapp_client or WhatsAppPollClient(config)
        self.storage = storage or PollStorage(config)

    def send_daily_polls(self, date: Optional[dt.date] = None) -> List[StoredPoll]:
        """Create a WhatsApp poll for each training event on the given date."""
        events = self._fetch_events(date)
        stored_polls: List[StoredPoll] = []
        for event in events:
            question = self._format_question(event)
            poll = self.whatsapp.send_poll(question, self.config.poll_options)
            stored = StoredPoll.from_event(event, poll)
            self.storage.record_poll(event, poll)
            stored_polls.append(stored)
            LOGGER.info(
                "Created poll %s for event %s", poll.id, event.title
            )
        return stored_polls

    def collect_attendance(self, date: Optional[dt.date] = None) -> Path:
        """Collect poll votes and write them to a CSV file."""
        if date is None:
            date = dt.date.today()
        polls = self.storage.load_polls(date)
        rows: List[dict] = []
        for poll in polls:
            votes = self.whatsapp.fetch_poll_votes(poll.message_id)
            rows.extend(aggregate_votes(poll, votes, self.config.players))
        if not rows:
            LOGGER.warning("No poll responses found for %s", date)
        csv_path = export_votes_to_csv(self.config, date, rows)
        LOGGER.info("Attendance exported to %s", csv_path)
        return csv_path

    def _fetch_events(self, date: Optional[dt.date]) -> Iterable[TrainingEvent]:
        events = self.calendar.fetch_training_events(date)
        if not events:
            LOGGER.info("No training events found for %s", date or dt.date.today())
        return events

    @staticmethod
    def _format_question(event: TrainingEvent) -> str:
        start_time = event.start.strftime("%H:%M")
        return f"{event.title} at {start_time} — will you attend?"


__all__ = ["TrainingAttendanceBot", "load_config"]
