from infrastructure.logger import log 

def find_standard_col(df_columns, target_type, default=None):
    """
    Maps various naming conventions to standard radio columns.
    target_type: 'lat', 'lon', 'azi', 'site', 'cell', 'hba', 'tilt'
    """
    mapping = {
        'lat': ['lat', 'latitude', 'y_coord', 'north'],
        'lon': ['lon', 'long', 'longitude', 'x_coord', 'east'],
        'azi': ['azi', 'dir', 'orientation', 'angle', 'beam'],
        'site': ['site', 'node', 'enodeb', 'site_id'],
        'cell': ['cell', 'sector', 'antenna', 'cell_name'],
        'hba': ['hba', 'height', 'mha', 'altitude'],
        'tilt': ['tilt', 'etilt', 'e-tilt', 'elect_tilt'],
        'arfcn': ['arfcn', 'earfcndl', 'earfcn', 'ssbfrequency', 'ssb_freq']
    }
    
    keywords = mapping.get(target_type, [])
    for col in df_columns:
        if any(key.lower() in col.lower() for key in keywords):
            log.info(f"[MAPPER] Found '{col}' for {target_type.upper()}")
            return col
            
    if default:
        log.warning(f"[MAPPER] No match for {target_type.upper()}, defaulting to '{default}'")
    else:
        log.debug(f"[MAPPER] Optional column {target_type.upper()} not found.")
        
    return default


def get_lte_band(cell_name, earfcn):
    """Specific mapping for LTE bands based on EARFCNDL and suffixes."""
    p = {
        'L800': ('LTE800', '#1f77b4', 0.6),
        'L1800': ('LTE1800', '#2ca02c', 0.35),
        'L2100': ('LTE2100', '#ff7f0e', 0.25),
    }
    
    if earfcn:
        try:
            val = int(earfcn)
            if val == 6200: return p['L800']
            if val in [1350, 1375]: return p['L1800']
            if val in [251, 276]: return p['L2100']
        except (ValueError, TypeError): pass

    suffix = str(cell_name)[-1].upper()
    if suffix in ['O', 'P', 'Q', 'N']: return p['L800']
    if suffix in ['X', 'Y', 'Z', 'L']: return p['L1800']
    if suffix in ['A', 'B', 'C', 'D']: return p['L2100']
    return ('Unknown LTE', '#7f7f7f', 0.3)

def get_nr_band(cell_name, ssb_freq):
    """Specific mapping for NR bands including n3 (1800) and n78 (3500)."""
    p = {
        'N3500': ('NR3500', '#e377c2', 0.2),
        'N700':  ('NR700/800', '#9467bd', 0.7),
        'N1800': ('NR1800', '#2ca02c', 0.35), # n3 band
    }

    if ssb_freq:
        try:
            val = int(ssb_freq)
            if val in [361490, 361970]: return p['N3500']
            if val in [647328, 644056]: return p['N700']
            if val in [360000, 390000]: return p['N1800'] # Example NR n3 ssbFreqs
        except (ValueError, TypeError): pass

    suffix = str(cell_name)[-1].upper()
    if suffix in ['R', 'S', 'T']: return p['N700']
    # If the cell name contains 'NR' and ends in X,Y,Z, it's likely n3
    if 'NR' in str(cell_name).upper() and suffix in ['X', 'Y', 'Z']: return p['N1800']
    
    return ('Unknown NR', '#7f7f7f', 0.3)