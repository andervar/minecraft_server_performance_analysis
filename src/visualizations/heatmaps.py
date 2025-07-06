import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob

def load_summary_data():
    """
    Load and calculate summary statistics from the actual CSV data files
    """
    # Get all CSV files
    data_files = glob.glob("../../data/processed/response_variables/T*_response_variables_*.csv")
    
    if not data_files:
        print("No data files found. Make sure you're running from the visualizations folder.")
        return None
    
    all_data = []
    for file in data_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    if not all_data:
        print("No valid data found.")
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Calculate summary statistics for each treatment
    treatments = sorted(combined_df['treatment'].unique())
    summary_data = []
    
    for treatment in treatments:
        treatment_data = combined_df[combined_df['treatment'] == treatment]
        
        if len(treatment_data) > 0:
            summary = {
                'treatment': treatment,
                'tps_min': treatment_data['tps'].min(),
                'tps_max': treatment_data['tps'].max(),
                'tps_mean': treatment_data['tps'].mean(),
                'cpu_min': treatment_data['cpu_usage'].min(),
                'cpu_max': treatment_data['cpu_usage'].max(),
                'cpu_mean': treatment_data['cpu_usage'].mean(),
                'ram_min': treatment_data['ram_usage'].min(),
                'ram_max': treatment_data['ram_usage'].max(),
                'ram_mean': treatment_data['ram_usage'].mean(),
            }
            summary_data.append(summary)
    
    if not summary_data:
        print("No summary data could be calculated.")
        return None
    
    df_summary = pd.DataFrame(summary_data)
    
    # Round values for better presentation
    numeric_columns = ['tps_min', 'tps_max', 'tps_mean', 'cpu_min', 'cpu_max', 'cpu_mean', 
                      'ram_min', 'ram_max', 'ram_mean']
    for col in numeric_columns:
        if col in df_summary.columns:
            df_summary[col] = df_summary[col].round(2)
    
    print(f"Loaded and calculated summary for treatments: {treatments}")
    print(f"Summary data shape: {df_summary.shape}")
    
    return df_summary

def create_performance_heatmap(df, save_path="heatmaps"):
    """
    Create a heatmap showing performance metrics across treatments
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Prepare data for heatmap (means only)
    heatmap_data = df[['treatment', 'tps_mean', 'cpu_mean', 'ram_mean']].copy()
    heatmap_data = heatmap_data.set_index('treatment')
    
    # Rename columns for better display
    heatmap_data.columns = ['TPS (Mean)', 'CPU % (Mean)', 'RAM MB (Mean)']
    
    # Normalize data for better visualization (0-1 scale)
    normalized_data = heatmap_data.copy()
    
    # For TPS: higher is better, so we keep as is (normalized 0-1)
    normalized_data['TPS (Mean)'] = (heatmap_data['TPS (Mean)'] - heatmap_data['TPS (Mean)'].min()) / (heatmap_data['TPS (Mean)'].max() - heatmap_data['TPS (Mean)'].min())
    
    # For CPU: lower is better, so we invert (1 - normalized value)
    normalized_data['CPU % (Mean)'] = 1 - ((heatmap_data['CPU % (Mean)'] - heatmap_data['CPU % (Mean)'].min()) / (heatmap_data['CPU % (Mean)'].max() - heatmap_data['CPU % (Mean)'].min()))
    
    # For RAM: lower is better, so we invert
    normalized_data['RAM MB (Mean)'] = 1 - ((heatmap_data['RAM MB (Mean)'] - heatmap_data['RAM MB (Mean)'].min()) / (heatmap_data['RAM MB (Mean)'].max() - heatmap_data['RAM MB (Mean)'].min()))
    
    # Create the heatmap
    plt.figure(figsize=(10, 8))
    
    # Raw values heatmap
    sns.heatmap(heatmap_data.T, annot=True, fmt='.2f', cmap='RdYlGn', 
                cbar_kws={'label': 'Performance Value'}, 
                linewidths=0.5, linecolor='white')
    
    plt.title('Performance Metrics Heatmap (Raw Values)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Treatment', fontsize=14, fontweight='bold')
    plt.ylabel('Metrics', fontsize=14, fontweight='bold')
    
    # Add note
    plt.figtext(0.5, 0.02, 'Note: For TPS higher is better, for CPU and RAM lower is better', 
                ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/performance_heatmap_raw.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()
    
    # Create normalized heatmap (performance score)
    plt.figure(figsize=(10, 8))
    
    sns.heatmap(normalized_data.T, annot=True, fmt='.3f', cmap='RdYlGn', 
                vmin=0, vmax=1, cbar_kws={'label': 'Performance Score (0-1)'}, 
                linewidths=0.5, linecolor='white')
    
    plt.title('Performance Score Heatmap (Normalized)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Treatment', fontsize=14, fontweight='bold')
    plt.ylabel('Metrics', fontsize=14, fontweight='bold')
    
    # Add note
    plt.figtext(0.5, 0.02, 'Note: Higher scores (green) indicate better performance across all metrics', 
                ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/performance_heatmap_normalized.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def create_range_heatmap(df, save_path="heatmaps"):
    """
    Create a heatmap showing the ranges (max-min) for each metric
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Calculate ranges
    range_data = pd.DataFrame({
        'treatment': df['treatment'],
        'TPS Range': df['tps_max'] - df['tps_min'],
        'CPU Range': df['cpu_max'] - df['cpu_min'],
        'RAM Range': df['ram_max'] - df['ram_min']
    })
    
    range_data = range_data.set_index('treatment')
    
    # Create the heatmap
    plt.figure(figsize=(10, 6))
    
    sns.heatmap(range_data.T, annot=True, fmt='.2f', cmap='YlOrRd', 
                cbar_kws={'label': 'Range (Max - Min)'}, 
                linewidths=0.5, linecolor='white')
    
    plt.title('Performance Variability Heatmap (Ranges)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Treatment', fontsize=14, fontweight='bold')
    plt.ylabel('Metrics', fontsize=14, fontweight='bold')
    
    # Add note
    plt.figtext(0.5, 0.02, 'Note: Higher values indicate more variability in performance', 
                ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/variability_heatmap.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def create_correlation_heatmap(save_path="heatmaps"):
    """
    Create a correlation heatmap between different metrics
    """
    try:
        import glob
        
        # Load raw data for correlation analysis
        data_files = glob.glob("../data/processed/response_variables/T*_response_variables_*.csv")
        
        if not data_files:
            print("No raw data files found for correlation analysis")
            return
        
        all_data = []
        for file in data_files:
            df = pd.read_csv(file)
            all_data.append(df)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Calculate correlation matrix
        metrics = ['tps', 'cpu_usage', 'ram_usage']
        corr_matrix = combined_df[metrics].corr()
        
        # Rename for better display
        corr_matrix.index = ['TPS', 'CPU Usage (%)', 'RAM Usage (MB)']
        corr_matrix.columns = ['TPS', 'CPU Usage (%)', 'RAM Usage (MB)']
        
        # Create the heatmap
        plt.figure(figsize=(8, 6))
        
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                    square=True, cbar_kws={'label': 'Correlation Coefficient'}, 
                    linewidths=0.5, linecolor='white')
        
        plt.title('Performance Metrics Correlation Matrix', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Save plot
        filename = f"{save_path}/correlation_heatmap.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")
        
        plt.show()
        
    except Exception as e:
        print(f"Could not create correlation heatmap: {e}")

def main():
    """
    Main function to generate all heatmaps
    """
    print("Loading summary data...")
    df = load_summary_data()
    
    if df is not None:
        print("\nGenerating performance heatmaps...")
        create_performance_heatmap(df)
        
        print("\nGenerating variability heatmap...")
        create_range_heatmap(df)
        
        print("\nGenerating correlation heatmap...")
        create_correlation_heatmap()
        
        print("\nHeatmap generation complete!")
        print("Check the 'heatmaps' folder for saved images.")
    else:
        print("Failed to load data.")

if __name__ == "__main__":
    main()
