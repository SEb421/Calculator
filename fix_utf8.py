# -*- coding: utf-8 -*-
import re

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

# Read file as bytes
with open(file_path, 'rb') as f:
    content = f.read()

original = content
changes = 0

# Fix cubic meter: look for the corrupted byte sequence
# The corrupted form of m³ is often: m + Â³ which is bytes for Latin1 misinterpretation
# Looking for: 6d c2 b3 (m followed by Â³) or other variations

# Pattern 1: mÂ³ - double encoded (m + Â + ³)
# In UTF-8 doubled encoding: 6d c3 82 c2 b3 
pattern1 = b'm\xc3\x82\xc2\xb3'
if pattern1 in content:
    content = content.replace(pattern1, b'm\xc2\xb3')
    changes += 1
    print("Fixed cubic meter (double-encoded)")

# Pattern 2: Direct Â³ (single extra layer)  
pattern2 = b'\xc3\x82\xc2\xb3'
if pattern2 in content:
    content = content.replace(pattern2, b'\xc2\xb3')
    changes += 1
    print("Fixed superscript 3 (single extra layer)")

# Fix close button: âœ• should be ✕
# âœ• in double-encoding
close_corrupt = b'\xc3\xa2\xc2\x9c\xc2\x95'
close_fixed = b'\xe2\x9c\x95'
if close_corrupt in content:
    content = content.replace(close_corrupt, close_fixed)
    changes += 1
    print("Fixed close button symbol")

# Fix arrow: â†' should be →
# â†' in double-encoding  
arrow_corrupt = b'\xc3\xa2\xc2\x86\xc2\x92'
arrow_fixed = b'\xe2\x86\x92'
if arrow_corrupt in content:
    content = content.replace(arrow_corrupt, arrow_fixed)
    changes += 1
    print("Fixed arrow symbol")

if changes > 0:
    with open(file_path, 'wb') as f:
        f.write(content)
    print(f"\nTotal fixes applied: {changes}")
else:
    print("No matching byte patterns found.")
    
    # Debug: show hex around known problem areas
    content_str = content.decode('utf-8', errors='replace')
    
    # Find CBM area
    cbm_idx = content.find(b'setVol, 3)} m')
    if cbm_idx > 0:
        area = content[cbm_idx:cbm_idx+30]
        print(f"\nCBM area bytes: {area.hex()}")
        print(f"CBM area decoded: {repr(area)}")
    
    # Find close button area
    close_idx = content.find(b'setSettingsOpen(false)}')
    if close_idx > 0:
        area = content[close_idx:close_idx+80]
        print(f"\nClose button area bytes: {area.hex()}")
        print(f"Close button area decoded: {repr(area)}")
    
    # Find GBP arrow area
    gbp_idx = content.find(b'GBP')
    while gbp_idx >= 0:
        area = content[gbp_idx:gbp_idx+30]
        if b'USD' in area:
            print(f"\nGBP->USD area bytes: {area.hex()}")
            print(f"GBP->USD area decoded: {repr(area)}")
            break
        gbp_idx = content.find(b'GBP', gbp_idx + 1)
