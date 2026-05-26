from dataclasses import dataclass, field
from enum import Enum


class WeekDay(Enum):
    MONDAY = "Lunes"
    TUESDAY = "Martes"
    WEDNESDAY = "Miércoles"
    THURSDAY = "Jueves"
    FRIDAY = "Viernes"
    SATURDAY = "Sábado"
    SUNDAY = "Domingo"


class Platform(Enum):
    TWITCH = "twitch"
    YOUTUBE = "youtube"


@dataclass
class CollabMember:
    name: str = ""
    color: str = "#ffffff"


@dataclass
class DaySchedule:
    day: WeekDay
    is_rest_day: bool = False
    image_path: str | None = None
    title: str = ""
    platform: Platform = Platform.TWITCH
    collab_members: list[CollabMember] = field(default_factory=list)
    time_text: str = ""


@dataclass
class CalendarModel:
    date_range: str = ""
    fanart_image_path: str | None = None
    fanart_artist: str = ""
    days: dict[WeekDay, DaySchedule] = field(default_factory=dict)
