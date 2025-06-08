import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/processed/response_variables/T1_response_variables.csv')

# List the columns you want to plot
variables = [
    ("tps", "TPS (Ticks Per Second)"),
    ("cpu_usage", "CPU Usage (%)"),
    ("ram_usage", "RAM Usage (MB)"),
    ("avg_ping", "Average Latency (ms)"),
    # Add more variables here if needed
]

# If the date column exists, parse it as datetime for better x-axis
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])

for var, label in variables:
    if var in df.columns:
        plt.figure(figsize=(10, 4))
        plt.plot(df['date'], df[var], marker='o', linestyle='-')
        plt.title(f'{label} - Tratamiento 1')
        plt.xlabel('Time')
        plt.ylabel(label)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    else:
        print(f"Column '{var}' not found in the CSV.")