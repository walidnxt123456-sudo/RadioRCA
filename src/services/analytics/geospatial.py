import pandas as pd
import numpy as np
from ..rca_utils import get_latest_clean_file, fetch_ericsson_e_tilt_group

def calculate_required_tilt(height_m, distance_km):
    """Calculates the downward angle (tilt) required to reach the user's location."""
    if distance_km <= 0: return 0
    # Convert distance to meters
    distance_m = distance_km * 1000
    # tan(theta) = Opp / Adj -> Tilt = arctan(HBA / Dist)
    tilt_rad = np.arctan2(height_m, distance_m)
    return round(float(np.degrees(tilt_rad)), 1)

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
    
    # Identify if we are in CLI or Web mode to handle the 'input'
    is_web = ctx.get('is_web', False)
    site_limit = ctx.get('site_limit', 1)
    
    if not is_web:
        # Input Request
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

    # Identify Vertical columns independently
    hba_col = next((c for c in df.columns if any(k in c for k in ['hba', 'height', 'mha'])), None)
    etilt_col = next((c for c in df.columns if any(k in c for k in ['etilt', 'e-tilt', 'elect_tilt'])), None)

    # Calculate Distance for every row
    df['distance_km'] = df.apply(lambda r: haversine(u_lat, u_lon, float(r[lat_col]), float(r[lon_col])), axis=1)
    
    # 1. Initialize a Results Structure
    analysis_results = {
        "user_coords": [u_lat, u_lon],
        "cells": [],
        "verdict": ""
    }
    
    # 2. Main Processing Loop
    unique_nearest_sites = df.sort_values('distance_km')[site_col].unique()[:site_limit]
    
    for site in unique_nearest_sites:
        # Get all cells belonging to this site
        site_cells = df[df[site_col] == site].copy()
        
        for _, row in site_cells.iterrows():
            # --- HORIZONTAL BLOCK (Azimuth) ---
            # 1. Calculate the bearing from Site to User
            angle_to_user = calculate_bearing(row[lat_col], row[lon_col], u_lat, u_lon)
            
            # 2. Calculate the Offset (the "Shit-factor" for radio gain)
            azimuth = row[azi_col] if azi_col else None
            offset = calculate_angle_offset(azimuth, angle_to_user)
            
            # --- VERTICAL BLOCK (Tilt) ---
            # Extract height and electrical tilt independently
            hba = float(row[hba_col]) if hba_col and not pd.isna(row[hba_col]) else 30.0
            
            cell_name = row[cell_col]
            site_id = row[site_col]
            # t.1. Fetch live data from CM
            e_tilt_group = fetch_ericsson_e_tilt_group(site_id, cell_name)
            e_tilt = 0.0 # Default fallback
            if e_tilt_group:
                e_tilt = e_tilt_group['e_tilt']
                band_info = e_tilt_group['band_id']
                
            # t.2. Calculate Required Tilt
            req_tilt = calculate_required_tilt(hba, row['distance_km'])
            tilt_delta = abs(req_tilt - e_tilt) # Use this for future RCA logic
            # t.3. Determine Vertical Status
            v_delta = abs(req_tilt - e_tilt)
            if v_delta <= 3:
                v_status = "✅ [V-OK]"
            elif v_delta <= 6:
                v_status = "⚠️ [EDGE]"
            else:
                v_status = "❌ [MISSED]"
            
            # 3. Enhanced Status Logic
            # --- STATUS BLOCK (Horizontal logic) ---
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
                    
            # 4. Instead of printing, we APPEND to our list
            cell_data = {
                "site_id": str(row[site_col]),
                "cell_name": str(row[cell_col]),
                "site_lat": float(row[lat_col]),  # Added for mapping
                "site_lon": float(row[lon_col]),  # Added for mapping
                "distance": round(row['distance_km'], 2),
                "azimuth": int(row[azi_col]) if azi_col else 0,
                "bearing": int(angle_to_user),
                "offset": offset,
                "h_status": status,
                "req_tilt": req_tilt,
                "e_tilt": e_tilt,
                "v_status": v_status
            }
            analysis_results["cells"].append(cell_data)

            # --- PRINTING BLOCK --
            if not is_web:
                off_str = f"{int(offset)}°" if offset is not None else "---"
                print(f"{str(row[site_col]):<12} | "
                      f"{str(row[cell_col]):<20} | "
                      f"{row['distance_km']:<10.2f} | "
                      f"{int(row[azi_col]) if azi_col else 'N/A':<5} | "
                      f"{int(angle_to_user):>3}°     | "
                      f"{off_str:<8} | "
                      f"{status:<16}  |"                  
                      f"{req_tilt:>5}° | "
                      f"{e_tilt:>4}° | "
                      f"{v_status}")
                  
        if not is_web:
            print("-" * 85) # Separator between different sites

    if not is_web:
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
            
        # Separate Vertical RCA Insight
        if hba_col and best_dist < 0.2 and hba > 35:
            print(f"📉 Vertical RCA: User is in the 'Null' zone. Too close ({best_dist:.2f}km) to a tall tower ({hba}m).")
        # Final Verdict Logic
        if offset <= 30 and v_delta <= 3:
            print("\n🎯 VERDICT: User is in the Sweet Spot (Horizontal & Vertical alignment OK).")
        elif offset > 30 and v_delta <= 3:
            print("\n📢 VERDICT: Horizontal Mismatch. Azimuth is the likely Root Cause.")
        elif offset <= 30 and v_delta > 3:
            print("\n📉 VERDICT: Vertical Mismatch. Overshooting or Tilt issue is the likely Root Cause.")
        else:
            print("\n🚫 VERDICT: Poor Coverage. User is not served by any main beam of this site.")
            
    return analysis_results # : Returning data