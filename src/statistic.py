import pandas as pd

def analyze_response_variables(filename):
    """
    Analyze response variables from a CSV file and print summary statistics.
    This function reads a CSV file containing various response variables and prints
    summary statistics for each specified variable.
    """
    print("-" * 50)
    print(f"Analyzing response variables from: {filename}\n")
    # Load your CSV file with all response variables
    df = pd.read_csv(filename)

    # List all columns you want summary stats for
    variables = [
        'tps',           # Ticks Per Second
        'cpu_usage',     # CPU Usage (total, per-core analysis requires more columns)
        'ram_usage',  # RAM usage in MB
        'players_online', # Number of players online
    ]

    for var in variables:
        if var in df.columns:
            print(f"--- {var} ---")
            print(df[var].describe())
            print()
        else:
            print(f"Column '{var}' not found in CSV.\n")

if __name__ == "__main__":
    analyze_response_variables("data/processed/response_variables/T1_response_variables_treatment1.csv")
    analyze_response_variables("data/processed/response_variables/T2_response_variables_treatment2.csv")
    analyze_response_variables("data/processed/response_variables/T3_response_variables_treatment3.csv")
    analyze_response_variables("data/processed/response_variables/T4_response_variables_treatment4.csv")
    analyze_response_variables("data/processed/response_variables/T5_response_variables_treatment5.csv")
    analyze_response_variables("data/processed/response_variables/T6_response_variables_treatment6.csv")
    analyze_response_variables("data/processed/response_variables/T7_response_variables_treatment7.csv")