# Participa WhatsApp Training Attendance Bot

This repository contains a configurable WhatsApp chatbot that reads a Google Calendar for upcoming training events, posts poll messages in a WhatsApp chat, and exports the daily attendance results to CSV.

## Features

- **Google Calendar integration** – reads a service account calendar and filters events by a configurable title pattern.
- **WhatsApp poll automation** – posts a poll for every training session using the WhatsApp Cloud API.
- **Attendance exports** – fetches votes at the end of the day and writes a CSV summary mapped to player names.
- **Configurable** – chat id, calendar configuration, filter pattern, poll options, and player phone mapping live in a YAML config file.

## Project layout

```
config.sample.yaml         # Example configuration file
src/participa/             # Python package containing the bot
  ├── bot.py               # High-level orchestration
  ├── calendar.py          # Google Calendar wrapper
  ├── cli.py               # Command line entry point
  ├── config.py            # YAML configuration loader
  ├── poll_manager.py      # Poll persistence and CSV export
  └── whatsapp.py          # WhatsApp Cloud API client
```

## Getting started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create a configuration file**

   Copy `config.sample.yaml` to `config.yaml` and fill in your credentials:

   - `calendar.credentials_path`: path to the Google service account JSON file.
   - `calendar.filter_pattern`: regular expression used to select training events.
   - `whatsapp` section: details for the WhatsApp Cloud API (token, phone number id, and chat id).
   - `players`: mapping of WhatsApp phone numbers (international format) to player names.

3. **Run the bot**

   Send polls for today:

   ```bash
   python -m participa.cli send-polls
   ```

   Collect results for today and export to CSV:

   ```bash
   python -m participa.cli collect-results
   ```

   Use `--date YYYY-MM-DD` to target a different day and `--config path/to/file.yaml` to use a custom configuration file.

## Requirements

- Python 3.11+
- Google Calendar service account with read access to the calendar containing the training events.
- WhatsApp Cloud API credentials with permission to send polls to the configured chat.

## Notes

- Poll metadata is stored in `data/polls_YYYY-MM-DD.json` (customizable via `storage_dir`).
- Daily CSV exports are saved to `out/attendance_YYYYMMDD.csv` (customizable via `results_dir`).
- Retrieving poll votes requires enabling the appropriate fields in the WhatsApp Graph API and may require webhook subscriptions depending on your account tier.

## License

This project is provided as-is without warranty.
