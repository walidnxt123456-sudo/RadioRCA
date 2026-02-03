import pandas as pd
import numpy as np
from ..rca_utils import get_latest_clean_file

def calculate_angle_offset(azimuth, bearing):
    """Calculates the absolute minimum difference between antenna azimuth and user bearing."""
    if azimuth is None or np.isnan(azimuth):
        return None
    diff = abs(azimuth - bearing) % 360
    if diff > 180:
        diff = 360 - diff
    return round(float(diff), 1)

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
    print("="*100)
    print(f"{'SITE ID':<12} | {'CELL NAME':<20} | {'DIST (km)':<10} | {'AZI':<5} | {'BEARING':<8} | {'OFFSET':<8} | {'STATUS'}")
    print("-" * 100)

    for site in unique_nearest_sites:
        # Get all cells belonging to this site
        site_cells = df[df[site_col] == site].copy()
        
        for _, row in site_cells.iterrows():
            # 1. Calculate the bearing from Site to User
            angle_to_user = calculate_bearing(row[lat_col], row[lon_col], u_lat, u_lon)
            
            # 2. Calculate the Offset (the "Shit-factor" for radio gain)
            azimuth = row[azi_col] if azi_col else None
            offset = calculate_angle_offset(azimuth, angle_to_user)
            
            # 3. Enhanced Status Logic
            status = "N/A"
            if offset is not None:
                if offset <= 30:
                    status = "✅ [DIRECT]"
                elif offset <= 70:
                    status = "⚠️ [SIDE]"
                elif offset <= 120:
                    status = "⚠️ [Fare SIDE]"
                else:
                    status = "❌ [BACK]"
                    
            # 4. Print the Row
            off_str = f"{int(offset)}°" if offset is not None else "---"
            print(f"{str(row[site_col]):<12} | "
                  f"{str(row[cell_col]):<20} | "
                  f"{row['distance_km']:<10.2f} | "
                  f"{int(row[azi_col]) if azi_col else 'N/A':<5} | "
                  f"{int(angle_to_user):>3}°     | "
                  f"{off_str:<8} | "
                  f"{status}")                  
                  
        print("-" * 85) # Separator between different sites

    # RCA Insight
    best_dist = df['distance_km'].min()
    if best_dist > 3.5:
        print(f"💡 RCA Insight: Closest site is {best_dist:.2f}km away. Distance is likely the Root Cause.")
    else:
        print(f"✅ RCA Insight: Distance is okay ({best_dist:.2f}km). Check cell azimuths/directivity above.")
        
    # Find the best candidate (Closest to 0 degree offset among nearby cells)
    # We filter for cells within 5km, then sort by offset
    valid_candidates = df[df['distance_km'] < 2.0].copy()
    if azi_col and not valid_candidates.empty:
        valid_candidates['offset'] = valid_candidates.apply(
            lambda r: calculate_angle_offset(r[azi_col], calculate_bearing(r[lat_col], r[lon_col], u_lat, u_lon)), 
            axis=1
        )
        best_row = valid_candidates.sort_values('offset').iloc[0]
        
        if best_row['offset'] < 25:
            print(f"🎯 Recommended Cell: {best_row[cell_col]} (Offset: {int(best_row['offset'])}°)")