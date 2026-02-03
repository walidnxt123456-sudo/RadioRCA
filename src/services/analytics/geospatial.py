import pandas as pd
import numpy as np
from ..rca_utils import get_latest_clean_file

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculates the bearing (angle) from Point 1 (Site) to Point 2 (User)."""
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    d_lambda = np.radians(lon2 - lon1)
    y = np.sin(d_lambda) * np.cos(phi2)
    x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(d_lambda)
    return (np.degrees(np.arctan2(y, x)) + 360) % 360

def haversine(lat1, lon1, lat2, lon2):
    """Standard distance calculation."""
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi, dlambda = np.radians(lat2-lat1), np.radians(lon2-lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def analyze(ctx):
    u_lat, u_lon = ctx.get('latitude'), ctx.get('longitude')
    
    # 1. Professional Input Request
    print("\n" + "-"*60)
    limit_input = input("🔢 Specify the number of nearest SITES to evaluate (default 1): ").strip()
    site_limit = int(limit_input) if limit_input and limit_input.isdigit() else 1

    file_path = get_latest_clean_file("database", "database_")
    if not file_path: return print("⚠️ Clean database not found.")

    df = pd.read_csv(file_path)
    
    # FIX: Correct string accessor for index
    df.columns = df.columns.str.strip().str.lower()

    # Identify columns
    lat_col = next(c for c in df.columns if 'lat' in c)
    lon_col = next(c for c in df.columns if 'lon' in c)
    azi_col = next((c for c in df.columns if 'azi' in c), None)
    site_col = next((c for c in df.columns if 'site' in c), df.columns[0])
    cell_col = next((c for c in df.columns if 'cell' in c), site_col)

    # 2. Calculate Distance for every row
    df['distance_km'] = df.apply(lambda r: haversine(u_lat, u_lon, float(r[lat_col]), float(r[lon_col])), axis=1)
    
    # 3. Get unique nearest Site IDs
    unique_nearest_sites = df.sort_values('distance_km')[site_col].unique()[:site_limit]
    
    print(f"\n🌍 User Coordinates: {u_lat}, {u_lon}")
    print("="*85)
    print(f"{'SITE ID':<12} | {'CELL NAME':<20} | {'DIST (km)':<10} | {'AZI':<5} | {'BEARING'}")
    print("-" * 85)

    for site in unique_nearest_sites:
        # Get all cells belonging to this site
        site_cells = df[df[site_col] == site].copy()
        
        for _, row in site_cells.iterrows():
            angle_to_user = calculate_bearing(row[lat_col], row[lon_col], u_lat, u_lon)
            
            # Directional Insight
            status = ""
            if azi_col:
                diff = abs(row[azi_col] - angle_to_user)
                if diff > 180: diff = 360 - diff
                if diff <= 35: status = "🎯 [DIRECT]"
                elif diff > 120: status = "❌ [BACK]"

            print(f"{str(row[site_col]):<12} | "
                  f"{str(row[cell_col]):<20} | "
                  f"{row['distance_km']:<10.2f} | "
                  f"{int(row[azi_col]) if azi_col else 'N/A':<5} | "
                  f"{int(angle_to_user):>3}° {status}")
        print("-" * 85) # Separator between different sites

    # RCA Insight
    best_dist = df['distance_km'].min()
    if best_dist > 3.5:
        print(f"💡 RCA Insight: Closest site is {best_dist:.2f}km away. Distance is likely the Root Cause.")
    else:
        print(f"✅ RCA Insight: Distance is okay ({best_dist:.2f}km). Check cell azimuths/directivity above.")