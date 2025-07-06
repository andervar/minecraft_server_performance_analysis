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

def create_mean_comparison_bars(df, save_path="bar_charts"):
    """
    Create bar charts comparing mean values across treatments
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    
    # Create subplots for each metric
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Mean Performance Metrics Comparison', fontsize=16, fontweight='bold')
    
    # Metrics configuration
    metrics = [
        ('tps_mean', 'TPS (Mean)', 'green', 'Higher is Better'),
        ('cpu_mean', 'CPU Usage % (Mean)', 'orange', 'Lower is Better'),
        ('ram_mean', 'RAM Usage MB (Mean)', 'red', 'Lower is Better')
    ]
    
    for i, (metric, title, color, note) in enumerate(metrics):
        # Create bar plot
        bars = axes[i].bar(df['treatment'], df[metric], color=color, alpha=0.7, edgecolor='black')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            axes[i].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Customize subplot
        axes[i].set_title(f'{title}\n({note})', fontsize=12, fontweight='bold')
        axes[i].set_xlabel('Treatment', fontsize=11, fontweight='bold')
        axes[i].set_ylabel(title.split('(')[0].strip(), fontsize=11, fontweight='bold')
        axes[i].grid(True, alpha=0.3, axis='y')
        
        # Highlight best performer
        if 'Higher is Better' in note:
            best_idx = df[metric].idxmax()
        else:
            best_idx = df[metric].idxmin()
        
        bars[best_idx].set_color('gold')
        bars[best_idx].set_edgecolor('black')
        bars[best_idx].set_linewidth(2)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/mean_comparison_bars.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def create_range_comparison_bars(df, save_path="bar_charts"):
    """
    Create bar charts showing ranges (variability) for each treatment
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Calculate ranges
    df['tps_range'] = df['tps_max'] - df['tps_min']
    df['cpu_range'] = df['cpu_max'] - df['cpu_min']
    df['ram_range'] = df['ram_max'] - df['ram_min']
    
    # Create subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Performance Variability Comparison (Ranges)', fontsize=16, fontweight='bold')
    
    # Metrics configuration
    metrics = [
        ('tps_range', 'TPS Range', 'lightblue'),
        ('cpu_range', 'CPU Range (%)', 'lightcoral'),
        ('ram_range', 'RAM Range (MB)', 'lightgreen')
    ]
    
    for i, (metric, title, color) in enumerate(metrics):
        # Create bar plot
        bars = axes[i].bar(df['treatment'], df[metric], color=color, alpha=0.7, edgecolor='black')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            axes[i].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Customize subplot
        axes[i].set_title(title, fontsize=12, fontweight='bold')
        axes[i].set_xlabel('Treatment', fontsize=11, fontweight='bold')
        axes[i].set_ylabel('Range (Max - Min)', fontsize=11, fontweight='bold')
        axes[i].grid(True, alpha=0.3, axis='y')
        
        # Highlight most stable (lowest range)
        min_idx = df[metric].idxmin()
        bars[min_idx].set_color('gold')
        bars[min_idx].set_edgecolor('black')
        bars[min_idx].set_linewidth(2)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/variability_comparison_bars.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def create_grouped_bar_chart(df, save_path="bar_charts"):
    """
    Create grouped bar chart showing min, mean, max for each treatment
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Prepare data for TPS metric
    treatments = df['treatment']
    tps_min = df['tps_min']
    tps_mean = df['tps_mean']
    tps_max = df['tps_max']
    
    x = np.arange(len(treatments))
    width = 0.25
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    bars1 = ax.bar(x - width, tps_min, width, label='Minimum', color='lightcoral', alpha=0.8)
    bars2 = ax.bar(x, tps_mean, width, label='Mean', color='gold', alpha=0.8)
    bars3 = ax.bar(x + width, tps_max, width, label='Maximum', color='lightgreen', alpha=0.8)
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Customize plot
    ax.set_title('TPS Performance: Min, Mean, Max by Treatment', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Treatment', fontsize=14, fontweight='bold')
    ax.set_ylabel('TPS (Ticks Per Second)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(treatments)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add horizontal line for ideal TPS (20.0)
    ax.axhline(y=20.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Ideal TPS (20.0)')
    ax.legend(fontsize=12)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/tps_grouped_bars.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def create_performance_score_bars(df, save_path="bar_charts"):
    """
    Create a composite performance score bar chart
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Normalize metrics (0-1 scale)
    # TPS: higher is better
    tps_score = (df['tps_mean'] - df['tps_mean'].min()) / (df['tps_mean'].max() - df['tps_mean'].min())
    
    # CPU: lower is better (invert)
    cpu_score = 1 - ((df['cpu_mean'] - df['cpu_mean'].min()) / (df['cpu_mean'].max() - df['cpu_mean'].min()))
    
    # RAM: lower is better (invert)
    ram_score = 1 - ((df['ram_mean'] - df['ram_mean'].min()) / (df['ram_mean'].max() - df['ram_mean'].min()))
    
    # Calculate composite score (equal weights)
    composite_score = (tps_score + cpu_score + ram_score) / 3
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Individual scores
    x = np.arange(len(df))
    width = 0.25
    
    bars1 = ax1.bar(x - width, tps_score, width, label='TPS Score', color='green', alpha=0.7)
    bars2 = ax1.bar(x, cpu_score, width, label='CPU Score', color='orange', alpha=0.7)
    bars3 = ax1.bar(x + width, ram_score, width, label='RAM Score', color='red', alpha=0.7)
    
    ax1.set_title('Individual Performance Scores by Treatment', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Performance Score (0-1)', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['treatment'])
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim(0, 1.1)
    
    # Composite score
    bars_composite = ax2.bar(df['treatment'], composite_score, color='purple', alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bar in bars_composite:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # Highlight best performer
    best_idx = composite_score.idxmax()
    bars_composite[best_idx].set_color('gold')
    bars_composite[best_idx].set_edgecolor('black')
    bars_composite[best_idx].set_linewidth(2)
    
    ax2.set_title('Composite Performance Score by Treatment', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Treatment', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Composite Score (0-1)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/performance_scores.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()
    
    # Print ranking
    ranking = df['treatment'].iloc[composite_score.sort_values(ascending=False).index]
    scores = composite_score.sort_values(ascending=False)
    
    print("\nPerformance Ranking:")
    print("-" * 30)
    for i, (treatment, score) in enumerate(zip(ranking, scores), 1):
        print(f"{i}. {treatment}: {score:.3f}")

def main():
    """
    Main function to generate all bar charts
    """
    print("Loading summary data...")
    df = load_summary_data()
    
    if df is not None:
        print("\nGenerating mean comparison bars...")
        create_mean_comparison_bars(df)
        
        print("\nGenerating variability comparison bars...")
        create_range_comparison_bars(df)
        
        print("\nGenerating grouped TPS bars...")
        create_grouped_bar_chart(df)
        
        print("\nGenerating performance score bars...")
        create_performance_score_bars(df)
        
        print("\nBar chart generation complete!")
        print("Check the 'bar_charts' folder for saved images.")
    else:
        print("Failed to load data.")

if __name__ == "__main__":
    main()
