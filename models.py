from collections import namedtuple
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


OrgNames = namedtuple("OrgNames", ["external", "origin"])

ORGS: Dict[str, OrgNames] = {
    # "Djinatec": OrgNames(external="ДЖИНАТЭК ООО", origin="ДЖИНАТЭК ООО"),
    # "FarmaFond": OrgNames(external="ООО \"ФАРМАФОНД\"", origin="ФАРМАФОНД ООО"),
    # "FS": OrgNames(external="Фармасинтез", origin="Фармасинтез ООО"),
    # "Primafarm": OrgNames(external="Примафарм", origin="Примафарм ООО"),
    # "Profarm": OrgNames(external="Профарм", origin="Профарм ООО"),
    # "PuniaNV": OrgNames(external="ИП ПунияНВ", origin="Пуния НВ ИП"),
    # "PuniaVS": OrgNames(external="ИП ПунияВС", origin="Пуния ВС ИП"),
    # "RiverPark": OrgNames(external="РИВЕР ПАРК ООО", origin="РИВЕР ПАРК ООО"),
    "Sivalab": OrgNames(external="ООО \"СИВИлаб\"", origin="СИВИлаб ООО"),
}


PHONES: Dict[str, str] = {
    # "Djinatec" : 7921,
    # "FarmaFond" : 7922,
    # "FS": 7923,
    # "Primafarm" : 7924,
    # "Profarm" : 7925,
    # "PuniaNV" : 7929,
    # "PuniaVS" : 7930,
    # "RiverPark" : 7926,
    "Sivalab" : 7927,
}


class BaseParceError(Exception):
    pass


class GetRowOriginError(BaseParceError):
    pass


def origin_orgs() -> List[str]:
    return [org.origin for org in ORGS.values()]


@dataclass
class RowExternal:
    number: str
    date: str
    two: str
    type_: str
    code: str
    fio: str
    two2: str
    amount: str
    skip1: Any
    skip2: Any
    skip3: Any
    org: str
    skip5: Any
    skip6: Any
    skip7: Any
    skip8: Any
    zero: str

    @property
    def first_name(self) -> str:
        return self.fio.split(" ")[1]

    @property
    def last_name(self) -> str:
        return self.fio.split(" ")[0]

    @property
    def middle_name(self) -> Optional[str]:
        ifo = self.fio.split(" ")
        return ifo[2] if len(ifo) > 2 else None

    @property
    def first_middle_name(self) -> str:
        return f"{self.first_name} {self.middle_name}"

    @classmethod
    def from_row(cls, row: List[Any]) -> "RowExternal":
        return cls(
            number=row[0],
            date=row[1],
            two=row[2],
            type_=row[3],
            code=row[4],
            fio=row[5],
            two2=row[6],
            amount=row[7],
            skip1=row[8],
            skip2=row[9],
            skip3=row[10],
            org=row[11],
            skip5=row[12],
            skip6=row[13],
            skip7=row[14],
            skip8=row[15],
            zero=row[16],
        )


@dataclass
class MCard:
    active: Optional[str]
    deleted: List

    @classmethod
    def from_magnet_cards(cls, magnet_cards: str) -> "MCard":
        active = None
        deleted = []
        if "," in magnet_cards:
            for card in magnet_cards.split(","):
                card = card.strip()
                if card.isdigit():
                    active = card
                else:
                    deleted.append(re.findall(r"\d+", card)[-1])
        else:
            if magnet_cards.isdigit():
                active = magnet_cards.strip()
            else:
                deleted = re.findall(r"\d+", magnet_cards)[-1]
        return cls(active=active, deleted=deleted)


@dataclass
class RowOrigin:
    phone: str
    fio: str
    magnet_card: MCard
    magnet_cards: str
    when_created: str
    guest_categories: str
    org: str
    category: str

    @staticmethod
    def _get_org(guest_categories: str) -> str:
        for cat in guest_categories.split(","):
            if cat.strip() in origin_orgs():
                return cat.strip()

    @staticmethod
    def _get_category(guest_categories: str) -> str:
        for cat in guest_categories.split(","):
            if "рублей" in cat:
                return cat.strip()

    @classmethod
    def from_csv(cls, row: dict) -> "RowOrigin":
        try:
            magnet_card = MCard.from_magnet_cards(row["MagnetCards"])
        except Exception as e:
            raise GetRowOriginError(f"\n!!! Не удалось спарсить карту из строки - {row}\n\n Error - {str(e)}")

        try:
            org = cls._get_org(row["GuestCategories"])
        except Exception as e:
            raise GetRowOriginError(f"\n!!! Не удалось спарсить организацию из строки - {row}\n\n Error - {str(e)}")

        try:
            category = cls._get_category(row["GuestCategories"])
        except Exception as e:
            raise GetRowOriginError(f"\n!!! Не удалось спарсить категорию из строки - {row}\n\n Error - {str(e)}")

        return cls(
            phone=row["PhoneNumber"],
            fio=row["Name"],
            magnet_card=magnet_card,
            magnet_cards=row["MagnetCards"],
            when_created=datetime.strptime(row["WhenCreated"], "%d.%m.%Y %H:%M:%S"),
            guest_categories=row["GuestCategories"],
            org=org,
            category=category,
        )


@dataclass
class RowOutput:
    phone: str
    track_1: str
    name: str
    last_name: str
    amount: str
    org: str

    @classmethod
    def from_externel(cls, phone: Optional[str], row: RowExternal, is_deleted: bool = False) -> "RowOutput":
        return cls(
            phone=phone,
            track_1=row.number if not is_deleted else f"{row.number}(удалена)",
            name=row.last_name,
            last_name=row.first_middle_name,
            amount=row.amount,
            org=row.org,
        )

    @classmethod
    def from_origin(cls, emp: RowOrigin) -> "RowOutput":
        return cls(
            phone=emp.phone,
            track_1=emp.magnet_card.active,
            name=emp.fio,
            last_name=emp.fio,
            amount=emp.category,
            org=emp.org,
        )
