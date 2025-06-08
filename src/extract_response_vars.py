import sqlite3
import pandas as pd
from datetime import datetime
import os
import pytz

db_path = "data/raw/database.db"
local_tz = pytz.timezone('America/Costa_Rica')

treatments = [
    ("T1", 19, 40, 19, 50),
    ("T2", 20, 38, 20, 48),
    ("T3", 19, 56, 20, 6),
    ("T4", 21, 9, 21, 19),
    ("T5", 20, 9, 20, 19),
    ("T6", 21, 32, 21, 42),
    ("T7", 20, 22, 20, 32),
    ("T8", 21, 49, 21, 59),
    ("T9", 22, 4, 22, 14),
]

output_folder = "data/processed/response_variables"
os.makedirs(output_folder, exist_ok=True)

for name, sh, sm, eh, em in treatments:
    local_start = local_tz.localize(datetime(2025, 6, 7, sh, sm, 0))
    local_end = local_tz.localize(datetime(2025, 6, 7, eh, em, 0))
    start_time = int(local_start.astimezone(pytz.utc).timestamp() * 1000)
    end_time = int(local_end.astimezone(pytz.utc).timestamp() * 1000)
    print(f"\n{name}: {local_start} -> {local_end}")

    conn = sqlite3.connect(db_path)

    # Main query for TPS, CPU, RAM
    query = """
    SELECT
        tps.date,
        tps.tps,
        tps.cpu_usage,
        tps.ram_usage
    FROM plan_tps tps
    WHERE tps.date BETWEEN ? AND ?
    ORDER BY tps.date ASC
    """
    params = (start_time, end_time)
    df = pd.read_sql_query(query, conn, params=params)
    df["date"] = pd.to_datetime(df["date"], unit="ms").dt.tz_localize('UTC').dt.tz_convert('America/Costa_Rica')

    # Latency
    query_ping = """
    SELECT date, avg(avg_ping) as avg_ping
    FROM plan_ping
    WHERE date BETWEEN ? AND ?
    GROUP BY date
    ORDER BY date ASC
    """
    df_ping = pd.read_sql_query(query_ping, conn, params=params)
    df_ping["date"] = pd.to_datetime(df_ping["date"], unit="ms").dt.tz_localize('UTC').dt.tz_convert('America/Costa_Rica')
    df = pd.merge_asof(
        df.sort_values("date"), df_ping.sort_values("date"),
        on="date", direction="backward"
    )
    conn.close()

    output_path = os.path.join(output_folder, f"{name}_response_variables.csv")
    df.to_csv(output_path, index=False)
    print(f"Exported: {output_path}")