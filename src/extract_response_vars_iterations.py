import sqlite3
import pandas as pd
from datetime import datetime
import os
import pytz

# === CONFIGURATION ===
db_path = "data/raw/database.db"
local_tz = pytz.timezone('America/Costa_Rica')

# Format: (iteration_number, start_year, start_month, start_day, start_hour, start_minute,
#                       end_year,   end_month,   end_day,   end_hour,   end_minute)
# ========== TRATAMIENTO T1 ==========
iterations1 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 11, 18, 0, 2025, 6, 12, 6, 0),
]

# ========== TRATAMIENTO T2 ==========
iterations2 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 22, 21, 2, 2025, 6, 28, 16, 10),
]

# ========== TRATAMIENTO T3 ==========
iterations3 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 12, 23, 0, 2025, 6, 14, 16, 0),
    ("2", 2025, 6, 21, 22, 20, 2025, 6, 22, 12, 0),
]

# ========== TRATAMIENTO T4 ==========
iterations4 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    # ("1", 2025, 6, 19, 11, 0, 2025, 6, 19, 11, 0),  # Eliminado - comentado
    ("1", 2025, 6, 21, 18, 0, 2025, 6, 21, 22, 0),
]

# ========== TRATAMIENTO T5 ==========
iterations5 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 14, 16, 0, 2025, 6, 19, 10, 0),
    ("2", 2025, 6, 21, 15, 0, 2025, 6, 21, 18, 0),
]

# ========== TRATAMIENTO T6 ==========
iterations6 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 20, 21, 9, 2025, 6, 21, 15, 0),
    ("2", 2025, 6, 22, 15, 2, 2025, 6, 22, 18, 0),
    ("3", 2025, 6, 28, 16, 10, 2025, 6, 30, 23, 10),  # En progreso - sin fecha fin
]

# ========== TRATAMIENTO T7 ==========
iterations7 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    # ("1", 2025, 6, 12, 9, 0, 2025, 6, 12, 23, 0),   # Eliminado por mod - comentado
    ("1", 2025, 6, 20, 18, 9, 2025, 6, 20, 20, 59),
    ("2", 2025, 6, 22, 18, 0, 2025, 6, 22, 21, 0),
]

def  extract_response_variables(filename, iterations, treatment_number):
    """
    Extracts response variables from the database for specified iterations.
    Each iteration is defined by a start and end time.
    """

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
            print(f"Warning: No players online during Iteration {iteration} (T{treatment_number})")

        # Add treatment and iteration columns
        df["treatment"] = f"T{treatment_number}"
        df["iteration"] = iteration

        all_data.append(df)
        conn.close()

    # Combine all iterations into a single DataFrame
    final_df = pd.concat(all_data, ignore_index=True)

    # Export to a single CSV file
    output_path = os.path.join(output_folder, f"T{treatment_number}_response_variables_"+ filename + ".csv")
    final_df.to_csv(output_path, index=False)
    print(f"\nFinal CSV exported: {output_path}")

if __name__ == "__main__":
    # Extract response variables for each treatment
    extract_response_variables("treatment1", iterations1, 1)
    extract_response_variables("treatment2", iterations2, 2)
    extract_response_variables("treatment3", iterations3, 3)
    extract_response_variables("treatment4", iterations4, 4)
    extract_response_variables("treatment5", iterations5, 5)
    extract_response_variables("treatment6", iterations6, 6)
    extract_response_variables("treatment7", iterations7, 7)
