import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import kruskal
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def load_all_treatment_data():
    """
    Load and combine all treatment data for Kruskal-Wallis analysis
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

def prepare_data_for_kruskal(df, metric):
    """
    Prepare data groups for Kruskal-Wallis test
    """
    treatments = sorted(df['treatment'].unique())
    data_groups = []
    group_names = []
    
    for treatment in treatments:
        treatment_data = df[df['treatment'] == treatment][metric].dropna()
        if len(treatment_data) > 0:
            data_groups.append(treatment_data.values)
            group_names.append(treatment)
    
    return data_groups, group_names

def perform_kruskal_wallis_test(df, metric):
    """
    Perform Kruskal-Wallis test for a specific metric
    """
    data_groups, group_names = prepare_data_for_kruskal(df, metric)
    
    if len(data_groups) < 2:
        print(f"Not enough groups for {metric} analysis")
        return None
    
    # Perform Kruskal-Wallis test
    h_statistic, p_value = kruskal(*data_groups)
    
    # Calculate effect size (eta-squared for Kruskal-Wallis)
    n_total = sum(len(group) for group in data_groups)
    eta_squared = (h_statistic - len(data_groups) + 1) / (n_total - len(data_groups))
    
    # Interpret effect size
    if eta_squared < 0.01:
        effect_size_interpretation = "Small"
    elif eta_squared < 0.06:
        effect_size_interpretation = "Medium"
    else:
        effect_size_interpretation = "Large"
    
    result = {
        'metric': metric,
        'h_statistic': h_statistic,
        'p_value': p_value,
        'degrees_freedom': len(data_groups) - 1,
        'effect_size_eta_squared': eta_squared,
        'effect_size_interpretation': effect_size_interpretation,
        'significant': p_value < 0.05,
        'groups': group_names,
        'group_sizes': [len(group) for group in data_groups]
    }
    
    return result

def create_kruskal_wallis_summary_plot(results, save_path="kruskal_analysis"):
    """
    Create visualization of Kruskal-Wallis results
    """
    os.makedirs(save_path, exist_ok=True)
    
    # Extract data for plotting
    metrics = [r['metric'] for r in results if r is not None]
    h_statistics = [r['h_statistic'] for r in results if r is not None]
    p_values = [r['p_value'] for r in results if r is not None]
    effect_sizes = [r['effect_size_eta_squared'] for r in results if r is not None]
    
    if not metrics:
        print("No results to plot")
        return
    
    # Create subplot figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Kruskal-Wallis Test Results Summary', fontsize=16, fontweight='bold')
    
    # Plot 1: H-statistics
    axes[0].bar(metrics, h_statistics, color=['skyblue', 'lightcoral', 'lightgreen'])
    axes[0].set_title('H-Statistics', fontweight='bold')
    axes[0].set_ylabel('H-Statistic')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Plot 2: P-values with significance line
    colors = ['red' if p < 0.05 else 'gray' for p in p_values]
    axes[1].bar(metrics, p_values, color=colors)
    axes[1].axhline(y=0.05, color='red', linestyle='--', label='α = 0.05')
    axes[1].set_title('P-Values', fontweight='bold')
    axes[1].set_ylabel('P-Value')
    axes[1].set_yscale('log')
    axes[1].legend()
    axes[1].tick_params(axis='x', rotation=45)
    
    # Plot 3: Effect sizes
    axes[2].bar(metrics, effect_sizes, color=['purple', 'orange', 'brown'])
    axes[2].set_title('Effect Size (η²)', fontweight='bold')
    axes[2].set_ylabel('Eta-squared')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/kruskal_wallis_summary.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Summary plot saved: {filename}")
    
    plt.show()

def comprehensive_kruskal_wallis_analysis(df, save_path="kruskal_analysis"):
    """
    Perform comprehensive Kruskal-Wallis analysis for all metrics
    """
    if df is None or df.empty:
        print("No data to analyze")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    metrics = ['tps', 'cpu_usage', 'ram_usage']
    metric_titles = {
        'tps': 'TPS (Ticks Per Second)',
        'cpu_usage': 'CPU Usage (%)',
        'ram_usage': 'RAM Usage (MB)'
    }
    
    all_results = []
    
    print("\n" + "="*80)
    print("KRUSKAL-WALLIS NON-PARAMETRIC ANALYSIS")
    print("="*80)
    print("Testing for differences between treatment groups")
    print("H₀: All treatment groups have the same distribution")
    print("H₁: At least one treatment group differs from the others")
    print("="*80)
    
    for metric in metrics:
        print(f"\n{metric_titles[metric].upper()} ANALYSIS:")
        print("-" * 50)
        
        # Perform Kruskal-Wallis test
        result = perform_kruskal_wallis_test(df, metric)
        
        if result:
            all_results.append(result)
            
            # Print results
            print(f"H-statistic: {result['h_statistic']:.4f}")
            print(f"P-value: {result['p_value']:.6f}")
            print(f"Degrees of freedom: {result['degrees_freedom']}")
            print(f"Effect size (η²): {result['effect_size_eta_squared']:.4f} ({result['effect_size_interpretation']})")
            
            if result['significant']:
                print("🔴 SIGNIFICANT: Reject H₀ - Treatments differ significantly")
                print("→ Consider running post-hoc tests to identify specific group differences")
            else:
                print("⚪ NOT SIGNIFICANT: Fail to reject H₀ - No significant differences")
            
            # Print descriptive statistics by group
            print(f"\nDescriptive statistics for {metric}:")
            treatments = sorted(df['treatment'].unique())
            for treatment in treatments:
                treatment_data = df[df['treatment'] == treatment][metric].dropna()
                if len(treatment_data) > 0:
                    median_val = treatment_data.median()
                    q1 = treatment_data.quantile(0.25)
                    q3 = treatment_data.quantile(0.75)
                    iqr = q3 - q1
                    print(f"  {treatment}: Median={median_val:.2f}, IQR={iqr:.2f}, n={len(treatment_data)}")
    
    # Save results to CSV
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_filename = f"{save_path}/kruskal_wallis_results.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"\nKruskal-Wallis results saved: {results_filename}")
    
    # Create summary visualization
    create_kruskal_wallis_summary_plot(all_results, save_path)
    
    # Print final summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    significant_metrics = [r['metric'] for r in all_results if r['significant']]
    if significant_metrics:
        print(f"Metrics with significant treatment effects: {', '.join(significant_metrics)}")
        print("Recommendation: Run post-hoc tests to identify specific group differences")
        print("Use the post_hoc_analysis.py script for detailed pairwise comparisons")
    else:
        print("No significant treatment effects found in any metric")
        print("Recommendation: Treatments may have similar performance characteristics")
    
    return all_results

def main():
    """
    Main function to perform Kruskal-Wallis analysis
    """
    print("Starting Kruskal-Wallis Non-Parametric Analysis...")
    print("="*60)
    print("This test is used when:")
    print("- Data doesn't meet normality assumptions for ANOVA")
    print("- Comparing 3+ independent groups")
    print("- Working with ordinal or non-normal continuous data")
    print("="*60)
    
    # Load data
    df = load_all_treatment_data()
    
    if df is not None:
        # Perform comprehensive analysis
        results = comprehensive_kruskal_wallis_analysis(df)
        
        print("\n" + "="*60)
        print("Kruskal-Wallis Analysis Complete!")
        print("Check the 'kruskal_analysis' folder for:")
        print("- Kruskal-Wallis test results (CSV)")
        print("- Summary visualization (PNG)")
        print("\nFor post-hoc analysis, run: python post_hoc_analysis.py")
        print("="*60)
    else:
        print("Failed to load data. Please check your data files.")

if __name__ == "__main__":
    main()
