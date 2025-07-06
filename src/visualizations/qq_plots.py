import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
import os
import glob
from scipy.stats import shapiro

def load_all_treatment_data():
    """
    Load and combine all treatment data for Q-Q plot analysis
    """
    # Get all CSV files
    data_files = glob.glob("../../data/processed/response_variables/T*_response_variables_*.csv")
    
    if not data_files:
        print("No data files found. Make sure you're running from the analysis folder.")
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

def create_qq_plots_by_treatment(df, save_path="qq_plots"):
    """
    Create Q-Q plots for each treatment and metric to test normality
    """
    if df is None or df.empty:
        print("No data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Metrics to analyze
    metrics = ['tps', 'cpu_usage', 'ram_usage']
    metric_titles = {
        'tps': 'TPS (Ticks Per Second)',
        'cpu_usage': 'CPU Usage (%)',
        'ram_usage': 'RAM Usage (MB)'
    }
    
    treatments = sorted(df['treatment'].unique())
    
    for metric in metrics:
        # Create figure with subplots for each treatment
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        fig.suptitle(f'Q-Q Plots for {metric_titles[metric]} - Normality Test', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes for easier iteration
        axes = axes.flatten()
        
        normality_results = []
        
        for i, treatment in enumerate(treatments):
            # Get data for this treatment
            treatment_data = df[df['treatment'] == treatment][metric].dropna()
            
            if len(treatment_data) < 3:
                print(f"Warning: Not enough data for {treatment} in {metric}")
                continue
            
            # Create Q-Q plot
            stats.probplot(treatment_data, dist="norm", plot=axes[i])
            axes[i].set_title(f'{treatment}\n(n={len(treatment_data)})', fontweight='bold')
            axes[i].grid(True, alpha=0.3)
            
            # Perform Shapiro-Wilk test
            if len(treatment_data) >= 3:
                shapiro_stat, shapiro_p = shapiro(treatment_data)
                normality_results.append({
                    'treatment': treatment,
                    'metric': metric,
                    'shapiro_statistic': shapiro_stat,
                    'shapiro_p_value': shapiro_p,
                    'is_normal': shapiro_p > 0.05,
                    'sample_size': len(treatment_data)
                })
                
                # Add test result to plot
                color = 'green' if shapiro_p > 0.05 else 'red'
                axes[i].text(0.05, 0.95, f'Shapiro p={shapiro_p:.4f}', 
                           transform=axes[i].transAxes, fontsize=9,
                           bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        # Hide unused subplots
        for j in range(len(treatments), len(axes)):
            axes[j].set_visible(False)
        
        plt.tight_layout()
        
        # Save plot
        filename = f"{save_path}/qq_plot_{metric}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")
        
        # Save normality test results
        if normality_results:
            results_df = pd.DataFrame(normality_results)
            results_filename = f"{save_path}/normality_test_{metric}.csv"
            results_df.to_csv(results_filename, index=False)
            print(f"Normality test results saved: {results_filename}")
        
        plt.show()

def create_comprehensive_qq_analysis(df, save_path="qq_plots"):
    """
    Create a comprehensive Q-Q analysis with summary statistics
    """
    if df is None or df.empty:
        print("No data to analyze")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    metrics = ['tps', 'cpu_usage', 'ram_usage']
    treatments = sorted(df['treatment'].unique())
    
    all_normality_results = []
    
    print("\n" + "="*80)
    print("NORMALITY ANALYSIS SUMMARY")
    print("="*80)
    
    for metric in metrics:
        print(f"\n{metric.upper()} ANALYSIS:")
        print("-" * 40)
        
        for treatment in treatments:
            treatment_data = df[df['treatment'] == treatment][metric].dropna()
            
            if len(treatment_data) >= 3:
                # Descriptive statistics
                mean_val = treatment_data.mean()
                std_val = treatment_data.std()
                skewness = treatment_data.skew()
                kurtosis = treatment_data.kurtosis()
                
                # Normality tests
                shapiro_stat, shapiro_p = shapiro(treatment_data)
                
                # Store results
                result = {
                    'metric': metric,
                    'treatment': treatment,
                    'sample_size': len(treatment_data),
                    'mean': mean_val,
                    'std': std_val,
                    'skewness': skewness,
                    'kurtosis': kurtosis,
                    'shapiro_statistic': shapiro_stat,
                    'shapiro_p_value': shapiro_p,
                    'is_normal_shapiro': shapiro_p > 0.05
                }
                
                all_normality_results.append(result)
                
                # Print summary
                normal_status = "NORMAL" if shapiro_p > 0.05 else "NOT NORMAL"
                print(f"{treatment}: n={len(treatment_data)}, μ={mean_val:.2f}, "
                      f"σ={std_val:.2f}, Shapiro p={shapiro_p:.4f} [{normal_status}]")
    
    # Save comprehensive results
    if all_normality_results:
        results_df = pd.DataFrame(all_normality_results)
        results_filename = f"{save_path}/comprehensive_normality_analysis.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"\nComprehensive analysis saved: {results_filename}")
        
        # Create summary by metric
        print("\n" + "="*80)
        print("NORMALITY TEST SUMMARY BY METRIC")
        print("="*80)
        
        for metric in metrics:
            metric_data = results_df[results_df['metric'] == metric]
            normal_count = metric_data['is_normal_shapiro'].sum()
            total_count = len(metric_data)
            
            print(f"\n{metric.upper()}:")
            print(f"  Normal distributions: {normal_count}/{total_count}")
            print(f"  Percentage normal: {(normal_count/total_count)*100:.1f}%")
            
            if normal_count < total_count:
                print(f"  → Recommendation: Consider non-parametric tests (Kruskal-Wallis)")
            else:
                print(f"  → Recommendation: Parametric tests (ANOVA) may be appropriate")

def main():
    """
    Main function to perform Q-Q plot analysis
    """
    print("Starting Q-Q Plot Analysis for Normality Testing...")
    print("="*60)
    
    # Load data
    df = load_all_treatment_data()
    
    if df is not None:
        print("\nGenerating Q-Q plots by treatment...")
        create_qq_plots_by_treatment(df)
        
        print("\nPerforming comprehensive normality analysis...")
        create_comprehensive_qq_analysis(df)
        
        print("\n" + "="*60)
        print("Q-Q Plot Analysis Complete!")
        print("Check the 'qq_plots' folder for:")
        print("- Individual Q-Q plots for each metric")
        print("- Normality test results (CSV files)")
        print("- Comprehensive analysis summary")
        print("="*60)
    else:
        print("Failed to load data. Please check your data files.")

if __name__ == "__main__":
    main()
