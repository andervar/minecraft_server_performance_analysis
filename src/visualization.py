import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Plot the results from a csv
def plot_response_variables(filename, t):
    df = pd.read_csv(filename)

    # Columns to plot
    variables = [
        ("tps", "TPS (Ticks Per Second)"),
        ("cpu_usage", "CPU Usage (%)"),
        ("ram_usage", "RAM Usage (MB)"),
        ("avg_ping", "Average Latency (ms)"),
    ]

    # If the date column exists, parse it as datetime for better x-axis
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    for var, label in variables:
        if var in df.columns:
            plt.figure(figsize=(10, 4))
            plt.plot(df['date'], df[var], marker='o', linestyle='-')
            plt.title(f'{label} - Tratamiento {t}')
            plt.xlabel('Time')
            plt.ylabel(label)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        else:
            print(f"Column '{var}' not found in the CSV.")

if __name__ == "__main__":
    plot_response_variables("data\\processed\\response_variables\\T1_response_variables_treatment1.csv", 1)
    plot_response_variables("data\\processed\\response_variables\\T2_response_variables_treatment2.csv", 2)
    plot_response_variables("data\\processed\\response_variables\\T3_response_variables_treatment3.csv", 3)
    plot_response_variables("data\\processed\\response_variables\\T4_response_variables_treatment4.csv", 4)
    plot_response_variables("data\\processed\\response_variables\\T5_response_variables_treatment5.csv", 5)
    plot_response_variables("data\\processed\\response_variables\\T6_response_variables_treatment6.csv", 6)
    plot_response_variables("data\\processed\\response_variables\\T7_response_variables_treatment7.csv", 7)