from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PersonReportRow:
    rank: str
    name: str
    position: str
    start_date: str


@dataclass(frozen=True, slots=True)
class AreaReportData:
    name: str
    personnel: list[PersonReportRow]


@dataclass(frozen=True, slots=True)
class DirectoryReportData:
    title: str
    period: str
    areas: list[AreaReportData]


__all__ = [
    "AreaReportData",
    "DirectoryReportData",
    "PersonReportRow",
]
