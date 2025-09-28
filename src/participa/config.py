"""Configuration handling for the Participa WhatsApp attendance bot."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

import yaml


@dataclass(slots=True)
class CalendarConfig:
    """Google Calendar connection details."""

    calendar_id: str
    credentials_path: Path
    filter_pattern: str = ".*"


@dataclass(slots=True)
class WhatsAppConfig:
    """Configuration required to communicate with the WhatsApp Cloud API."""

    token: str
    phone_number_id: str
    chat_id: str
    graph_api_version: str = "v19.0"


@dataclass(slots=True)
class BotConfig:
    """Top level configuration for the attendance bot."""

    calendar: CalendarConfig
    whatsapp: WhatsAppConfig
    players: Mapping[str, str] = field(default_factory=dict)
    poll_options: Sequence[str] = field(
        default_factory=lambda: (
            "✅ Attending",
            "❌ Not attending",
            "❓ Maybe",
        )
    )
    storage_dir: Path = Path("data")
    results_dir: Path = Path("out")

    def ensure_directories(self) -> None:
        """Create the storage directories if they do not exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


def _expand_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _load_calendar_config(raw: Mapping[str, object]) -> CalendarConfig:
    try:
        calendar_id = raw["calendar_id"]
        credentials = raw["credentials_path"]
    except KeyError as exc:  # pragma: no cover - explicit failure path
        raise ValueError("calendar configuration requires 'calendar_id' and 'credentials_path'") from exc

    return CalendarConfig(
        calendar_id=str(calendar_id),
        credentials_path=_expand_path(credentials),
        filter_pattern=str(raw.get("filter_pattern", ".*")),
    )


def _load_whatsapp_config(raw: Mapping[str, object]) -> WhatsAppConfig:
    required = {"token", "phone_number_id", "chat_id"}
    missing = required.difference(raw)
    if missing:  # pragma: no cover - explicit failure path
        raise ValueError(f"whatsapp configuration missing keys: {', '.join(sorted(missing))}")

    return WhatsAppConfig(
        token=str(raw["token"]),
        phone_number_id=str(raw["phone_number_id"]),
        chat_id=str(raw["chat_id"]),
        graph_api_version=str(raw.get("graph_api_version", "v19.0")),
    )


def _load_players(raw: Mapping[str, object] | Iterable[Mapping[str, object]]) -> Dict[str, str]:
    players: Dict[str, str] = {}
    if isinstance(raw, Mapping):
        for phone, name in raw.items():
            players[str(phone)] = str(name)
        return players

    for entry in raw:
        phone = entry.get("phone")
        name = entry.get("name")
        if not phone or not name:
            raise ValueError("player entries must define 'phone' and 'name'")
        players[str(phone)] = str(name)
    return players


def load_config(path: str | Path) -> BotConfig:
    """Load bot configuration from a YAML file."""
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    if not isinstance(payload, Mapping):  # pragma: no cover - defensive
        raise ValueError("configuration file must contain a mapping")

    calendar = _load_calendar_config(payload.get("calendar", {}))
    whatsapp = _load_whatsapp_config(payload.get("whatsapp", {}))
    players_raw = payload.get("players", {})
    players = _load_players(players_raw)

    poll_options = payload.get("poll_options")
    if poll_options is None:
        poll_options_seq: Sequence[str] = (
            "✅ Attending",
            "❌ Not attending",
            "❓ Maybe",
        )
    else:
        poll_options_seq = tuple(str(option) for option in poll_options)

    storage_dir = _expand_path(payload.get("storage_dir", "data"))
    results_dir = _expand_path(payload.get("results_dir", "out"))

    config = BotConfig(
        calendar=calendar,
        whatsapp=whatsapp,
        players=players,
        poll_options=poll_options_seq,
        storage_dir=storage_dir,
        results_dir=results_dir,
    )
    config.ensure_directories()
    return config


__all__ = [
    "BotConfig",
    "CalendarConfig",
    "WhatsAppConfig",
    "load_config",
]
