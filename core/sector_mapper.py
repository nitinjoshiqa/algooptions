"""Sector classification for NSE stocks - covers NIFTY, NIFTY100, and Bank Nifty."""


SECTOR_MAP = {
    # Auto (6)
    'MARUTI': 'Auto', 'BAJAJ-AUTO': 'Auto', 'TATAMOTORS': 'Auto', 'EICHERMOT': 'Auto', 'HEROMOTOCO': 'Auto', 'M&M': 'Auto',
    'HYUNDAI': 'Auto', 'ESCORTS': 'Auto', 'TVSMOTOR': 'Auto',
    
    # Banking - All Bank Nifty constituents (14)
    'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'KOTAKBANK': 'Banking', 'SBIN': 'Banking', 'AXISBANK': 'Banking',
    'BANKBARODA': 'Banking', 'CANBK': 'Banking', 'FEDERALBNK': 'Banking', 'INDUSINDBK': 'Banking', 'AUBANK': 'Banking',
    'UNIONBANK': 'Banking', 'YESBANK': 'Banking', 'IDFCFIRSTB': 'Banking', 'PNB': 'Banking',
    
    # FMCG (5)
    'NESTLE': 'FMCG', 'NESTLEIND': 'FMCG', 'BRITANNIA': 'FMCG', 'HINDUNILVR': 'FMCG', 'ITC': 'FMCG',
    'COLPAL': 'FMCG', 'MAZDOCK': 'FMCG',
    
    # Finance & Financial Services (10)
    'BAJAJFINSV': 'Finance', 'BAJFINANCE': 'Finance', 'SHRIRAMFIN': 'Finance', 'HDFCLIFE': 'Finance', 
    'SBILIFE': 'Finance', 'LICI': 'Finance', 'SBICARD': 'Finance', 'CHOLAFIN': 'Finance',
    'JIOFIN': 'Finance', 'MANAPPURAM': 'Finance',
    
    # Pharma (6)
    'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma', 'LUPIN': 'Pharma',
    'DIVISLAB': 'Pharma', 'APOLLOHOSP': 'Healthcare',
    
    # IT (8)
    'INFY': 'IT', 'TCS': 'IT', 'WIPRO': 'IT', 'TECHM': 'IT', 'HCL': 'IT', 'HCLTECH': 'IT',
    'LTTS': 'IT', 'KPITTECH': 'IT', 'MPHASIS': 'IT', 'NAUKRI': 'IT',
    
    # Oil & Gas (5)
    'RELIANCE': 'Oil & Gas', 'BPCL': 'Oil & Gas', 'ONGC': 'Oil & Gas', 'GAIL': 'Oil & Gas', 'IOC': 'Oil & Gas',
    
    # Metals (5)
    'TATASTEEL': 'Metals', 'HINDALCO': 'Metals', 'VEDL': 'Metals', 'JSWSTEEL': 'Metals', 'AMBUJACEM': 'Metals',
    
    # Power & Energy (7)
    'NTPC': 'Power', 'POWERGRID': 'Power', 'TATAPOWER': 'Power', 'ADANIPOWER': 'Power',
    'ADANIGREEN': 'Power', 'JSWENERGY': 'Power', 'SOLARINDS': 'Power', 'NHPC': 'Power',
    
    # Cement (2)
    'ULTRACEMCO': 'Cement', 'SHREECEM': 'Cement',
    
    # Utilities & Infrastructure (8)
    'LT': 'Infrastructure', 'SIEMENS': 'Infrastructure', 'BOSCHLTD': 'Infrastructure', 'HAVELLS': 'Infrastructure',
    'LANDT': 'Infrastructure', 'BEL': 'Defense', 'HAL': 'Defense', 'ADANIPORTS': 'Ports & Logistics',
    
    # Telecom (1)
    'BHARTIARTL': 'Telecom',
    
    # Consumer & Retail (10)
    'TITAN': 'Consumer', 'TRENT': 'Consumer', 'TATACONSUM': 'Consumer', 'PAGE': 'Consumer', 
    'ASIANPAINT': 'Consumer', 'INDIGO': 'Aviation', 'INDHOTEL': 'Hospitality', 'DLF': 'Real Estate',
    'LODHA': 'Real Estate', 'MRTI': 'Real Estate',
    
    # Diversified & Industrial (8)
    'ADANIENSOL': 'Diversified', 'GRASIM': 'Diversified', 'BAJAJHLDNG': 'Diversified',
    'ABB': 'Industrial', 'MOTHERSON': 'Industrial', 'MSUMI': 'Industrial', 'ESCORTS': 'Industrial',
    'GRINDWELL': 'Industrial',
    
    # Chemicals & Pharma Support (4)
    'TORNTPHARM': 'Pharma', 'PIDILITIND': 'Chemicals', 'CGPOWER': 'Industrial', 'HONAUT': 'Industrial',
    
    # Financial Infrastructure (4)
    'PFC': 'Finance', 'RECLTD': 'Finance', 'IRFC': 'Finance', 'IDFC': 'Finance',
    
    # Healthcare (2)
    'MAXHEALTH': 'Healthcare',
    
    # Miscellaneous/New Sectors (8)
    'COALINDIA': 'Mining', 'JBJART': 'Industrial', 'LINDEINDIA': 'Industrial',
    'PIIND': 'Industrial', 'LAURUSLABS': 'Pharma',
}


def get_sector(symbol):
    """Get sector for a symbol. Returns 'Unknown' if not found."""
    return SECTOR_MAP.get(symbol, 'Unknown')
