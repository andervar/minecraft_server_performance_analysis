import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from itertools import combinations

def load_all_treatment_data():
    """
    Load and combine all treatment data for post-hoc analysis
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

def check_kruskal_results(kruskal_results_file="kruskal_analysis/kruskal_wallis_results.csv"):
    """
    Check which metrics showed significant results in Kruskal-Wallis test
    """
    if not os.path.exists(kruskal_results_file):
        print(f"Kruskal-Wallis results file not found: {kruskal_results_file}")
        print("Please run kruskal_wallis.py first!")
        return None
    
    try:
        kruskal_df = pd.read_csv(kruskal_results_file)
        significant_metrics = kruskal_df[kruskal_df['significant'] == True]['metric'].tolist()
        
        print("Kruskal-Wallis Results Summary:")
        print("-" * 40)
        for _, row in kruskal_df.iterrows():
            status = "SIGNIFICANT" if row['significant'] else "NOT SIGNIFICANT"
            print(f"{row['metric']}: H={row['h_statistic']:.4f}, p={row['p_value']:.6f} [{status}]")
        
        return significant_metrics
    except Exception as e:
        print(f"Error reading Kruskal-Wallis results: {e}")
        return None

def perform_dunn_post_hoc(df, metric, alpha=0.05):
    """
    Perform Dunn's post-hoc test for pairwise comparisons after Kruskal-Wallis
    Using Mann-Whitney U test with multiple comparison corrections
    """
    treatments = sorted(df['treatment'].unique())
    comparisons = []
    
    # Get all pairwise combinations
    pairs = list(combinations(treatments, 2))
    
    # Multiple comparison corrections
    bonferroni_alpha = alpha / len(pairs)
    
    print(f"\nPerforming {len(pairs)} pairwise comparisons for {metric}")
    print(f"Bonferroni corrected α = {bonferroni_alpha:.6f}")
    
    for treatment1, treatment2 in pairs:
        group1 = df[df['treatment'] == treatment1][metric].dropna()
        group2 = df[df['treatment'] == treatment2][metric].dropna()
        
        if len(group1) > 0 and len(group2) > 0:
            # Mann-Whitney U test
            u_statistic, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            
            # Calculate effect size (r = Z / sqrt(N))
            n1, n2 = len(group1), len(group2)
            # Better z-score calculation
            mean_rank_diff = abs(group1.rank().mean() - group2.rank().mean())
            pooled_n = n1 + n2
            z_approx = (u_statistic - (n1 * n2 / 2)) / np.sqrt(n1 * n2 * (pooled_n + 1) / 12)
            effect_size_r = abs(z_approx) / np.sqrt(pooled_n)
            
            # Interpret effect size
            if effect_size_r < 0.1:
                effect_interpretation = "Negligible"
            elif effect_size_r < 0.3:
                effect_interpretation = "Small"
            elif effect_size_r < 0.5:
                effect_interpretation = "Medium"
            else:
                effect_interpretation = "Large"
            
            comparison = {
                'group1': treatment1,
                'group2': treatment2,
                'u_statistic': u_statistic,
                'p_value': p_value,
                'p_bonferroni': min(p_value * len(pairs), 1.0),
                'significant_uncorrected': p_value < alpha,
                'significant_bonferroni': p_value < bonferroni_alpha,
                'effect_size_r': effect_size_r,
                'effect_interpretation': effect_interpretation,
                'median_group1': group1.median(),
                'median_group2': group2.median(),
                'mean_rank_group1': group1.rank().mean(),
                'mean_rank_group2': group2.rank().mean(),
                'n_group1': n1,
                'n_group2': n2,
                'winner': treatment1 if group1.median() > group2.median() else treatment2
            }
            
            comparisons.append(comparison)
    
    return comparisons

def create_post_hoc_visualization(all_comparisons, save_path="post_hoc_analysis"):
    """
    Create visualization matrix of post-hoc results
    """
    os.makedirs(save_path, exist_ok=True)
    
    metrics = list(set([comp['metric'] for comp in all_comparisons]))
    
    for metric in metrics:
        metric_comparisons = [comp for comp in all_comparisons if comp['metric'] == metric]
        
        if not metric_comparisons:
            continue
        
        # Get unique treatments
        treatments = sorted(list(set([comp['group1'] for comp in metric_comparisons] + 
                                   [comp['group2'] for comp in metric_comparisons])))
        
        # Create matrices for p-values and effect sizes
        n_treatments = len(treatments)
        p_matrix = np.ones((n_treatments, n_treatments))
        effect_matrix = np.zeros((n_treatments, n_treatments))
        
        # Fill matrices
        for comp in metric_comparisons:
            i = treatments.index(comp['group1'])
            j = treatments.index(comp['group2'])
            
            # Use Bonferroni corrected p-values
            p_matrix[i, j] = comp['p_bonferroni']
            p_matrix[j, i] = comp['p_bonferroni']
            
            effect_matrix[i, j] = comp['effect_size_r']
            effect_matrix[j, i] = comp['effect_size_r']
        
        # Create subplot figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle(f'Post-Hoc Analysis Results for {metric.upper()}', fontsize=16, fontweight='bold')
        
        # Plot 1: P-values heatmap
        mask = np.eye(n_treatments, dtype=bool)  # Mask diagonal
        sns.heatmap(p_matrix, annot=True, fmt='.4f', mask=mask,
                   xticklabels=treatments, yticklabels=treatments,
                   cmap='RdYlBu_r', center=0.05, ax=ax1,
                   cbar_kws={'label': 'Bonferroni Corrected P-value'})
        ax1.set_title('P-Values Matrix\n(Red = Significant, Blue = Not Significant)')
        
        # Plot 2: Effect sizes heatmap
        sns.heatmap(effect_matrix, annot=True, fmt='.3f', mask=mask,
                   xticklabels=treatments, yticklabels=treatments,
                   cmap='viridis', ax=ax2,
                   cbar_kws={'label': 'Effect Size (r)'})
        ax2.set_title('Effect Sizes Matrix\n(Darker = Larger Effect)')
        
        plt.tight_layout()
        
        # Save plot
        filename = f"{save_path}/post_hoc_{metric}_matrix.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Post-hoc visualization saved: {filename}")
        
        plt.show()

def create_effect_size_summary(all_comparisons, save_path="post_hoc_analysis"):
    """
    Create summary plot of effect sizes across metrics
    """
    if not all_comparisons:
        return
    
    os.makedirs(save_path, exist_ok=True)
    
    # Convert to DataFrame for easier plotting
    df_comparisons = pd.DataFrame(all_comparisons)
    
    # Create comparison labels
    df_comparisons['comparison'] = df_comparisons['group1'] + ' vs ' + df_comparisons['group2']
    
    # Create subplot for each metric
    metrics = df_comparisons['metric'].unique()
    fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 4*len(metrics)))
    
    if len(metrics) == 1:
        axes = [axes]
    
    for i, metric in enumerate(metrics):
        metric_data = df_comparisons[df_comparisons['metric'] == metric]
        
        # Sort by effect size
        metric_data = metric_data.sort_values('effect_size_r', ascending=True)
        
        # Color by significance
        colors = ['red' if sig else 'gray' for sig in metric_data['significant_bonferroni']]
        
        # Create horizontal bar plot
        bars = axes[i].barh(range(len(metric_data)), metric_data['effect_size_r'], color=colors)
        axes[i].set_yticks(range(len(metric_data)))
        axes[i].set_yticklabels(metric_data['comparison'])
        axes[i].set_xlabel('Effect Size (r)')
        axes[i].set_title(f'{metric.upper()} - Effect Sizes (Red = Significant after Bonferroni)')
        axes[i].grid(True, alpha=0.3)
        
        # Add effect size interpretation lines
        axes[i].axvline(x=0.1, color='blue', linestyle='--', alpha=0.5, label='Small')
        axes[i].axvline(x=0.3, color='orange', linestyle='--', alpha=0.5, label='Medium') 
        axes[i].axvline(x=0.5, color='red', linestyle='--', alpha=0.5, label='Large')
        axes[i].legend()
    
    plt.tight_layout()
    
    # Save plot
    filename = f"{save_path}/effect_sizes_summary.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Effect sizes summary saved: {filename}")
    
    plt.show()

def comprehensive_post_hoc_analysis(df, metrics_to_analyze=None, save_path="post_hoc_analysis"):
    """
    Perform comprehensive post-hoc analysis for specified metrics
    """
    if df is None or df.empty:
        print("No data to analyze")
        return
    
    # Check Kruskal-Wallis results first
    if metrics_to_analyze is None:
        significant_metrics = check_kruskal_results()
        if not significant_metrics:
            print("\nNo significant metrics found in Kruskal-Wallis test.")
            print("Post-hoc analysis is only meaningful when the omnibus test is significant.")
            return
        metrics_to_analyze = significant_metrics
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    all_comparisons = []
    
    print("\n" + "="*80)
    print("POST-HOC PAIRWISE COMPARISONS ANALYSIS")
    print("="*80)
    print("Using Dunn's test (Mann-Whitney U with Bonferroni correction)")
    print("Only analyzing metrics with significant Kruskal-Wallis results")
    print("="*80)
    
    for metric in metrics_to_analyze:
        print(f"\n{metric.upper()} POST-HOC ANALYSIS:")
        print("-" * 50)
        
        # Perform post-hoc comparisons
        comparisons = perform_dunn_post_hoc(df, metric)
        
        if comparisons:
            # Add metric info to each comparison
            for comp in comparisons:
                comp['metric'] = metric
            
            all_comparisons.extend(comparisons)
            
            # Print significant results
            significant_comps = [c for c in comparisons if c['significant_bonferroni']]
            
            if significant_comps:
                print(f"\nSignificant pairwise differences (α = 0.05, Bonferroni corrected):")
                for comp in significant_comps:
                    winner_symbol = ">" if comp['median_group1'] > comp['median_group2'] else "<"
                    print(f"  {comp['group1']} {winner_symbol} {comp['group2']}: "
                          f"p={comp['p_bonferroni']:.4f}, r={comp['effect_size_r']:.3f} ({comp['effect_interpretation']})")
                    print(f"    Medians: {comp['median_group1']:.2f} vs {comp['median_group2']:.2f}")
            else:
                print("  No significant pairwise differences after Bonferroni correction")
            
            # Print summary of all comparisons
            print(f"\nSummary for {metric}:")
            total_comps = len(comparisons)
            sig_uncorrected = sum(1 for c in comparisons if c['significant_uncorrected'])
            sig_corrected = sum(1 for c in comparisons if c['significant_bonferroni'])
            
            print(f"  Total comparisons: {total_comps}")
            print(f"  Significant (uncorrected): {sig_uncorrected}")
            print(f"  Significant (Bonferroni): {sig_corrected}")
    
    # Save results to CSV
    if all_comparisons:
        results_df = pd.DataFrame(all_comparisons)
        results_filename = f"{save_path}/post_hoc_comparisons.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"\nPost-hoc results saved: {results_filename}")
        
        # Create visualizations
        create_post_hoc_visualization(all_comparisons, save_path)
        create_effect_size_summary(all_comparisons, save_path)
        
        # Print final summary
        print("\n" + "="*80)
        print("POST-HOC ANALYSIS SUMMARY")
        print("="*80)
        
        metrics_with_significant = list(set([c['metric'] for c in all_comparisons 
                                           if c['significant_bonferroni']]))
        
        if metrics_with_significant:
            print(f"Metrics with significant pairwise differences: {', '.join(metrics_with_significant)}")
            print("Check the visualization files for detailed comparison matrices")
        else:
            print("No significant pairwise differences found after multiple comparison correction")
            print("This suggests that while the omnibus test was significant,")
            print("the individual pairwise differences are not strong enough to survive correction")
    
    return all_comparisons

def main():
    """
    Main function to perform post-hoc analysis
    """
    print("Starting Post-Hoc Pairwise Comparisons Analysis...")
    print("="*60)
    print("This analysis should only be run AFTER Kruskal-Wallis test")
    print("and only for metrics that showed significant omnibus effects")
    print("="*60)
    
    # Load data
    df = load_all_treatment_data()
    
    if df is not None:
        # Perform comprehensive post-hoc analysis
        comparisons = comprehensive_post_hoc_analysis(df)
        
        print("\n" + "="*60)
        print("Post-Hoc Analysis Complete!")
        print("Check the 'post_hoc_analysis' folder for:")
        print("- Detailed pairwise comparisons (CSV)")
        print("- P-value and effect size matrices (PNG)")
        print("- Effect size summary plots (PNG)")
        print("="*60)
    else:
        print("Failed to load data. Please check your data files.")

if __name__ == "__main__":
    main()
