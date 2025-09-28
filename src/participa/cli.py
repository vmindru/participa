"""Command line interface for the training attendance bot."""
from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path

from .bot import TrainingAttendanceBot, load_config


def _parse_date(value: str | None) -> dt.date | None:
    if value is None:
        return None
    return dt.datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WhatsApp attendance bot")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to the YAML configuration file",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD. Defaults to today.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("send-polls", help="Send polls for training sessions")
    subparsers.add_parser(
        "collect-results", help="Collect poll votes and write a CSV report"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config = load_config(args.config)
    bot = TrainingAttendanceBot(config)
    date = _parse_date(args.date)

    if args.command == "send-polls":
        bot.send_daily_polls(date)
    elif args.command == "collect-results":
        bot.collect_attendance(date)
    else:  # pragma: no cover - argparse enforces valid values
        parser.error(f"Unknown command {args.command}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
