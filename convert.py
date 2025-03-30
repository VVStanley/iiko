import csv
import glob
import os
import shutil
from typing import Dict, List
from dataclasses import asdict, fields
from collections import defaultdict
from models import (
    ORGS,
    PHONES,
    BaseParceError,
    RowExternal,
    RowOrigin,
    RowOutput,
)


# Внешние данные, путь к папке
EXTERNAL_PATH = ".\\external\\*.csv"
# EXTERNAL_PATH = "./external/*.csv"

# Наши данные с iiko
ORIGIN_PATH = ".\\origin.csv"
# ORIGIN_PATH = "./origin.csv"

# Вывод найденных файлов
OUTPUT_PATH = ".\\output\\"
# OUTPUT_PATH = "./output/"


def _origin_data() -> List[RowOrigin]:
    with open(ORIGIN_PATH, mode="r", encoding="UTF-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        return [RowOrigin.from_csv(row) for row in reader]


def _clear_folder(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def _get_file_name(file_path: str) -> str:
    name = file_path.split("\\")[-1]
    # name = file_path.split("/")[-1]
    return name


def _get_org_names(file_name: str) -> str:
    return file_name.split(".")[0].split("_")[-1]


def save_data(outputs: Dict[str, List[RowOutput]]) -> None:
    for file_name, rows in outputs.items():
        with open(f"{OUTPUT_PATH}{file_name}", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[f.name for f in fields(RowOutput)], delimiter=";")
            writer.writeheader()
            for row in rows:
                writer.writerow(asdict(row))


PHONE_DIGINT = 11 + 1
PHONE_DIGINT_PREFIX = 5


def calc_phones() -> None:
    for org_name, org_names in ORGS.items():
        org_phones = [org.phone for org in _origin_data() if org.org == org_names.origin]
        PREFIX = PHONES.get(org_name)
        number = max(int(phone[PHONE_DIGINT_PREFIX + 1 :]) for phone in org_phones) + 1
        zerows = (PHONE_DIGINT - PHONE_DIGINT_PREFIX - len(str(number))) * "0"
        PHONES[org_name] = int(f"{PREFIX}{zerows}{number}")


def next_phone(org_name) -> str:
    phone = PHONES[org_name]
    PHONES[org_name] = PHONES[org_name] + 1
    return phone


def convert() -> None:
    map_active_origin_employees: Dict[str, RowOrigin] = {}
    map_deactive_origin_employees: Dict[str, RowOrigin] = {}
    deleted_cards = []
    for emp in _origin_data():
        if emp.magnet_card.active:
            map_active_origin_employees.update({emp.magnet_card.active: emp})
            if emp.magnet_card.deleted:
                for del_card in emp.magnet_card.deleted:
                    map_deactive_origin_employees.update({del_card: emp})
        else:
            deleted_cards.append(emp.magnet_card.deleted)

    outputs = defaultdict(list)

    all_external_emp_card_finds = []

    for file_path in glob.glob(EXTERNAL_PATH):

        with open(file_path, mode="r", encoding="windows-1251") as file:
            file_name = _get_file_name(file_path)
            reader = csv.reader(file)

            for raw_row in reader:
                row = RowExternal.from_row(raw_row)
                all_external_emp_card_finds.append(row.number)
                if row.number not in map_active_origin_employees and row.number not in deleted_cards:
                    if row.number in map_deactive_origin_employees:
                        outputs[file_name].append(
                            RowOutput.from_externel(
                                phone=map_deactive_origin_employees[row.number].phone,
                                row=row,
                                is_deleted=True,
                            )
                        )
                    else:
                        outputs[file_name].append(
                            RowOutput.from_externel(phone=next_phone(_get_org_names(file_name)), row=row)
                        )

    file_name = "НЕ_найденные_у_них.csv"
    not_founds_external_emp = {file_name: []}
    for origin_emp_card in map_active_origin_employees.keys():
        if origin_emp_card not in all_external_emp_card_finds:
            not_founds_external_emp[file_name].append(
                RowOutput.from_origin(emp=map_active_origin_employees.get(origin_emp_card))
            )

    save_data(outputs)
    save_data(not_founds_external_emp)


if __name__ == "__main__":
    _clear_folder(OUTPUT_PATH)

    calc_phones()

    try:
        convert()
    except BaseParceError as e:
        print("НЕ УДАЛОСЬ СПАРСИТЬ ФАИЛ, ОШИБКА -")
        print(str(e))
