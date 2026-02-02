import click
import pandas as pd
from pathlib import Path

BASE_DIR = Path("data/input")

@click.group(epilog="Example: python3 src/cli.py show pm 0 --limit 10")
def cli():
    """📡 RadioRCA CLI: Navigate and inspect your cleaned Telecom data.
    
    This tool allows you to browse through archived PM, CM, Database, and RF files.
    Use 'list' to see file indexes and 'show' to view data.
    """
    pass

@cli.command()
@click.argument('data_type', type=click.Choice(['pm', 'cm', 'database', 'rf']))
@click.argument('index', type=int, required=False)
@click.option('--limit', default=5, type=int, help='Number of rows to display (default: 5).')
@click.option('--all', is_flag=True, help='Combine all files in the archive into one view.')
def show(data_type, index, limit, all):
    """View a snapshot of data from the archive.
    
    DATA_TYPE: The category (pm, cm, database, or rf).
    
    INDEX: The file number (0=latest, 1=previous, etc.). Run 'list' to see indexes.
    """
    archive_path = BASE_DIR / data_type / "archive"
    
    clean_files = sorted(
        archive_path.glob("clean_*.csv"), 
        key=lambda x: x.stat().st_mtime, 
        reverse=True
    )

    if not clean_files:
        click.echo(f"Error: No cleaned {data_type} files found in {archive_path}")
        return

    if all:
        click.echo(f"Processing aggregation of {len(clean_files)} files...")
        df = pd.concat([pd.read_csv(f) for f in clean_files], ignore_index=True)
    else:
        target_index = index if index is not None else 0
        if target_index >= len(clean_files):
            click.echo(f"Error: Index {target_index} is invalid. Max index is {len(clean_files)-1}.")
            return
            
        target_file = clean_files[target_index]
        click.echo(f"Reading [{target_index}]: {target_file.name}")
        df = pd.read_csv(target_file)
    
    click.echo("-" * 30)
    click.echo(df.head(limit).to_string(index=False))
    click.echo("-" * 30)
    click.echo(f"Summary: {len(df)} rows | Columns: {list(df.columns)}")

@cli.command(name='kpi')
@click.option('--show-all', is_flag=True, help='Show all headers even if they are in only one file.')
def kpis_matrix(show_all):
    """Correlation Discovery: Matrix of available IDs and KPIs."""
    archive_path = BASE_DIR / "pm" / "archive"
    
    clean_files = sorted(
        archive_path.glob("clean_*.csv"), 
        key=lambda x: x.stat().st_mtime, 
        reverse=True
    )

    if not clean_files:
        click.secho("No PM archives found.", fg='red')
        return

    click.echo(f"Analyzing {len(clean_files)} files for IDs and Counters...")
    
    kpi_map = []
    # We now track which identifiers are present too
    id_cols = ['Date', 'ERBS Id', 'EUtranCell Id', 'Local Cell Id', 'Cell ID']

    for i, f in enumerate(clean_files):
        df_headers = pd.read_csv(f, nrows=0)
        # We process ALL columns now
        for col in df_headers.columns:
            kpi_map.append({'Header': col, 'File_Index': i, 'Is_ID': col in id_cols})

    matrix_df = pd.DataFrame(kpi_map)
    pivot_df = pd.crosstab(matrix_df['Header'], matrix_df['File_Index'])
    
    # Calculate Coverage
    total_files = len(clean_files)
    pivot_df['Coverage %'] = (pivot_df.sum(axis=1) / total_files * 100).round(1)
    
    # Create the display version
    display_df = pivot_df.drop(columns=['Coverage %']).map(lambda x: 'X' if x > 0 else '.')
    display_df['Coverage %'] = pivot_df['Coverage %'].astype(str) + '%'

    # Separate IDs from KPIs for a cleaner view
    all_headers = pivot_df.index.tolist()
    found_ids = [h for h in all_headers if h in id_cols]
    found_kpis = [h for h in all_headers if h not in id_cols]

    click.secho("\n🔑 IDENTIFIERS (Join Keys)", fg='yellow', bold=True)
    click.echo(display_df.loc[found_ids].to_string())

    click.secho("\n📊 PERFORMANCE COUNTERS", fg='green', bold=True)
    kpi_display = display_df.loc[found_kpis]
    
    if not show_all:
        # Hide unique one-off counters unless --show-all is used
        kpi_display = kpi_display[pivot_df.loc[found_kpis, 'Coverage %'] > (100/total_files)]
    
    click.echo(kpi_display.to_string())
    
    if not show_all and len(found_kpis) > len(kpi_display):
        click.echo(f"\n... {len(found_kpis) - len(kpi_display)} more unique KPIs hidden. Use --show-all to see everything.")


@cli.command(name='headers')
@click.option('--data_type', type=click.Choice(['pm', 'cm', 'database', 'rf']), help='Filter to a specific folder.')
def show_headers(data_type):
    """Universal Matrix: Shows headers and IDs across all data categories."""
    folders = [data_type] if data_type else ['pm', 'cm', 'database', 'rf']
    
    for folder in folders:
        archive_path = BASE_DIR / folder / "archive"
        clean_files = sorted(
            archive_path.glob("clean_*.csv"), 
            key=lambda x: x.stat().st_mtime, 
            reverse=True
        )

        if not clean_files:
            continue

        click.secho(f"\n📁 {folder.upper()} HEADER MATRIX", fg='cyan', bold=True, underline=True)
        
        header_map = []
        for i, f in enumerate(clean_files):
            # Read only the header row
            df_headers = pd.read_csv(f, nrows=0)
            for col in df_headers.columns:
                header_map.append({'Header': col, 'File_Index': i})

        if not header_map:
            continue

        matrix_df = pd.DataFrame(header_map)
        pivot_df = pd.crosstab(matrix_df['Header'], matrix_df['File_Index'])
        
        # Mark presence with 'X'
        display_df = pivot_df.map(lambda x: 'X' if x > 0 else '.')
        
        click.echo(display_df.to_string())
        click.echo("-" * 40)



@cli.command(name='list')
def list_data():
    """List all archived files and their corresponding Index numbers."""
    for folder in ['pm', 'cm', 'database', 'rf']:
        p = BASE_DIR / folder / "archive"
        files = sorted(
            p.glob("clean_*.csv"), 
            key=lambda x: x.stat().st_mtime, 
            reverse=True
        ) if p.exists() else []
        
        click.secho(f"\n📁 {folder.upper()} ARCHIVE", fg='cyan', bold=True)
        if not files:
            click.echo("  (No files found)")
        for i, f in enumerate(files):
            click.echo(f"  [{i}] {f.name}")

if __name__ == "__main__":
    cli()