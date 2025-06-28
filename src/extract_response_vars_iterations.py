import sqlite3
import pandas as pd
from datetime import datetime
import os
import pytz

# === CONFIGURATION ===
db_path = "data/raw/database.db"
local_tz = pytz.timezone('America/Costa_Rica')
TREATMENT_NUMBER = 1  # Change if you're processing another treatment

# Format: (iteration_number, start_year, start_month, start_day, start_hour, start_minute,
#                       end_year,   end_month,   end_day,   end_hour,   end_minute)
iterations = [
   #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 11, 18, 00, 2025, 6, 12, 6, 00),
    # ("2", 2025, 6, 7, 20, 38, 2025, 6, 7, 20, 48),
    # ("3", 2025, 6, 7, 23, 55, 2025, 6, 8, 0, 5),  
]

# Output folder
output_folder = "data/processed/response_variables"
os.makedirs(output_folder, exist_ok=True)

# DataFrame to store all iterations
all_data = []

# Process each iteration
for iteration, sy, sM, sd, sh, sm, ey, eM, ed, eh, em in iterations:
    local_start = local_tz.localize(datetime(sy, sM, sd, sh, sm, 0))
    local_end = local_tz.localize(datetime(ey, eM, ed, eh, em, 0))
    start_time = int(local_start.astimezone(pytz.utc).timestamp() * 1000)
    end_time = int(local_end.astimezone(pytz.utc).timestamp() * 1000)

    print(f"Processing Iteration {iteration}: {local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}")

    conn = sqlite3.connect(db_path)

    # Query TPS, CPU, RAM, and players online
    query = """
    SELECT
        tps.date,
        tps.tps,
        tps.cpu_usage,
        tps.ram_usage,
        tps.players_online
    FROM plan_tps tps
    WHERE tps.date BETWEEN ? AND ?
    ORDER BY tps.date ASC
    """
    df = pd.read_sql_query(query, conn, params=(start_time, end_time))
    df["date"] = pd.to_datetime(df["date"], unit="ms").dt.tz_localize('UTC').dt.tz_convert(local_tz)

    # Query average ping
    query_ping = """
    SELECT date, avg(avg_ping) as avg_ping
    FROM plan_ping
    WHERE date BETWEEN ? AND ?
    GROUP BY date
    ORDER BY date ASC
    """
    df_ping = pd.read_sql_query(query_ping, conn, params=(start_time, end_time))
    df_ping["date"] = pd.to_datetime(df_ping["date"], unit="ms").dt.tz_localize('UTC').dt.tz_convert(local_tz)

    # Merge ping data with TPS data based on nearest previous timestamp
    df = pd.merge_asof(
        df.sort_values("date"),
        df_ping.sort_values("date"),
        on="date", direction="backward"
    )

    # Check for presence of players
    if df["players_online"].fillna(0).sum() == 0:
        print(f"Warning: No players online during Iteration {iteration} (T{TREATMENT_NUMBER})")

    # Add treatment and iteration columns
    df["treatment"] = f"T{TREATMENT_NUMBER}"
    df["iteration"] = iteration

    all_data.append(df)
    conn.close()

# Combine all iterations into a single DataFrame
final_df = pd.concat(all_data, ignore_index=True)

# Export to a single CSV file
output_path = os.path.join(output_folder, f"T{TREATMENT_NUMBER}_response_variables_iterations.csv")
final_df.to_csv(output_path, index=False)
print(f"\nFinal CSV exported: {output_path}")
