import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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

def create_interactive_dashboard(df_summary, df_raw=None, save_path="interactive"):
    """
    Create an interactive dashboard with multiple views
    """
    if df_summary is None or df_summary.empty:
        print("No summary data to plot")
        return
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'TPS Performance by Treatment',
            'CPU Usage by Treatment', 
            'RAM Usage by Treatment',
            'Performance Metrics Comparison',
            'Variability Analysis',
            'Performance Score Ranking'
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}]
        ]
    )
    
    # Colors for treatments
    colors = px.colors.qualitative.Set3[:len(df_summary)]
    
    # 1. TPS Performance (Box-like plot with min, mean, max)
    for i, (_, row) in enumerate(df_summary.iterrows()):
        fig.add_trace(
            go.Scatter(
                x=[row['treatment'], row['treatment'], row['treatment']],
                y=[row['tps_min'], row['tps_mean'], row['tps_max']],
                mode='markers+lines',
                name=f"{row['treatment']} TPS",
                marker=dict(color=colors[i], size=[8, 12, 8]),
                line=dict(color=colors[i]),
                showlegend=False
            ),
            row=1, col=1
        )
    
    # 2. CPU Usage Bar Chart
    fig.add_trace(
        go.Bar(
            x=df_summary['treatment'],
            y=df_summary['cpu_mean'],
            name='CPU Usage',
            marker_color=colors,
            text=[f"{val:.1f}%" for val in df_summary['cpu_mean']],
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. RAM Usage Bar Chart
    fig.add_trace(
        go.Bar(
            x=df_summary['treatment'],
            y=df_summary['ram_mean'],
            name='RAM Usage',
            marker_color=colors,
            text=[f"{val:.0f} MB" for val in df_summary['ram_mean']],
            textposition='outside',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 4. Performance Metrics Radar Chart (normalized)
    # Normalize metrics
    tps_norm = (df_summary['tps_mean'] - df_summary['tps_mean'].min()) / (df_summary['tps_mean'].max() - df_summary['tps_mean'].min())
    cpu_norm = 1 - ((df_summary['cpu_mean'] - df_summary['cpu_mean'].min()) / (df_summary['cpu_mean'].max() - df_summary['cpu_mean'].min()))
    ram_norm = 1 - ((df_summary['ram_mean'] - df_summary['ram_mean'].min()) / (df_summary['ram_mean'].max() - df_summary['ram_mean'].min()))
    
    # Create heatmap instead of radar for subplot compatibility
    heatmap_data = []
    for i, treatment in enumerate(df_summary['treatment']):
        heatmap_data.append([tps_norm.iloc[i], cpu_norm.iloc[i], ram_norm.iloc[i]])
    
    fig.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=['TPS Score', 'CPU Score', 'RAM Score'],
            y=df_summary['treatment'],
            colorscale='RdYlGn',
            showscale=True,
            zmin=0, zmax=1
        ),
        row=2, col=2
    )
    
    # 5. Variability Analysis (Range bars)
    tps_range = df_summary['tps_max'] - df_summary['tps_min']
    cpu_range = df_summary['cpu_max'] - df_summary['cpu_min']
    ram_range = df_summary['ram_max'] - df_summary['ram_min']
    
    fig.add_trace(
        go.Bar(
            x=df_summary['treatment'],
            y=tps_range,
            name='TPS Range',
            marker_color='lightblue',
            opacity=0.7,
            showlegend=False
        ),
        row=3, col=1
    )
    
    # 6. Performance Score Ranking
    composite_score = (tps_norm + cpu_norm + ram_norm) / 3
    sorted_indices = composite_score.sort_values(ascending=False).index
    
    fig.add_trace(
        go.Bar(
            x=df_summary['treatment'].iloc[sorted_indices],
            y=composite_score.iloc[sorted_indices],
            name='Performance Score',
            marker_color='purple',
            text=[f"{val:.3f}" for val in composite_score.iloc[sorted_indices]],
            textposition='outside',
            showlegend=False
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title_text="Minecraft Server Performance Analysis Dashboard",
        title_x=0.5,
        title_font_size=20,
        showlegend=False
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Treatment", row=1, col=1)
    fig.update_yaxes(title_text="TPS", row=1, col=1)
    
    fig.update_xaxes(title_text="Treatment", row=1, col=2)
    fig.update_yaxes(title_text="CPU Usage (%)", row=1, col=2)
    
    fig.update_xaxes(title_text="Treatment", row=2, col=1)
    fig.update_yaxes(title_text="RAM Usage (MB)", row=2, col=1)
    
    fig.update_xaxes(title_text="Metric", row=2, col=2)
    fig.update_yaxes(title_text="Treatment", row=2, col=2)
    
    fig.update_xaxes(title_text="Treatment", row=3, col=1)
    fig.update_yaxes(title_text="TPS Range", row=3, col=1)
    
    fig.update_xaxes(title_text="Treatment (Ranked)", row=3, col=2)
    fig.update_yaxes(title_text="Score", row=3, col=2)
    
    # Save as HTML
    filename = f"{save_path}/performance_dashboard.html"
    fig.write_html(filename)
    print(f"Saved interactive dashboard: {filename}")
    
    # Show the plot
    fig.show()

def create_time_series_plot(df_raw, save_path="interactive"):
    """
    Create an interactive time series plot if raw data is available
    """
    if df_raw is None or df_raw.empty:
        print("No raw data available for time series plot")
        return
    
    # Create time series plot
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('TPS Over Time', 'CPU Usage Over Time', 'RAM Usage Over Time'),
        shared_xaxes=True,
        vertical_spacing=0.08
    )
    
    # Get unique treatments and colors
    treatments = sorted(df_raw['treatment'].unique())
    colors = px.colors.qualitative.Set3[:len(treatments)]
    
    for i, treatment in enumerate(treatments):
        treatment_data = df_raw[df_raw['treatment'] == treatment]
        
        # TPS
        fig.add_trace(
            go.Scatter(
                x=treatment_data['date'],
                y=treatment_data['tps'],
                mode='lines',
                name=f'{treatment} TPS',
                line=dict(color=colors[i]),
                legendgroup=treatment
            ),
            row=1, col=1
        )
        
        # CPU
        fig.add_trace(
            go.Scatter(
                x=treatment_data['date'],
                y=treatment_data['cpu_usage'],
                mode='lines',
                name=f'{treatment} CPU',
                line=dict(color=colors[i]),
                legendgroup=treatment,
                showlegend=False
            ),
            row=2, col=1
        )
        
        # RAM
        fig.add_trace(
            go.Scatter(
                x=treatment_data['date'],
                y=treatment_data['ram_usage'],
                mode='lines',
                name=f'{treatment} RAM',
                line=dict(color=colors[i]),
                legendgroup=treatment,
                showlegend=False
            ),
            row=3, col=1
        )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text="Performance Metrics Over Time",
        title_x=0.5,
        title_font_size=18
    )
    
    # Update axes
    fig.update_yaxes(title_text="TPS", row=1, col=1)
    fig.update_yaxes(title_text="CPU Usage (%)", row=2, col=1)
    fig.update_yaxes(title_text="RAM Usage (MB)", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    
    # Save as HTML
    filename = f"{save_path}/time_series_plot.html"
    fig.write_html(filename)
    print(f"Saved time series plot: {filename}")
    
    fig.show()

def create_3d_scatter_plot(df_summary, save_path="interactive"):
    """
    Create a 3D scatter plot showing the relationship between all three metrics
    """
    if df_summary is None or df_summary.empty:
        print("No data for 3D plot")
        return
    
    fig = go.Figure(data=[go.Scatter3d(
        x=df_summary['tps_mean'],
        y=df_summary['cpu_mean'],
        z=df_summary['ram_mean'],
        mode='markers+text',
        marker=dict(
            size=12,
            color=df_summary['tps_mean'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="TPS Mean")
        ),
        text=df_summary['treatment'],
        textposition="middle center",
        hovertemplate='<b>%{text}</b><br>' +
                     'TPS: %{x:.2f}<br>' +
                     'CPU: %{y:.2f}%<br>' +
                     'RAM: %{z:.0f} MB<extra></extra>'
    )])
    
    fig.update_layout(
        title='3D Performance Metrics Visualization',
        scene=dict(
            xaxis_title='TPS (Mean)',
            yaxis_title='CPU Usage % (Mean)',
            zaxis_title='RAM Usage MB (Mean)'
        ),
        width=800,
        height=600
    )
    
    # Save as HTML
    filename = f"{save_path}/3d_scatter_plot.html"
    fig.write_html(filename)
    print(f"Saved 3D scatter plot: {filename}")
    
    fig.show()

def main():
    """
    Main function to generate all interactive visualizations
    """
    print("Loading data...")
    df_summary = load_summary_data()
    df_raw = load_raw_data()
    
    if df_summary is not None:
        print("\nGenerating interactive dashboard...")
        create_interactive_dashboard(df_summary, df_raw)
        
        print("\nGenerating 3D scatter plot...")
        create_3d_scatter_plot(df_summary)
        
        if df_raw is not None:
            print("\nGenerating time series plot...")
            create_time_series_plot(df_raw)
        else:
            print("Raw data not available for time series plot")
        
        print("\nInteractive visualization generation complete!")
        print("Check the 'interactive' folder for HTML files.")
        print("Open the HTML files in your web browser to view interactive plots.")
    else:
        print("Failed to load summary data.")

if __name__ == "__main__":
    main()
