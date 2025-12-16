from datetime import date, datetime

from attrs import define
from tomlkit import loads

from cattrs.preconf.tomlkit import make_converter


@define
class Event:
    event_date: date
    event_datetime: datetime


def test_tomlkit_dates():
    """Native date and datetime objects from tomlkit are properly handled."""
    toml_input = """
event_date = 2025-12-16
event_datetime = 2025-12-16T20:00:00
"""
    converter = make_converter()
    parsed = loads(toml_input)
    structured = converter.structure(parsed, Event)
    assert structured.event_date == date(2025, 12, 16)
    assert structured.event_datetime == datetime(2025, 12, 16, 20, 0, 0)
