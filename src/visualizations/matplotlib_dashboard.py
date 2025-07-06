import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
from mpl_toolkits.mplot3d import Axes3D

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

def load_raw_data():
    """
    Load raw data for detailed analysis from actual CSV files
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
        print("No valid raw data found.")
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Convert date column to datetime if it exists
    if 'date' in combined_df.columns:
        combined_df['date'] = pd.to_datetime(combined_df['date'])
    
    print(f"Loaded raw data for treatments: {sorted(combined_df['treatment'].unique())}")
    print(f"Total raw records: {len(combined_df)}")
    
    return combined_df

def create_comprehensive_dashboard(df_summary, df_raw=None, save_path="dashboard"):
    """
    Create a comprehensive dashboard using matplotlib
    """
    if df_summary is None or df_summary.empty:
        print("No summary data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Create a large figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. TPS Performance (subplot 1)
    ax1 = plt.subplot(3, 3, 1)
    x_pos = range(len(df_summary))
    bars = ax1.bar(df_summary['treatment'], df_summary['tps_mean'], 
                   color='green', alpha=0.7, edgecolor='black')
    ax1.errorbar(x_pos, df_summary['tps_mean'], 
                yerr=[df_summary['tps_mean'] - df_summary['tps_min'],
                      df_summary['tps_max'] - df_summary['tps_mean']], 
                fmt='none', color='black', capsize=5)
    ax1.set_title('TPS Performance by Treatment', fontweight='bold')
    ax1.set_ylabel('TPS')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. CPU Usage (subplot 2)
    ax2 = plt.subplot(3, 3, 2)
    bars = ax2.bar(df_summary['treatment'], df_summary['cpu_mean'], 
                   color='orange', alpha=0.7, edgecolor='black')
    ax2.set_title('CPU Usage by Treatment', fontweight='bold')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.grid(True, alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 3. RAM Usage (subplot 3)
    ax3 = plt.subplot(3, 3, 3)
    bars = ax3.bar(df_summary['treatment'], df_summary['ram_mean'], 
                   color='red', alpha=0.7, edgecolor='black')
    ax3.set_title('RAM Usage by Treatment', fontweight='bold')
    ax3.set_ylabel('RAM Usage (MB)')
    ax3.grid(True, alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'{height:.0f}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Performance Heatmap (subplot 4)
    ax4 = plt.subplot(3, 3, 4)
    # Normalize metrics for heatmap
    tps_norm = (df_summary['tps_mean'] - df_summary['tps_mean'].min()) / (df_summary['tps_mean'].max() - df_summary['tps_mean'].min())
    cpu_norm = 1 - ((df_summary['cpu_mean'] - df_summary['cpu_mean'].min()) / (df_summary['cpu_mean'].max() - df_summary['cpu_mean'].min()))
    ram_norm = 1 - ((df_summary['ram_mean'] - df_summary['ram_mean'].min()) / (df_summary['ram_mean'].max() - df_summary['ram_mean'].min()))
    
    heatmap_data = np.array([tps_norm, cpu_norm, ram_norm]).T
    
    im = ax4.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax4.set_xticks(range(3))
    ax4.set_xticklabels(['TPS Score', 'CPU Score', 'RAM Score'])
    ax4.set_yticks(range(len(df_summary)))
    ax4.set_yticklabels(df_summary['treatment'])
    ax4.set_title('Normalized Performance Scores', fontweight='bold')
    
    # Add text annotations
    for i in range(len(df_summary)):
        for j in range(3):
            text = ax4.text(j, i, f'{heatmap_data[i, j]:.2f}',
                           ha="center", va="center", color="black", fontweight='bold')
    
    # 5. Variability Analysis (subplot 5)
    ax5 = plt.subplot(3, 3, 5)
    tps_range = df_summary['tps_max'] - df_summary['tps_min']
    bars = ax5.bar(df_summary['treatment'], tps_range, 
                   color='lightblue', alpha=0.7, edgecolor='black')
    ax5.set_title('TPS Variability (Range)', fontweight='bold')
    ax5.set_ylabel('TPS Range')
    ax5.grid(True, alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 6. Performance Score Ranking (subplot 6)
    ax6 = plt.subplot(3, 3, 6)
    composite_score = (tps_norm + cpu_norm + ram_norm) / 3
    sorted_indices = composite_score.sort_values(ascending=False).index
    
    bars = ax6.bar(df_summary['treatment'].iloc[sorted_indices], 
                   composite_score.iloc[sorted_indices],
                   color='purple', alpha=0.7, edgecolor='black')
    ax6.set_title('Performance Score Ranking', fontweight='bold')
    ax6.set_ylabel('Composite Score')
    ax6.grid(True, alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 7. 3D Scatter Plot (subplot 7)
    ax7 = plt.subplot(3, 3, 7, projection='3d')
    scatter = ax7.scatter(df_summary['tps_mean'], df_summary['cpu_mean'], df_summary['ram_mean'],
                         c=df_summary['tps_mean'], cmap='viridis', s=100, alpha=0.8)
    
    # Add labels for each point
    for i, treatment in enumerate(df_summary['treatment']):
        ax7.text(df_summary['tps_mean'].iloc[i], 
                df_summary['cpu_mean'].iloc[i], 
                df_summary['ram_mean'].iloc[i], 
                treatment, fontsize=10, fontweight='bold')
    
    ax7.set_xlabel('TPS (Mean)')
    ax7.set_ylabel('CPU Usage % (Mean)')
    ax7.set_zlabel('RAM Usage MB (Mean)')
    ax7.set_title('3D Performance Visualization', fontweight='bold')
    
    # 8. Performance Comparison Radar-like Chart (subplot 8)
    ax8 = plt.subplot(3, 3, 8)
    metrics = ['TPS Score', 'CPU Score', 'RAM Score']
    
    # Create a simple radar-like visualization
    x_pos = np.arange(len(metrics))
    width = 0.1
    
    for i, treatment in enumerate(df_summary['treatment']):
        scores = [tps_norm.iloc[i], cpu_norm.iloc[i], ram_norm.iloc[i]]
        ax8.bar(x_pos + i * width, scores, width, label=treatment, alpha=0.7)
    
    ax8.set_xlabel('Metrics')
    ax8.set_ylabel('Normalized Score')
    ax8.set_title('Performance Comparison', fontweight='bold')
    ax8.set_xticks(x_pos + width * 3)
    ax8.set_xticklabels(metrics)
    ax8.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax8.grid(True, alpha=0.3)
    
    # 9. Summary Statistics (subplot 9)
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    # Create summary text
    summary_text = f"""PERFORMANCE SUMMARY
    
Best TPS: {df_summary.loc[df_summary['tps_mean'].idxmax(), 'treatment']} ({df_summary['tps_mean'].max():.2f})
Best CPU: {df_summary.loc[df_summary['cpu_mean'].idxmin(), 'treatment']} ({df_summary['cpu_mean'].min():.2f}%)
Best RAM: {df_summary.loc[df_summary['ram_mean'].idxmin(), 'treatment']} ({df_summary['ram_mean'].min():.0f} MB)

Overall Winner: {df_summary['treatment'].iloc[sorted_indices[0]]}
Score: {composite_score.iloc[sorted_indices[0]]:.3f}

Average TPS: {df_summary['tps_mean'].mean():.2f}
Average CPU: {df_summary['cpu_mean'].mean():.2f}%
Average RAM: {df_summary['ram_mean'].mean():.0f} MB

Most Stable TPS: {df_summary.loc[tps_range.idxmin(), 'treatment']}
Range: {tps_range.min():.2f}
"""
    
    ax9.text(0.1, 0.9, summary_text, transform=ax9.transAxes, fontsize=11,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Main title
    fig.suptitle('Minecraft Server Performance Analysis Dashboard', 
                 fontsize=24, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    # Save the dashboard
    filename = f"{save_path}/performance_dashboard.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved dashboard: {filename}")
    
    plt.show()

def create_time_series_plot(df_raw, save_path="dashboard"):
    """
    Create time series plots if raw data is available
    """
    if df_raw is None or df_raw.empty:
        print("No raw data available for time series plot")
        return
    
    # Create time series plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    
    # Get unique treatments and colors
    treatments = sorted(df_raw['treatment'].unique())
    colors = plt.cm.Set3(np.linspace(0, 1, len(treatments)))
    
    for i, treatment in enumerate(treatments):
        treatment_data = df_raw[df_raw['treatment'] == treatment]
        
        # TPS
        ax1.plot(treatment_data['date'], treatment_data['tps'], 
                label=treatment, color=colors[i], linewidth=2)
        
        # CPU
        ax2.plot(treatment_data['date'], treatment_data['cpu_usage'], 
                label=treatment, color=colors[i], linewidth=2)
        
        # RAM
        ax3.plot(treatment_data['date'], treatment_data['ram_usage'], 
                label=treatment, color=colors[i], linewidth=2)
    
    # Customize plots
    ax1.set_title('TPS Over Time', fontweight='bold')
    ax1.set_ylabel('TPS')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2.set_title('CPU Usage Over Time', fontweight='bold')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.grid(True, alpha=0.3)
    
    ax3.set_title('RAM Usage Over Time', fontweight='bold')
    ax3.set_ylabel('RAM Usage (MB)')
    ax3.set_xlabel('Date')
    ax3.grid(True, alpha=0.3)
    
    plt.suptitle('Performance Metrics Over Time', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/time_series_plot.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved time series plot: {filename}")
    
    plt.show()

def main():
    """
    Main function to generate all visualizations
    """
    print("Loading data...")
    df_summary = load_summary_data()
    df_raw = load_raw_data()
    
    if df_summary is not None:
        print("\nGenerating comprehensive dashboard...")
        create_comprehensive_dashboard(df_summary, df_raw)
        
        if df_raw is not None:
            print("\nGenerating time series plot...")
            create_time_series_plot(df_raw)
        else:
            print("Raw data not available for time series plot")
        
        print("\nDashboard generation complete!")
        print("Check the 'dashboard' folder for PNG files.")
    else:
        print("Failed to load summary data.")

if __name__ == "__main__":
    main()
