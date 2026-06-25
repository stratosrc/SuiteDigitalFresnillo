from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonReportRow:
    rank: str
    name: str
    position: str
    email: str
    start_date: str


@dataclass(frozen=True)
class AreaReportData:
    name: str
    personnel: list[PersonReportRow]


@dataclass(frozen=True)
class DirectoryReportData:
    title: str
    period: str
    areas: list[AreaReportData]


__all__ = [
    "AreaReportData",
    "DirectoryReportData",
    "PersonReportRow",
]
