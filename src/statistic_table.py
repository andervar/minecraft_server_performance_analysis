import pandas as pd
import os
from datetime import datetime

def analyze_treatment_stats(filename):
    """
    Calculate comprehensive statistics for a treatment file
    """
    try:
        df = pd.read_csv(filename)
        if df.empty:
            return None
        
        stats = {
            'treatment': df['treatment'].iloc[0] if 'treatment' in df.columns else 'Unknown',
            'tps_min': df['tps'].min(),
            'tps_max': df['tps'].max(),
            'tps_mean': df['tps'].mean(),
            'cpu_min': df['cpu_usage'].min(),
            'cpu_max': df['cpu_usage'].max(),
            'cpu_mean': df['cpu_usage'].mean(),
            'ram_min': df['ram_usage'].min(),
            'ram_max': df['ram_usage'].max(),
            'ram_mean': df['ram_usage'].mean(),
        }
        
        return stats
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None

def create_summary_table():
    """
    Create a comprehensive summary table for all treatments
    """
    # Treatment files
    treatment_files = [
        "data/processed/response_variables/T1_response_variables_treatment1.csv",
        "data/processed/response_variables/T2_response_variables_treatment2.csv", 
        "data/processed/response_variables/T3_response_variables_treatment3.csv",
        "data/processed/response_variables/T4_response_variables_treatment4.csv",
        "data/processed/response_variables/T5_response_variables_treatment5.csv",
        "data/processed/response_variables/T6_response_variables_treatment6.csv",
        "data/processed/response_variables/T7_response_variables_treatment7.csv"
    ]
    
    # Collect statistics for all treatments
    all_stats = []
    
    for filename in treatment_files:
        if os.path.exists(filename):
            stats = analyze_treatment_stats(filename)
            if stats:
                all_stats.append(stats)
        else:
            print(f"Warning: File not found {filename}")
    
    if not all_stats:
        print("No valid data found!")
        return None
        
    # Create DataFrame
    df_summary = pd.DataFrame(all_stats)
    
    # Round values for better presentation
    numeric_columns = ['tps_min', 'tps_max', 'tps_mean', 'cpu_min', 'cpu_max', 'cpu_mean', 
                      'ram_min', 'ram_max', 'ram_mean']
    for col in numeric_columns:
        if col in df_summary.columns:
            df_summary[col] = df_summary[col].round(2)
    
    return df_summary

def export_to_markdown(df_summary, output_file="treatment_summary_table.md"):
    """
    Export the summary table to a Markdown file
    """
    if df_summary is None or df_summary.empty:
        print("No data to export!")
        return
    
    # Create markdown content
    markdown_content = f"""# Minecraft Server Performance Analysis - Treatment Summary

## Performance Metrics Summary Table

| Tratamiento | TPS Min | TPS Max | TPS Mean | CPU Min | CPU Max | CPU Mean | RAM Min | RAM Max | RAM Mean |
|-------------|---------|---------|----------|---------|---------|----------|---------|---------|----------|
"""
    
    # Add data rows
    for _, row in df_summary.iterrows():
        markdown_content += f"| {row['treatment']} | {row['tps_min']} | {row['tps_max']} | {row['tps_mean']} | {row['cpu_min']} | {row['cpu_max']} | {row['cpu_mean']} | {row['ram_min']:.0f} | {row['ram_max']:.0f} | {row['ram_mean']:.0f} |\n"

    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"\nSummary table exported to: {output_file}")
        print(f"Analyzed {len(df_summary)} treatments")
        return output_file
    except Exception as e:
        print(f"Error writing markdown file: {e}")
        return None

def print_console_table(df_summary):
    """
    Print a nicely formatted table to console
    """
    if df_summary is None or df_summary.empty:
        print("No data to display!")
        return
    
    print("\n" + "="*120)
    print("MINECRAFT SERVER PERFORMANCE ANALYSIS - TREATMENT SUMMARY")
    print("="*120)
    
    # Print the table with better formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    # Create a display version with shorter column names
    display_df = df_summary.copy()
    display_df = display_df.rename(columns={
        'treatment': 'Treatment',
        'tps_min': 'TPS Min',
        'tps_max': 'TPS Max', 
        'tps_mean': 'TPS Mean',
        'cpu_min': 'CPU Min',
        'cpu_max': 'CPU Max',
        'cpu_mean': 'CPU Mean',
        'ram_min': 'RAM Min',
        'ram_max': 'RAM Max',
        'ram_mean': 'RAM Mean'
    })
    
    print(display_df.to_string(index=False))
    print("="*120)

def generate_table_and_markdown():
    """
    Main function to generate both console table and markdown file
    """
    print("Starting Minecraft Server Performance Analysis...")
    
    # Create comprehensive summary table
    print("\nCreating Summary Table...")
    summary_df = create_summary_table()
    
    if summary_df is not None:
        # Print to console
        print_console_table(summary_df)
        
        # Export to Markdown
        markdown_file = export_to_markdown(summary_df)
        
        if markdown_file:
            print(f"\nAnalysis complete!")
            print(f"Markdown table saved as: {markdown_file}")
            print(f"You can open the .md file to view the formatted table")
            return True
    else:
        print("Failed to create summary table")
        return False

if __name__ == "__main__":
    generate_table_and_markdown()
