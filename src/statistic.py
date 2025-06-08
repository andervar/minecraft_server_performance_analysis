import pandas as pd

# Load your CSV file with all response variables
df = pd.read_csv('data/processed/response_variables/T1_response_variables.csv')

# List all columns you want summary stats for
variables = [
    'tps',           # Ticks Per Second
    'cpu_usage',     # CPU Usage (total, per-core analysis requires more columns)
    'ram_usage',  # RAM usage in MB
    'avg_ping',      # Average latency (ms)
]

for var in variables:
    if var in df.columns:
        print(f"--- {var} ---")
        print(df[var].describe())
        print()
    else:
        print(f"Column '{var}' not found in CSV.\n")