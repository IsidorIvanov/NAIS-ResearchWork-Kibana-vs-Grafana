#!/usr/bin/env python3
"""
Pokretanje:
    pip install -r requirements.txt
    python load_data_db/load_data.py --recreate-index
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_CSV_PATH = PROJECT_ROOT / "input" / "access_logs_merged.csv"

REQUIRED_COLUMNS = [
    "timestamp",
    "method",
    "path",
    "status_code",
    "response_time_ms",
    "bytes_sent",
    "user_agent",
    "ip_address",
    "referrer",
    "name",
    "region",
    "role",
]

# Mapiranje indeksa je bitno da Kibana i Grafana pravilno prepoznaju tipove.
INDEX_MAPPINGS = {
    "properties": {
        "timestamp": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
        "server_name": {"type": "keyword"},
        "region": {"type": "keyword"},
        "role": {"type": "keyword"},
        "method": {"type": "keyword"},
        "path": {"type": "keyword"},
        "status_code": {"type": "integer"},
        "status_class": {"type": "keyword"},
        "response_time_ms": {"type": "integer"},
        "bytes_sent": {"type": "long"},
        "user_agent": {
            "type": "text",
            "fields": {"raw": {"type": "keyword", "ignore_above": 512}},
        },
        "ip_address": {"type": "ip"},
        "referrer": {"type": "keyword"},
    }
}


@dataclass(frozen=True)
class Settings:
    es_url: str
    index: str
    csv_path: Path
    chunk_size: int
    max_errors: int
    kibana_url: str
    grafana_url: str


def status_class(code: int) -> str:
    return f"{code // 100}xx"


def require_module(module_name: str, package_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"Nedostaje Python paket '{package_name}'. "
            "Instaliraj dependency-je komandom: pip install -r requirements.txt"
        ) from exc


def load_elasticsearch_modules() -> tuple[type[Any], ModuleType]:
    elasticsearch_module = require_module("elasticsearch", "elasticsearch")
    helpers_module = require_module("elasticsearch.helpers", "elasticsearch")
    return elasticsearch_module.Elasticsearch, helpers_module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ucitaj access_logs_merged.csv u Elasticsearch indeks."
    )
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Obrisi postojeci indeks i kreiraj ga ponovo pre importa.",
    )
    parser.add_argument(
        "--csv",
        help="Putanja do CSV fajla. Default: ACCESS_LOGS_CSV iz .env.",
    )
    parser.add_argument(
        "--index",
        help="Naziv Elasticsearch indeksa. Default: ELASTICSEARCH_INDEX iz .env.",
    )
    parser.add_argument(
        "--es-url",
        help="Elasticsearch URL. Default: ELASTICSEARCH_URL iz .env.",
    )
    parser.add_argument("--chunk-size", type=int, help="Velicina bulk chunk-a.")
    parser.add_argument("--max-errors", type=int, help="Koliko gresaka prikazati u izvestaju.")
    return parser.parse_args()


def positive_int(value: int | str | None, default: int, name: str) -> int:
    if value is None or value == "":
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} mora biti ceo broj, dobijeno: {value!r}") from exc

    if parsed <= 0:
        raise SystemExit(f"{name} mora biti veci od 0, dobijeno: {parsed}")

    return parsed


def resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def load_settings(args: argparse.Namespace) -> Settings:
    dotenv_module = require_module("dotenv", "python-dotenv")
    dotenv_module.load_dotenv(ENV_PATH)

    elasticsearch_port = os.getenv("ELASTICSEARCH_PORT", "9200")
    kibana_port = os.getenv("KIBANA_PORT", "5601")
    grafana_port = os.getenv("GRAFANA_PORT", "3000")

    csv_value = args.csv or os.getenv("ACCESS_LOGS_CSV") or str(DEFAULT_CSV_PATH)

    return Settings(
        es_url=(
            args.es_url
            or os.getenv("ELASTICSEARCH_URL")
            or f"http://localhost:{elasticsearch_port}"
        ),
        index=args.index or os.getenv("ELASTICSEARCH_INDEX", "web-logs"),
        csv_path=resolve_project_path(csv_value),
        chunk_size=positive_int(
            args.chunk_size or os.getenv("LOAD_DATA_CHUNK_SIZE"),
            default=1000,
            name="LOAD_DATA_CHUNK_SIZE",
        ),
        max_errors=positive_int(
            args.max_errors or os.getenv("LOAD_DATA_MAX_ERRORS"),
            default=5,
            name="LOAD_DATA_MAX_ERRORS",
        ),
        kibana_url=os.getenv("KIBANA_URL", f"http://localhost:{kibana_port}"),
        grafana_url=os.getenv("GRAFANA_URL", f"http://localhost:{grafana_port}"),
    )


def validate_csv_header(csv_path: Path) -> list[str]:
    if not csv_path.exists():
        raise SystemExit(f"CSV fajl ne postoji: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing_columns:
        raise SystemExit("CSV nema obavezne kolone: " + ", ".join(missing_columns))

    return fieldnames


def parse_int(row: dict[str, str], column: str, line_number: int) -> int:
    value = (row.get(column) or "").strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Red {line_number}: kolona '{column}' mora biti ceo broj, dobijeno {value!r}"
        ) from exc


def make_document(row: dict[str, str], line_number: int) -> dict[str, object]:
    code = parse_int(row, "status_code", line_number)

    return {
        "timestamp": row["timestamp"],
        "server_name": row["name"],
        "region": row["region"],
        "role": row["role"],
        "method": row["method"],
        "path": row["path"],
        "status_code": code,
        "status_class": status_class(code),
        "response_time_ms": parse_int(row, "response_time_ms", line_number),
        "bytes_sent": parse_int(row, "bytes_sent", line_number),
        "user_agent": row["user_agent"],
        "ip_address": row["ip_address"],
        "referrer": None if row["referrer"] == "-" else row["referrer"],
    }


def document_id(row: dict[str, str], row_number: int) -> str:
    fingerprint = "|".join(row.get(column, "") for column in REQUIRED_COLUMNS)
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"access-log-{row_number}-{digest}"


def iter_actions(
    csv_path: Path,
    index: str,
    stats: dict[str, int],
    row_errors: list[str],
    max_errors: int,
):
    with csv_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for line_number, row in enumerate(reader, start=2):
            row_number = line_number - 1
            stats["rows_read"] += 1

            try:
                source = make_document(row, line_number)
            except ValueError as exc:
                stats["rows_skipped"] += 1
                if len(row_errors) < max_errors:
                    row_errors.append(str(exc))
                continue

            yield {
                "_op_type": "index",
                "_index": index,
                "_id": document_id(row, row_number),
                "_source": source,
            }


def connect_to_elasticsearch(es_url: str, elasticsearch_client: type[Any]) -> Any:
    es = elasticsearch_client(es_url, request_timeout=60)

    try:
        if not es.ping():
            raise RuntimeError("ping nije uspeo")
        info = es.info()
    except Exception as exc:
        raise SystemExit(
            f"Elasticsearch nije dostupan na {es_url}. "
            "Proveri da li je pokrenut `docker compose up -d` i da li je servis zdrav."
        ) from exc

    version = info.get("version", {}).get("number", "nepoznata")
    print(f"Elasticsearch je dostupan: {es_url} (verzija {version})")
    return es


def ensure_index(es: Any, index: str, recreate_index: bool) -> None:
    if es.indices.exists(index=index):
        if recreate_index:
            es.indices.delete(index=index)
            print(f"Obrisan postojeci indeks '{index}'")
        else:
            print(
                f"Indeks '{index}' vec postoji. "
                "Postojeci dokumenti se ne brisu; koristi --recreate-index za cist import."
            )
            return

    es.indices.create(index=index, mappings=INDEX_MAPPINGS)
    print(f"Kreiran indeks '{index}' sa mapiranjem")


def import_documents(
    es: Any,
    settings: Settings,
    helpers_module: ModuleType,
) -> tuple[int, int, dict[str, int], list[str]]:
    stats = {"rows_read": 0, "rows_skipped": 0}
    row_errors: list[str] = []
    bulk_errors: list[str] = []
    success_count = 0
    failure_count = 0

    actions = iter_actions(
        csv_path=settings.csv_path,
        index=settings.index,
        stats=stats,
        row_errors=row_errors,
        max_errors=settings.max_errors,
    )

    try:
        for ok, item in helpers_module.streaming_bulk(
            es.options(request_timeout=120),
            actions,
            chunk_size=settings.chunk_size,
            raise_on_error=False,
            raise_on_exception=False,
        ):
            if ok:
                success_count += 1
                continue

            failure_count += 1
            if len(bulk_errors) < settings.max_errors:
                bulk_errors.append(json.dumps(item, ensure_ascii=False))
    except Exception as exc:
        raise SystemExit(f"Bulk import nije uspeo: {exc}") from exc

    errors = row_errors + bulk_errors
    return success_count, failure_count, stats, errors


def print_summary(
    settings: Settings,
    success_count: int,
    failure_count: int,
    stats: dict[str, int],
    errors: list[str],
    final_count: int,
) -> None:
    print("\nRezime importa")
    print(f"  CSV fajl: {settings.csv_path}")
    print(f"  Indeks: {settings.index}")
    print(f"  Procitano redova: {stats['rows_read']}")
    print(f"  Ucitano dokumenata: {success_count}")
    print(f"  Preskoceno redova: {stats['rows_skipped']}")
    print(f"  Bulk gresaka: {failure_count}")
    print(f"  Dokumenata u indeksu posle importa: {final_count}")

    if errors:
        print("\nPrve greske:")
        for error in errors[: settings.max_errors]:
            print(f"  - {error}")

    print("\nSledece:")
    print(
        f"  Kibana:  {settings.kibana_url} -> "
        f"Data View nad '{settings.index}' (time field: timestamp)"
    )
    print(
        f"  Grafana: {settings.grafana_url} -> "
        f"Elasticsearch data source za indeks '{settings.index}'"
    )


def main() -> None:
    args = parse_args()
    settings = load_settings(args)
    elasticsearch_client, helpers_module = load_elasticsearch_modules()

    print("Podesavanja importa")
    print(f"  Elasticsearch URL: {settings.es_url}")
    print(f"  Indeks: {settings.index}")
    print(f"  CSV fajl: {settings.csv_path}")
    print(f"  Chunk size: {settings.chunk_size}")
    print(f"  Recreate index: {args.recreate_index}")

    columns = validate_csv_header(settings.csv_path)
    print("CSV validacija prosla. Kolone:", ", ".join(columns))

    es = connect_to_elasticsearch(settings.es_url, elasticsearch_client)
    ensure_index(es, settings.index, recreate_index=args.recreate_index)

    success_count, failure_count, stats, errors = import_documents(
        es,
        settings,
        helpers_module,
    )

    es.indices.refresh(index=settings.index)
    final_count = es.count(index=settings.index)["count"]
    print_summary(settings, success_count, failure_count, stats, errors, final_count)

    if stats["rows_skipped"] or failure_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
