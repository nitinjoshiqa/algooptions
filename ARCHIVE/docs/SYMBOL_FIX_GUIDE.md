# Symbol Fixes for Skipped Stocks (45 total)

These symbols failed to fetch data from Yahoo Finance. Below are the likely correct ticker formats:

## High-Confidence Fixes (Common Format Issues)

| Skipped Symbol | Likely Correct Yahoo Symbol | Notes |
|---|---|---|
| ALKEM | ALKEM.NS | Alkem Laboratories |
| APOLLOTYRE | APOLLOTYRE.NS | Apollo Tyres |
| BOSCHLTD | BOSCHLTD.NS | Bosch Limited |
| ESCORTS | ESCORTS.NS | Escorts Limited |
| EXIDEIND | EXIDEIND.NS | Exide Industries |
| GUJGASLTD | GUJGASLTD.NS | Gujarat Gas |
| HATSUN | HATSUN.NS | Hatsun Agro Products |
| KIOCL | KIOCL.NS | Kiocl Limited |
| LTTS | LTTS.NS | L&T Technology Services |
| MEDPLUS | MEDPLUS.NS | Medplus Health Services |
| MOIL | MOIL.NS | MOIL Limited |
| MIDHANI | MIDHANI.NS | Midhani |
| MSPL | MSPL.NS | Manganese Ore (India) Limited |
| NLCINDIA | NLCINDIA.NS | NLC India |
| NOCIL | NOCIL.NS | NOCIL |
| PAGEIND | PAGEIND.NS | Page Industries |
| PDSL | PDSL.NS | Pudumjee Pulp & Paper |
| PIIND | PIIND.NS | PiIndra Technologies |
| RATNAMANI | RATNAMANI.NS | Ratnamani Metals & Tubes |
| SHREECEM | SHREECEM.NS | Shree Cement |
| SIEMENS | SIEMENS.NS | Siemens Limited |
| SUNTV | SUNTV.NS | Sun TV Network |
| SOLARINDS | SOLARINDS.NS | Solar Industries |
| TATACHEM | TATACHEM.NS | Tata Chemicals |
| TATAELXSI | TATAELXSI.NS | Tata Elxsi |
| TORNTPHARM | TORNTPHARM.NS | Torrent Pharmaceuticals |
| TORNTPOWER | TORNTPOWER.NS | Torrent Power |
| UCOBANK | UCOBANK.NS | UCO Bank |
| TDPOWERSYS | TDPOWERSYS.NS | TD Power Systems |
| VGUARD | VGUARD.NS | V-Guard Industries |
| VINATIORGA | VINATIORGA.NS | Vinati Organics |
| WESTLIFE | WESTLIFE.NS | Westlife Development |
| VRLLOG | VRLLOG.NS | VRL Logistics |
| WHIRLPOOL | WHIRLPOOL.NS | Whirlpool of India |
| ZYDUSWELL | ZYDUSWELL.NS | Zydus Wellness |

## Medium-Confidence Fixes (Name variations)

| Skipped Symbol | Likely Correct Yahoo Symbol | Notes |
|---|---|---|
| AEGISLOG | AEGISLOG.NS | Aegis Logistics |
| APLLTD | APLLTD.NS | APL Apollo Tubes |
| BAJAJHLDNG | BAJAJHLDNG.NS | Bajaj Holdings |
| BSOFT | BSOFT.NS | BlueStack Solutions (formerly Bsoft) |
| DEEPAKFERT | DEEPAKFERT.NS | Deepak Fertilisers |
| FCONSUMER | FCONSUMER.NS | Future Consumer Limited |
| FORCEMOT | FORCEMOT.NS | Force Motors |
| IPCALAB | IPCALAB.NS | IPCA Laboratories |
| JYOTHYLAB | JYOTHYLAB.NS | Jyothy Laboratories |
| PCBL | PCBL.NS | Punjab Chemicals & Crop Protection |
| PFIZER | PFIZER.NS | Pfizer Limited (India) |

---

## How to Update

### **Option 1: Manual Entry (Quick)**
Please provide the correct symbols as they appear on Yahoo Finance. For most, adding `.NS` should work, but some may need investigation.

### **Option 2: Automatic Testing**
I can create a script to test common variations:
- `SYMBOL.NS`
- `SYMBOL.BO` (alternative BSE format)
- Just `SYMBOL` (if already listed globally)

### **Option 3: NSE Website Lookup**
Check [NSE Listing](https://www.nseindia.com/) for exact symbols and validate against Yahoo Finance.

---

## Instructions for User Fixes

1. **Create corrected file** with your validated symbols (one per line)
2. **Test with** `--universe nifty500` flag
3. **Report success rate** - how many symbols resolve now?

Would you like to:
- ✅ Test the `.NS` suffix additions first?
- 🔍 Manually research and provide correct symbols?
- 🤖 Use a lookup tool to auto-fetch correct formats?
