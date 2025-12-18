# -*- coding: utf-8 -*-
"""
Fix remaining corrupted symbols in calculator
"""

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

with open(file_path, 'rb') as f:
    content = f.read()

original = content
fixes = []

# Fix 1: Corrupted checkmark in Price Endings
# Corrupted: c3a2c593e2809c -> Correct: e29c93 (✓)
corrupt_check = bytes.fromhex('c3a2c593e2809c')
correct_check = bytes.fromhex('e29c93')

if corrupt_check in content:
    content = content.replace(corrupt_check, correct_check)
    fixes.append("Checkmark symbol (✓)")

# Also check for other common corrupted toggle symbols
# Sun/Moon icons for dark mode toggle
sun_corrupt = bytes.fromhex('c3a2c598e2809a')  # possible corrupted ☀
moon_corrupt = bytes.fromhex('c3a2c598e280a0')  # possible corrupted ☾

if sun_corrupt in content:
    content = content.replace(sun_corrupt, bytes.fromhex('e29880'))  # ☀
    fixes.append("Sun symbol")
    
if moon_corrupt in content:
    content = content.replace(moon_corrupt, bytes.fromhex('e2989e'))  # ☾
    fixes.append("Moon symbol")

if content != original:
    with open(file_path, 'wb') as f:
        f.write(content)
    print(f"Fixed {len(fixes)} symbols:")
    for f_name in fixes:
        print(f"  + {f_name}")
else:
    print("No matching patterns found")

# Verify
check = content.decode('utf-8', errors='replace')
print(f"\nFile integrity: {check.count('<script')} script tags")
