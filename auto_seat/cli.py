from __future__ import annotations

import argparse
from pathlib import Path
from rich.console import Console

from .config import load_config, getenv_or_fail
from .booking import run_reservation

console = Console(force_terminal=True)


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(
		prog="auto-seat",
		description="DLUFL Library seat auto-reservation script (config-driven)",
	)
	p.add_argument("--config", default="config.yaml", help="Path to YAML config file")
	p.add_argument("--username", help="Login username; fallback to env AUTO_SEAT_USERNAME")
	p.add_argument("--password", help="Login password; fallback to env AUTO_SEAT_PASSWORD")
	p.add_argument("--seat", required=True, help="Seat number or id to reserve")
	p.add_argument("--date", help="Date YYYY-MM-DD, 'today', or 'tomorrow'")
	p.add_argument("--start", default="08:00", help="Start time HH:MM")
	p.add_argument("--end", default="22:00", help="End time HH:MM")
	p.add_argument("--area", help="Optional area/room label")
	p.add_argument("--open-time", help="Optional time to wait until HH:MM[:SS]")
	p.add_argument("--headless", action="store_true", help="Run browser in headless mode")
	p.add_argument("--data-dir", help="Override user data dir for persistent login")
	return p


def main() -> None:
	args = build_parser().parse_args()
	cfg = load_config(args.config)
	username = args.username or getenv_or_fail("AUTO_SEAT_USERNAME")
	password = args.password or getenv_or_fail("AUTO_SEAT_PASSWORD")
	user_data_dir = Path(args.data_dir) if args.data_dir else cfg.storage_dir

	success = run_reservation(
		config=cfg,
		username=username,
		password=password,
		seat=args.seat,
		date_str=args.date,
		start_time=args.start,
		end_time=args.end,
		area=args.area,
		open_time_str=args.open_time,
		headless=args.headless,
		user_data_dir=user_data_dir,
	)
	if success:
		console.print("[bold green]Reservation successful")
		raise SystemExit(0)
	else:
		console.print("[bold red]Reservation may have failed. Check logs/website.")
		raise SystemExit(1)


if __name__ == "__main__":
	main()