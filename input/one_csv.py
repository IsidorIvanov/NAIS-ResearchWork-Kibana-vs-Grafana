import pandas as pd
SERVERS_PATH = "servers.csv"
ACCESS_LOGS_PATH = "access_logs.csv"
OUTPUT_PATH = "access_logs_merged.csv"

servers = pd.read_csv(SERVERS_PATH)
access_logs = pd.read_csv(ACCESS_LOGS_PATH)

print(f"servers.csv: {len(servers)} redova, kolone: {list(servers.columns)}")
print(f"access_logs.csv: {len(access_logs)} redova, kolone: {list(access_logs.columns)}")

servers_renamed = servers.rename(columns={"id": "server_id"})

merged = access_logs.merge(servers_renamed, on="server_id", how="left")
merged = merged.drop(columns=["server_id"])
missing = merged["name"].isna().sum()
if missing > 0:
    print(f"WARNING: {missing} redova u access_logs.csv nema imena servera")
else:
    print(f"Uspješno spojeni podaci iz servers.csv i access_logs.csv")

merged.to_csv(OUTPUT_PATH, index=False)
print(f"Uspješno spremljeni podaci u {OUTPUT_PATH}")