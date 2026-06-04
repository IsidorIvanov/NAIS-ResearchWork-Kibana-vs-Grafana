from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "access_logs_merged.csv"
OUTPUT_PATH = BASE_DIR / "basic_info_dataset.md"


def add_section(report: list[str], title: str) -> None:
    report.append(f"\n## {title}")


def add_code_block(report: list[str], content: str) -> None:
    report.extend(["", "```text", content, "```"])


def add_top_values(df: pd.DataFrame, report: list[str], column: str, limit: int = 10) -> None:
    if column not in df.columns:
        return

    report.append(f"\n### Najčešće vrednosti za `{column}`")
    add_code_block(report, df[column].value_counts(dropna=False).head(limit).to_string())


def save_report(report: list[str]) -> None:
    content = "\n".join(report).strip() + "\n"
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(content)
    print(f"\nMarkdown izveštaj je sačuvan u: {OUTPUT_PATH}")


def main() -> None:
    df = pd.read_csv(DATASET_PATH)
    report = ["# Osnovne informacije o datasetu"]

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    add_section(report, "Osnovne informacije")
    report.append(f"- Fajl: `{DATASET_PATH.name}`")
    report.append(f"- Broj redova: `{len(df):,}`")
    report.append(f"- Broj kolona: `{len(df.columns):,}`")
    report.append(f"- Kolone: {', '.join(f'`{column}`' for column in df.columns)}")

    add_section(report, "Tipovi podataka")
    add_code_block(report, df.dtypes.to_string())

    add_section(report, "Kvalitet podataka")
    report.append(f"- Duplirani redovi: `{df.duplicated().sum():,}`")
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        report.append("- Nema nedostajućih vrednosti.")
    else:
        report.append("- Nedostajuće vrednosti po kolonama:")
        add_code_block(report, missing.to_string())

    if "timestamp" in df.columns:
        add_section(report, "Vremenski opseg")
        valid_timestamps = df["timestamp"].dropna()
        if valid_timestamps.empty:
            report.append("- Kolona `timestamp` nema validne datume.")
        else:
            report.append(f"- Od: `{valid_timestamps.min()}`")
            report.append(f"- Do: `{valid_timestamps.max()}`")
            report.append(f"- Broj dana u datasetu: `{valid_timestamps.dt.date.nunique():,}`")
            report.append("\n### Broj zahteva po danu")
            add_code_block(report, valid_timestamps.dt.date.value_counts().sort_index().to_string())

    add_section(report, "Numeričke metrike")
    numeric_columns = ["status_code", "response_time_ms", "bytes_sent"]
    existing_numeric_columns = [col for col in numeric_columns if col in df.columns]
    if existing_numeric_columns:
        add_code_block(report, df[existing_numeric_columns].describe().round(2).to_string())
    else:
        report.append("- Nema očekivanih numeričkih kolona.")

    if "response_time_ms" in df.columns:
        report.append("\n### Percentili vremena odziva (ms)")
        percentiles = df["response_time_ms"].quantile([0.5, 0.75, 0.9, 0.95, 0.99])
        add_code_block(report, percentiles.round(2).to_string())

    if "bytes_sent" in df.columns:
        total_mb = df["bytes_sent"].sum() / (1024 * 1024)
        average_kb = df["bytes_sent"].mean() / 1024
        report.append(f"- Ukupno poslato podataka: `{total_mb:.2f} MB`")
        report.append(f"- Prosečno po zahtevu: `{average_kb:.2f} KB`")

    add_section(report, "HTTP statusi")
    if "status_code" in df.columns:
        status_counts = df["status_code"].value_counts().sort_index()
        add_code_block(report, status_counts.to_string())

        total_requests = len(df)
        client_errors = df["status_code"].between(400, 499).sum()
        server_errors = df["status_code"].between(500, 599).sum()
        report.append(f"- 4xx greške: `{client_errors:,}` (`{client_errors / total_requests:.2%}`)")
        report.append(f"- 5xx greške: `{server_errors:,}` (`{server_errors / total_requests:.2%}`)")
    else:
        report.append("- Kolona `status_code` ne postoji.")

    add_section(report, "Najčešće kategorije")
    for column in ["method", "path", "user_agent", "ip_address", "referrer", "name", "region", "role"]:
        add_top_values(df, report, column)

    if {"name", "response_time_ms"}.issubset(df.columns):
        add_section(report, "Performanse po serveru")
        performance_by_server = (
            df.groupby("name")["response_time_ms"]
            .agg(["count", "mean", "median", "max"])
            .sort_values("mean", ascending=False)
            .round(2)
        )
        add_code_block(report, performance_by_server.to_string())

    if {"path", "status_code"}.issubset(df.columns):
        add_section(report, "Putanje sa najviše grešaka")
        error_rows = df[df["status_code"] >= 400]
        if error_rows.empty:
            report.append("- Nema zabeleženih 4xx/5xx grešaka.")
        else:
            add_code_block(report, error_rows["path"].value_counts().head(10).to_string())

    save_report(report)


if __name__ == "__main__":
    main()
