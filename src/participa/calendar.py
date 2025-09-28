"""Google Calendar utilities for retrieving training sessions."""
from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import dataclass
from typing import Iterable, List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from .config import CalendarConfig

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TrainingEvent:
    """Representation of a single training event."""

    id: str
    title: str
    start: dt.datetime
    end: dt.datetime
    location: str | None = None

    @property
    def date_key(self) -> str:
        return self.start.strftime("%Y-%m-%d")


class GoogleCalendarClient:
    """Thin wrapper around the Google Calendar API."""

    def __init__(self, config: CalendarConfig) -> None:
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        self._credentials = Credentials.from_service_account_file(
            str(config.credentials_path), scopes=scopes
        )
        self._calendar_id = config.calendar_id
        self._pattern = re.compile(config.filter_pattern, re.IGNORECASE)

    def fetch_training_events(
        self, date: dt.date | None = None
    ) -> List[TrainingEvent]:
        """Fetch training events for the provided date."""
        if date is None:
            date = dt.date.today()

        start = dt.datetime.combine(date, dt.time.min, tzinfo=dt.timezone.utc)
        end = dt.datetime.combine(date, dt.time.max, tzinfo=dt.timezone.utc)

        service = build("calendar", "v3", credentials=self._credentials)
        events = (
            service.events()
            .list(
                calendarId=self._calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )

        return list(self._parse_events(events))

    def _parse_events(self, raw_events: Iterable[dict]) -> Iterable[TrainingEvent]:
        for entry in raw_events:
            summary = entry.get("summary", "")
            if not self._pattern.search(summary):
                LOGGER.debug("Ignoring event '%s'", summary)
                continue

            start_raw = entry.get("start", {}).get("dateTime")
            end_raw = entry.get("end", {}).get("dateTime")
            if not start_raw or not end_raw:
                LOGGER.warning("Event '%s' missing dateTime information", summary)
                continue

            start = dt.datetime.fromisoformat(start_raw)
            end = dt.datetime.fromisoformat(end_raw)

            yield TrainingEvent(
                id=str(entry.get("id")),
                title=summary,
                start=start,
                end=end,
                location=entry.get("location"),
            )


__all__ = ["GoogleCalendarClient", "TrainingEvent"]
