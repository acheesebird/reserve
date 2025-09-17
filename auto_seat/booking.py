from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Page
from tenacity import retry, stop_after_attempt, wait_fixed
from rich.console import Console

from .config import AppConfig
from .utils import OpenTime, wait_until, parse_date, parse_time

console = Console(force_terminal=True)


async def _ensure_logged_in(page: Page, cfg: AppConfig, username: str, password: str) -> None:
	await page.goto(cfg.login.url, wait_until="domcontentloaded")
	if cfg.login.logged_in_check_selector:
		if await page.locator(cfg.login.logged_in_check_selector).first.is_visible():
			console.log("Already logged in.")
			return
	await page.fill(cfg.login.username_selector, username)
	await page.fill(cfg.login.password_selector, password)
	await page.click(cfg.login.submit_selector)
	# Allow time for navigation or ajax login
	await page.wait_for_timeout(1500)
	if cfg.login.logged_in_check_selector:
		await page.wait_for_selector(cfg.login.logged_in_check_selector, state="visible", timeout=10000)


async def _prepare_reservation(page: Page, cfg: AppConfig, date: dt.date, start: str, end: str, area: Optional[str]) -> None:
	await page.goto(cfg.reservation.url, wait_until="domcontentloaded")
	for selector in cfg.reservation.pre_click_selectors:
		await page.locator(selector).first.click()
	if cfg.reservation.date_input_selector:
		await page.fill(cfg.reservation.date_input_selector, date.strftime("%Y-%m-%d"))
	if cfg.reservation.start_time_selector:
		await page.fill(cfg.reservation.start_time_selector, start)
	if cfg.reservation.end_time_selector:
		await page.fill(cfg.reservation.end_time_selector, end)
	if area and cfg.reservation.area_selector:
		await page.select_option(cfg.reservation.area_selector, label=area)


@retry(stop=stop_after_attempt(5), wait=wait_fixed(0.3))
async def _attempt_seat_selection(page: Page, cfg: AppConfig, seat: str) -> None:
	if cfg.reservation.seat_page_template:
		url = cfg.reservation.seat_page_template.format(seat=seat)
		await page.goto(url, wait_until="domcontentloaded")
	elif cfg.reservation.seat_selector_template:
		selector = cfg.reservation.seat_selector_template.format(seat=seat)
		await page.locator(selector).first.click()
	else:
		raise RuntimeError("Seat selection not configured. Provide seat_page_template or seat_selector_template.")
	if cfg.reservation.confirm_selector:
		await page.locator(cfg.reservation.confirm_selector).first.click()
	await page.wait_for_timeout(250)


async def _verify_result(page: Page, cfg: AppConfig) -> bool:
	if cfg.reservation.result_success_selector:
		success = page.locator(cfg.reservation.result_success_selector).first
		if await success.is_visible():
			return True
	if cfg.reservation.result_failure_selector:
		failure = page.locator(cfg.reservation.result_failure_selector).first
		if await failure.is_visible():
			return False
	# Fallback: assume success if page contains "成功" or "已预约"
	content = await page.content()
	return ("成功" in content) or ("已预约" in content)


async def reserve_seat(
	config: AppConfig,
	username: str,
	password: str,
	seat: str,
	date_str: Optional[str],
	start_time: str,
	end_time: str,
	area: Optional[str],
	open_time_str: Optional[str],
	headless: bool,
	user_data_dir: Optional[Path] = None,
) -> bool:
	date = parse_date(date_str)
	start = parse_time(start_time)
	end = parse_time(end_time)
	open_dt: Optional[dt.datetime] = None
	if open_time_str:
		open_time = OpenTime.parse(open_time_str)
		open_dt = open_time.as_today_datetime()
		if open_dt < dt.datetime.now():
			# if already past today open time, do not wait
			open_dt = None

	async with async_playwright() as p:
		browser_type = getattr(p, config.browser)
		storage_dir = user_data_dir or config.storage_dir
		context: BrowserContext
		if storage_dir:
			context = await browser_type.launch_persistent_context(
				user_data_dir=str(storage_dir), headless=headless, locale="zh-CN"
			)
		else:
			context = await browser_type.launch_persistent_context(user_data_dir=str(Path.home()/".auto_seat"), headless=headless, locale="zh-CN")

		page = await context.new_page()
		try:
			await _ensure_logged_in(page, config, username, password)
			await _prepare_reservation(page, config, date, start, end, area)
			if open_dt is not None:
				wait_until(open_dt, message="Waiting for open time")
			await _attempt_seat_selection(page, config, seat)
			success = await _verify_result(page, config)
			return success
		finally:
			await page.close()
			await context.close()


def run_reservation(
	config: AppConfig,
	username: str,
	password: str,
	seat: str,
	date_str: Optional[str],
	start_time: str,
	end_time: str,
	area: Optional[str],
	open_time_str: Optional[str],
	headless: bool,
	user_data_dir: Optional[Path] = None,
) -> bool:
	return asyncio.run(
		reserve_seat(
			config=config,
			username=username,
			password=password,
			seat=seat,
			date_str=date_str,
			start_time=start_time,
			end_time=end_time,
			area=area,
			open_time_str=open_time_str,
			headless=headless,
			user_data_dir=user_data_dir,
		)
	)