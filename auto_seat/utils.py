from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console(force_terminal=True)


@dataclass
class OpenTime:
	"""Represents a clock time in local timezone when reservations open."""
	hour: int
	minute: int
	second: int = 0

	@classmethod
	def parse(cls, time_str: str) -> "OpenTime":
		parts = [int(p) for p in time_str.split(":")]
		if len(parts) == 2:
			parts.append(0)
		return cls(parts[0], parts[1], parts[2])

	def as_today_datetime(self) -> _dt.datetime:
		now = _dt.datetime.now()
		return now.replace(hour=self.hour, minute=self.minute, second=self.second, microsecond=0)


def wait_until(target: _dt.datetime, message: str = "Waiting") -> None:
	if target <= _dt.datetime.now():
		return
	with Progress(
		SpinnerColumn(),
		TextColumn("[progress.description]{task.description}"),
		transient=True,
	) as progress:
		progress.add_task(description=f"{message} until {target.strftime('%H:%M:%S')}...", total=None)
		# Sleep in decreasing intervals for accuracy without busy-waiting
		while True:
			now = _dt.datetime.now()
			if now >= target:
				break
			remaining = (target - now).total_seconds()
			if remaining > 60:
				time.sleep(30)
			elif remaining > 10:
				time.sleep(5)
			elif remaining > 1:
				time.sleep(0.2)
			else:
				time.sleep(remaining)


def parse_date(date_str: Optional[str]) -> _dt.date:
	if not date_str or date_str.lower() in {"today", "tod", "t"}:
		return _dt.date.today()
	if date_str.lower() in {"tomorrow", "tmr", "tom"}:
		return _dt.date.today() + _dt.timedelta(days=1)
	return _dt.datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_time(hhmm: str) -> str:
	"""Return HH:MM string validated."""
	_h, _m = hhmm.split(":")
	return f"{int(_h):02d}:{int(_m):02d}"