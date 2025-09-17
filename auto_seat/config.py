import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class LoginConfig:
	url: str
	username_selector: str
	password_selector: str
	submit_selector: str
	logged_in_check_selector: Optional[str] = None


@dataclass
class ReservationConfig:
	url: str
	date_input_selector: Optional[str] = None
	start_time_selector: Optional[str] = None
	end_time_selector: Optional[str] = None
	area_selector: Optional[str] = None
	seat_selector_template: Optional[str] = None
	seat_page_template: Optional[str] = None
	confirm_selector: Optional[str] = None
	result_success_selector: Optional[str] = None
	result_failure_selector: Optional[str] = None
	pre_click_selectors: Optional[list[str]] = None
	post_click_selectors: Optional[list[str]] = None


@dataclass
class AppConfig:
	base_url: str
	login: LoginConfig
	reservation: ReservationConfig
	storage_dir: Path
	browser: str = "chromium"


def load_config(config_path: str | Path) -> AppConfig:
	load_dotenv(override=False)
	path = Path(config_path)
	if not path.exists():
		raise FileNotFoundError(f"Config file not found: {path}")
	with path.open("r", encoding="utf-8") as f:
		data: Dict[str, Any] = yaml.safe_load(f) or {}

	storage_dir = Path(os.getenv("AUTO_SEAT_STORAGE", Path.home() / ".auto_seat"))
	storage_dir.mkdir(parents=True, exist_ok=True)

	login_cfg = data.get("login", {})
	reservation_cfg = data.get("reservation", {})

	app_cfg = AppConfig(
		base_url=data.get("base_url", ""),
		login=LoginConfig(
			url=login_cfg.get("url", ""),
			username_selector=login_cfg.get("username_selector", ""),
			password_selector=login_cfg.get("password_selector", ""),
			submit_selector=login_cfg.get("submit_selector", ""),
			logged_in_check_selector=login_cfg.get("logged_in_check_selector"),
		),
		reservation=ReservationConfig(
			url=reservation_cfg.get("url", ""),
			date_input_selector=reservation_cfg.get("date_input_selector"),
			start_time_selector=reservation_cfg.get("start_time_selector"),
			end_time_selector=reservation_cfg.get("end_time_selector"),
			area_selector=reservation_cfg.get("area_selector"),
			seat_selector_template=reservation_cfg.get("seat_selector_template"),
			seat_page_template=reservation_cfg.get("seat_page_template"),
			confirm_selector=reservation_cfg.get("confirm_selector"),
			result_success_selector=reservation_cfg.get("result_success_selector"),
			result_failure_selector=reservation_cfg.get("result_failure_selector"),
			pre_click_selectors=reservation_cfg.get("pre_click_selectors") or [],
			post_click_selectors=reservation_cfg.get("post_click_selectors") or [],
		),
		storage_dir=storage_dir,
		browser=data.get("browser", "chromium"),
	)
	return app_cfg


def getenv_or_fail(key: str, default: Optional[str] = None) -> str:
	val = os.getenv(key, default)
	if not val:
		print(f"Environment variable '{key}' is required.", file=sys.stderr)
		sys.exit(2)
	return val