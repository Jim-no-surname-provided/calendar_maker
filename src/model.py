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
class ImageAsset:
    path: str | None = None
    crop_left: float = 0.0
    crop_top: float = 0.0
    crop_right: float = 1.0
    crop_bottom: float = 1.0


@dataclass
class DaySchedule:
    day: WeekDay
    is_rest_day: bool = False
    image: ImageAsset = field(default_factory=ImageAsset)
    title: str = ""
    platform: Platform = Platform.TWITCH
    collab_members: list[CollabMember] = field(default_factory=list)
    time_text: str = ""


@dataclass
class CalendarModel:
    date_range: str = ""
    fanart: ImageAsset = field(default_factory=ImageAsset)
    fanart_artist: str = ""
    days: dict[WeekDay, DaySchedule] = field(default_factory=dict)