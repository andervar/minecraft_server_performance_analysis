import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def load_all_treatment_data():
    """
    Load and combine all treatment data for visualization
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
    print(f"Loaded data for treatments: {sorted(combined_df['treatment'].unique())}")
    print(f"Total records: {len(combined_df)}")
    
    return combined_df

def create_box_plots(df, save_path="box_plots"):
    """
    Create box plots for TPS, CPU, and RAM metrics
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Metrics to plot
    metrics = [
        ('tps', 'TPS (Ticks Per Second)', 'Higher is Better'),
        ('cpu_usage', 'CPU Usage (%)', 'Lower is Better'),
        ('ram_usage', 'RAM Usage (MB)', 'Lower is Better')
    ]
    
    for metric, title, note in metrics:
        plt.figure(figsize=(12, 8))
        
        # Create box plot
        box_plot = sns.boxplot(data=df, x='treatment', y=metric, 
                              showmeans=True, meanprops={'marker': 'D', 'markerfacecolor': 'red', 'markersize': 8})
        
        # Customize plot
        plt.title(f'{title} by Treatment\n{note}', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Treatment', fontsize=14, fontweight='bold')
        plt.ylabel(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # Add sample size annotations
        for i, treatment in enumerate(sorted(df['treatment'].unique())):
            treatment_data = df[df['treatment'] == treatment][metric]
            n = len(treatment_data)
            plt.text(i, treatment_data.min() - (treatment_data.max() - treatment_data.min()) * 0.1, 
                    f'n={n}', ha='center', va='top', fontsize=10, fontweight='bold')
        
        # Add statistics summary as text
        stats_text = []
        for treatment in sorted(df['treatment'].unique()):
            treatment_data = df[df['treatment'] == treatment][metric]
            mean_val = treatment_data.mean()
            median_val = treatment_data.median()
            std_val = treatment_data.std()
            stats_text.append(f"{treatment}: μ={mean_val:.2f}, M={median_val:.2f}, σ={std_val:.2f}")
        
        # Add text box with statistics
        textstr = '\n'.join(stats_text)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        plt.figtext(0.02, 0.02, textstr, fontsize=9, verticalalignment='bottom', bbox=props)
        
        plt.tight_layout()
        
        # Save plot
        filename = f"{save_path}/{metric}_boxplot.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")
        
        plt.show()

def create_comparative_box_plot(df, save_path="box_plots"):
    """
    Create a single figure with all three metrics for comparison
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Create subplot figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Minecraft Server Performance Metrics Comparison', fontsize=16, fontweight='bold')
    
    # Metrics configuration
    metrics = [
        ('tps', 'TPS (Ticks Per Second)', 'Higher is Better'),
        ('cpu_usage', 'CPU Usage (%)', 'Lower is Better'),
        ('ram_usage', 'RAM Usage (MB)', 'Lower is Better')
    ]
    
    for i, (metric, title, note) in enumerate(metrics):
        # Create box plot
        sns.boxplot(data=df, x='treatment', y=metric, ax=axes[i],
                   showmeans=True, meanprops={'marker': 'D', 'markerfacecolor': 'red', 'markersize': 6})
        
        # Customize subplot
        axes[i].set_title(f'{title}\n({note})', fontsize=12, fontweight='bold')
        axes[i].set_xlabel('Treatment', fontsize=11, fontweight='bold')
        axes[i].set_ylabel(title, fontsize=11, fontweight='bold')
        axes[i].grid(True, alpha=0.3)
        
        # Rotate x-axis labels if needed
        axes[i].tick_params(axis='x', rotation=0)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/all_metrics_comparison.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def main():
    """
    Main function to generate all box plots
    """
    print("Loading treatment data...")
    df = load_all_treatment_data()
    
    if df is not None:
        print("\nGenerating individual box plots...")
        create_box_plots(df)
        
        print("\nGenerating comparative box plot...")
        create_comparative_box_plot(df)
        
        print("\nBox plot generation complete!")
        print("Check the 'box_plots' folder for saved images.")
    else:
        print("Failed to load data. Please check your data files.")

if __name__ == "__main__":
    main()
