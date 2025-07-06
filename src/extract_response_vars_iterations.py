import sqlite3
import pandas as pd
from datetime import datetime
import os
import pytz

# === CONFIGURATION ===
db_path = "data/raw/database.db"
local_tz = pytz.timezone('America/Costa_Rica')
verbose = False  # Set to True to enable detailed logging

# Format: (iteration_number, start_year, start_month, start_day, start_hour, start_minute,
#                       end_year,   end_month,   end_day,   end_hour,   end_minute)
# ========== TRATAMIENTO T1 ==========
iterations1 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 11, 18, 0, 2025, 6, 12, 6, 0),
]

# ========== TRATAMIENTO T2 ==========
iterations2 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 22, 21, 2, 2025, 6, 28, 16, 10),
]

# ========== TRATAMIENTO T3 ==========
iterations3 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 12, 23, 0, 2025, 6, 14, 16, 0),
    ("2", 2025, 6, 21, 22, 20, 2025, 6, 22, 12, 0),
]

# ========== TRATAMIENTO T4 ==========
iterations4 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    # ("1", 2025, 6, 19, 11, 0, 2025, 6, 19, 11, 0),  # Eliminado - comentado
    ("1", 2025, 6, 21, 18, 0, 2025, 6, 21, 22, 0),
]

# ========== TRATAMIENTO T5 ==========
iterations5 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 14, 16, 0, 2025, 6, 19, 10, 0),
    ("2", 2025, 6, 21, 15, 0, 2025, 6, 21, 18, 0),
]

# ========== TRATAMIENTO T6 ==========
iterations6 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    ("1", 2025, 6, 20, 21, 9, 2025, 6, 21, 15, 0),
    ("2", 2025, 6, 22, 15, 2, 2025, 6, 22, 18, 0),
    ("3", 2025, 6, 28, 16, 10, 2025, 6, 30, 23, 10),  # En progreso - sin fecha fin
]

# ========== TRATAMIENTO T7 ==========
iterations7 = [
    #(itr, st_yr, st_mon, st_day, st_hr, st_min,  end_yr, end_mo, end_day, end_hr, end_min)
    # ("1", 2025, 6, 12, 9, 0, 2025, 6, 12, 23, 0),   # Eliminado por mod - comentado
    ("1", 2025, 6, 20, 18, 9, 2025, 6, 20, 20, 59),
    ("2", 2025, 6, 22, 18, 0, 2025, 6, 22, 21, 0),
]

def trim_inactive_periods(df, max_minutes_without_players=20):
    """
    Trims periods of inactivity longer than the specified minutes.
    Instead of discarding the entire iteration, it removes only the excessive inactive periods.
    
    Args:
        df: DataFrame with the data
        max_minutes_without_players: Maximum minutes allowed without players
        
    Returns:
        Tuple: (List of DataFrames representing active periods, dict with statistics)
    """
    if df.empty:
        return [], {"total_minutes": 0, "accepted_minutes": 0, "rejected_minutes": 0, "discarded_segments": []}
    
    # Sort by date to ensure chronological order
    df_sorted = df.sort_values("date").copy().reset_index(drop=True)
    
    # Fill NaN values with 0 for players_online
    df_sorted["players_online"] = df_sorted["players_online"].fillna(0)
    
    # Calculate total duration in minutes
    total_duration = (df_sorted["date"].iloc[-1] - df_sorted["date"].iloc[0]).total_seconds() / 60
    
    # Find consecutive periods with 0 players
    no_players_mask = df_sorted["players_online"] == 0
    
    if not no_players_mask.any():
        stats = {
            "total_minutes": total_duration,
            "accepted_minutes": total_duration,
            "rejected_minutes": 0,
            "discarded_segments": []
        }
        return [df_sorted], stats  # No periods without players, return original data
    
    # Group consecutive periods without players
    groups = (no_players_mask != no_players_mask.shift()).cumsum()
    
    active_periods = []
    current_start = 0
    discarded_segments = []
    total_rejected_minutes = 0
    
    # Process each group to find long inactive periods
    for group_id in groups.unique():
        group_mask = groups == group_id
        group_data = df_sorted[group_mask]
        
        if group_data["players_online"].iloc[0] == 0 and len(group_data) >= 2:
            # This is an inactive period
            start_time = group_data["date"].iloc[0]
            end_time = group_data["date"].iloc[-1]
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            if duration_minutes > max_minutes_without_players:
                # Long inactive period found
                group_start_idx = group_data.index[0]
                group_end_idx = group_data.index[-1]
                
                # Calculate the cut point (keep only first max_minutes_without_players)
                max_duration_seconds = max_minutes_without_players * 60
                cut_time = start_time + pd.Timedelta(seconds=max_duration_seconds)
                
                # Find the index closest to the cut time within the inactive period
                cut_mask = group_data["date"] <= cut_time
                if cut_mask.any():
                    cut_idx = group_data[cut_mask].index[-1]
                    discarded_start = df_sorted.iloc[cut_idx]["date"]
                else:
                    cut_idx = group_start_idx
                    discarded_start = start_time
                
                # Calculate rejected time
                rejected_minutes = (end_time - discarded_start).total_seconds() / 60
                total_rejected_minutes += rejected_minutes
                
                # Record discarded segment
                discarded_segments.append({
                    "start": discarded_start.strftime('%H:%M'),
                    "end": end_time.strftime('%H:%M'),
                    "duration": rejected_minutes
                })
                
                # Add active period before the long inactive period
                if current_start < group_start_idx:
                    active_periods.append(df_sorted.iloc[current_start:group_start_idx])
                
                # Add the allowed portion of inactive period
                if current_start <= cut_idx:
                    active_periods.append(df_sorted.iloc[max(current_start, group_start_idx):cut_idx + 1])
                
                if verbose:
                    print(f"  Trimmed inactive period: {duration_minutes:.1f} minutes ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}) -> kept first {max_minutes_without_players} minutes")
                    print(f"  Discarded segment: {discarded_start.strftime('%H:%M')} - {end_time.strftime('%H:%M')} ({rejected_minutes:.1f} minutes)")
                
                # Set next start after the long inactive period
                current_start = group_end_idx + 1
    
    # Add remaining data after the last processed group
    if current_start < len(df_sorted):
        active_periods.append(df_sorted.iloc[current_start:])
    
    # Filter out empty periods
    active_periods = [period for period in active_periods if not period.empty]
    
    # Calculate accepted minutes
    accepted_minutes = total_duration - total_rejected_minutes
    
    stats = {
        "total_minutes": total_duration,
        "accepted_minutes": accepted_minutes,
        "rejected_minutes": total_rejected_minutes,
        "discarded_segments": discarded_segments
    }
    
    return active_periods, stats

def  extract_response_variables(filename, iterations, treatment_number, max_minutes_without_players=20):
    """
    Extracts response variables from the database for specified iterations.
    Each iteration is defined by a start and end time.
    
    Args:
        filename: Name for the output file
        iterations: List of iteration tuples with time ranges
        treatment_number: Treatment number
        max_minutes_without_players: Maximum minutes allowed without players before terminating iteration (default: 20)
    """
    if verbose:
        print(f"\n--- PROCESSING TREATMENT T{treatment_number} ---")
        print(f"Max minutes without players: {max_minutes_without_players}")
        print(f"Total iterations to process: {len(iterations)}")

    # Output folder
    output_folder = "data/processed/response_variables"
    os.makedirs(output_folder, exist_ok=True)

    # DataFrame to store all iterations
    all_data = []
    
    # Statistics tracking
    treatment_stats = {
        "total_minutes": 0,
        "accepted_minutes": 0,
        "rejected_minutes": 0,
        "total_discarded_segments": 0
    }

        # Process each iteration
    for iteration, sy, sM, sd, sh, sm, ey, eM, ed, eh, em in iterations:
        local_start = local_tz.localize(datetime(sy, sM, sd, sh, sm, 0))
        local_end = local_tz.localize(datetime(ey, eM, ed, eh, em, 0))
        start_time = int(local_start.astimezone(pytz.utc).timestamp() * 1000)
        end_time = int(local_end.astimezone(pytz.utc).timestamp() * 1000)

        if verbose:
            print(f"Processing Iteration {iteration}: {local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}")

        conn = sqlite3.connect(db_path)

        # Query TPS, CPU, RAM, and players online
        query = """
        SELECT
            tps.date,
            tps.tps,
            tps.cpu_usage,
            tps.ram_usage,
            tps.players_online
        FROM plan_tps tps
        WHERE tps.date BETWEEN ? AND ?
        ORDER BY tps.date ASC
        """
        df = pd.read_sql_query(query, conn, params=(start_time, end_time))
        df["date"] = pd.to_datetime(df["date"], unit="ms").dt.tz_localize('UTC').dt.tz_convert(local_tz)

        # Ensure all numeric columns have consistent dtypes
        numeric_columns = ['tps', 'cpu_usage', 'ram_usage', 'players_online']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Check for presence of players
        if df["players_online"].fillna(0).sum() == 0:
            print(f"Warning: No players online during Iteration {iteration} (T{treatment_number})")

        # Trim periods of inactivity longer than specified minutes
        active_periods, iteration_stats = trim_inactive_periods(df, max_minutes_without_players)
        
        # Update treatment statistics
        treatment_stats["total_minutes"] += iteration_stats["total_minutes"]
        treatment_stats["accepted_minutes"] += iteration_stats["accepted_minutes"]
        treatment_stats["rejected_minutes"] += iteration_stats["rejected_minutes"]
        treatment_stats["total_discarded_segments"] += len(iteration_stats["discarded_segments"])
        
        if not active_periods:
            print(f"WARNING: Iteration {iteration} (T{treatment_number}) has no active periods after trimming")
            continue  # Skip this iteration
        
        # Process each active period as a separate segment
        for segment_idx, active_df in enumerate(active_periods):
            # Add treatment and iteration columns with consistent dtypes
            active_df = active_df.copy()
            active_df["treatment"] = f"T{treatment_number}"
            active_df["iteration"] = str(f"{iteration}_{segment_idx + 1}" if len(active_periods) > 1 else iteration)
            
            # Ensure all DataFrames have the same column order and types
            expected_columns = ['date', 'tps', 'cpu_usage', 'ram_usage', 'players_online', 'treatment', 'iteration']
            for col in expected_columns:
                if col not in active_df.columns:
                    if col in numeric_columns:
                        active_df[col] = pd.Series(dtype='float64')
                    else:
                        active_df[col] = pd.Series(dtype='object')
            
            # Reorder columns to ensure consistency
            active_df = active_df[expected_columns]
            
            all_data.append(active_df)
        conn.close()

    # Check if we have valid data to export
    if not all_data:
        print(f"ERROR: No valid data found for Treatment T{treatment_number}. No CSV file will be created.")
        print("-" * 60)
        return

    # Filter out any empty DataFrames that might have been created
    valid_data = [df for df in all_data if not df.empty and len(df) > 0]

    if not valid_data:
        print(f"ERROR: No valid data found for Treatment T{treatment_number} after filtering. No CSV file will be created.")
        print("-" * 60)
        return

    # Combine all active periods into a single DataFrame
    final_df = pd.concat(valid_data, ignore_index=True, sort=False)

    # Export to a single CSV file
    output_path = os.path.join(output_folder, f"T{treatment_number}_response_variables_"+ filename + ".csv")
    final_df.to_csv(output_path, index=False)
    print(f"\nFinal CSV exported: {output_path}")

    if verbose:
        print(f"Total active segments processed: {len(all_data)}")
        print(f"Total data points: {len(final_df)}")
        # Show treatment summary statistics
        print("\n--- TREATMENT SUMMARY ---")
        print(f"Total original duration: {treatment_stats['total_minutes']:.1f} minutes")
        print(f"Accepted duration: {treatment_stats['accepted_minutes']:.1f} minutes ({(treatment_stats['accepted_minutes'])/60:.2f} hours) ({(treatment_stats['accepted_minutes']/treatment_stats['total_minutes']*100):.1f}%)")
        print(f"Rejected duration: {treatment_stats['rejected_minutes']:.1f} minutes ({(treatment_stats['rejected_minutes']/treatment_stats['total_minutes']*100):.1f}%)")
        print(f"Total discarded segments: {treatment_stats['total_discarded_segments']}")
        print("-" * 60)
    return treatment_stats

def display_treatment_summary_table(all_treatment_stats):
    """Display treatment statistics in a clean table format"""
    import pandas as pd
    
    # Convert stats to DataFrame
    summary_data = []
    for treatment_num, stats in all_treatment_stats.items():
        summary_data.append({
            'Treatment': f'T{treatment_num}',
            'Total Minutes': f"{stats['total_minutes']:.1f}",
            'Accepted Minutes': f"{stats['accepted_minutes']:.1f}",
            'Accepted Hours': f"{stats['accepted_minutes']/60:.2f}",
            'Retention %': f"{(stats['accepted_minutes']/stats['total_minutes']*100):.1f}%" if stats['total_minutes'] > 0 else "0%",
            'Rejected Minutes': f"{stats['rejected_minutes']:.1f}",
            'Discarded Segments': stats['total_discarded_segments']
        })
    
    df = pd.DataFrame(summary_data)
    print("\n" + "="*80)
    print("TREATMENT SUMMARY TABLE")
    print("="*80)
    print(df.to_string(index=False))
    print("="*80)

# Option 2: Rich library for beautiful console tables
def display_rich_table(all_treatment_stats):
    """Display results using the rich library for beautiful formatting"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.layout import Layout
        from rich.progress import Progress, BarColumn, TextColumn
        
        console = Console()
        
        # Create main table
        table = Table(title="Treatment Processing Summary", show_header=True, header_style="bold magenta")
        table.add_column("Treatment", style="cyan", justify="center")
        table.add_column("Total Time", justify="right")
        table.add_column("Accepted", justify="right", style="green")
        table.add_column("Rejected", justify="right", style="red")
        table.add_column("Retention", justify="right", style="yellow")
        table.add_column("Segments", justify="right")
        
        total_original = 0
        total_accepted = 0
        total_rejected = 0
        total_segments = 0
        
        for treatment_num, stats in all_treatment_stats.items():
            total_original += stats['total_minutes']
            total_accepted += stats['accepted_minutes']
            total_rejected += stats['rejected_minutes']
            total_segments += stats['total_discarded_segments']
            
            retention_pct = (stats['accepted_minutes']/stats['total_minutes']*100) if stats['total_minutes'] > 0 else 0
            
            table.add_row(
                f"T{treatment_num}",
                f"{stats['total_minutes']:.1f}m",
                f"{stats['accepted_minutes']:.1f}m ({stats['accepted_minutes']/60:.1f}h)",
                f"{stats['rejected_minutes']:.1f}m",
                f"{retention_pct:.1f}%",
                str(stats['total_discarded_segments'])
            )
        
        # Add totals row
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total_original:.1f}m[/bold]",
            f"[bold]{total_accepted:.1f}m ({total_accepted/60:.1f}h)[/bold]",
            f"[bold]{total_rejected:.1f}m[/bold]",
            f"[bold]{(total_accepted/total_original*100):.1f}%[/bold]" if total_original > 0 else "[bold]0%[/bold]",
            f"[bold]{total_segments}[/bold]"
        )
        
        console.print(table)
        
        # Add summary panel
        summary_text = f"""
        Overall Statistics:
        • Total Original Data: {total_original/60:.1f} hours
        • Data Retained: {total_accepted/60:.1f} hours ({(total_accepted/total_original*100):.1f}%)
        • Data Discarded: {total_rejected/60:.1f} hours ({(total_rejected/total_original*100):.1f}%)
        • Segments Removed: {total_segments}
        """
        
        console.print(Panel(summary_text, title="Processing Summary", border_style="green"))
        
    except ImportError:
        print("Rich library not installed. Install with: pip install rich")
        display_treatment_summary_table(all_treatment_stats)


if __name__ == "__main__":
    print("=" * 60)
    print("STARTING RESPONSE VARIABLES EXTRACTION")
    print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Dictionary to store all treatment statistics
    all_treatment_stats = {}
    
    # Process each treatment and collect stats
    treatments = [
        ("treatment1", iterations1, 1),
        ("treatment2", iterations2, 2),
        ("treatment3", iterations3, 3),
        ("treatment4", iterations4, 4),
        ("treatment5", iterations5, 5),
        ("treatment6", iterations6, 6),
        ("treatment7", iterations7, 7)
    ]
    
    for filename, iterations, treatment_num in treatments:
        # You'd need to modify extract_response_variables to return stats
        stats = extract_response_variables(filename, iterations, treatment_num)
        if stats:  # Only add if processing was successful
            all_treatment_stats[treatment_num] = stats
    
    # Display results in a beautiful format
    print("\n" + "="*60)
    print("PROCESSING COMPLETE - GENERATING SUMMARY")
    print("="*60)

    # Try rich table first, fall back to pandas if not available
    display_rich_table(all_treatment_stats)
