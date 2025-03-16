import csv
import glob
import os
import shutil
from typing import Dict, List
from dataclasses import asdict, fields
from collections import defaultdict
from models import ORGS, PHONES, OrgNames, RowExternal, RowOrigin, RowOutput


# Внешние данные, путь к папке
EXTERNAL_PATH = "./external/*.csv"

# Наши данные с iiko
ORIGIN_PATH = "./origin.csv"

# Вывод найденных файлов
OUTPUT_PATH = "./output/"



def _origin_data() -> List[RowOrigin]:
    with open(ORIGIN_PATH, mode="r", encoding="UTF-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        return [RowOrigin.from_csv(row) for row in reader]


def _clear_folder(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def _get_file_name(file_path: str) -> str:
    return file_path.split("/")[-1]


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
        number = max(int(phone[PHONE_DIGINT_PREFIX + 1:]) for phone in org_phones) + 1
        zerows = (PHONE_DIGINT - PHONE_DIGINT_PREFIX - len(str(number)))*"0"
        PHONES[org_name] = int(f"{PREFIX}{zerows}{number}")


def next_phone(org_name) -> str:
    phone = PHONES[org_name]
    PHONES[org_name] = PHONES[org_name] + 1
    return phone


def convert() -> None:

    origin_data = _origin_data()
    magnet_nums = [d.magnet_number for d in origin_data if d.magnet_number]
    outputs = defaultdict(list)
    
    
    for file_path in glob.glob(EXTERNAL_PATH):

        with open(file_path, mode="r", encoding="windows-1251") as file:

            file_name = _get_file_name(file_path)
            reader = csv.reader(file)

            for raw_row in reader:
                row = RowExternal.from_row(raw_row)
                if row.number not in magnet_nums:
                    outputs[file_name].append(
                        RowOutput(
                            phone=next_phone(_get_org_names(file_name)),
                            track_1=row.number,
                            name=row.last_name,
                            last_name=row.first_middle_name,
                            amount=row.amount,
                            org=row.org
                        )
                    )
    save_data(outputs)



if __name__ == "__main__":
    _clear_folder(OUTPUT_PATH)
    calc_phones()
    convert()


