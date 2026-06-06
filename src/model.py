from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIR = PROJECT_ROOT / "resources"


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
    name: str = "JimberrDev"
    color: str = "#d9af18"


@dataclass
class ThumbnailModel:
    mask_path: str | Path
    path: str | Path | None = None
    opacity: float = 8.0
    crop_left: float = 0.0
    crop_top: float = 0.0
    crop_right: float = 1.0
    crop_bottom: float = 1.0


@dataclass
class DayModel:
    day: WeekDay
    thumbnail: ThumbnailModel
    is_rest_day: bool = False
    title: str = ""
    subtitle: str = ""
    platform: Platform = Platform.TWITCH
    collab_members: list[CollabMember] = field(default_factory=list)
    time_text: str = ""


@dataclass
class CalendarModel:
    date_range: str = ""
    fanart: ThumbnailModel = field(
        default_factory=lambda: ThumbnailModel(
            mask_path=RESOURCE_DIR / "masks" / "fanart.png",
        )
    )
    fanart_artist: str = ""
    days: dict[WeekDay, DayModel] = field(default_factory=lambda: {
        day: DayModel(day, ThumbnailModel(mask_path=RESOURCE_DIR / "masks" / (day.name + ".png")))
        for day in WeekDay
    })
