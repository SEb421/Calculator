import re

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

# Read file as bytes first to avoid encoding issues
with open(file_path, 'rb') as f:
    content = f.read()

# Decode to string
content_str = content.decode('utf-8')

# Look for patterns around known corrupted text
patterns_to_find = [
    'text-xl">',  # before package emoji
    'Suggestions:',  # lightbulb area
    'setSettingsOpen(false)',  # close button area
    'GBP',  # arrow area  
    'mÂ³',  # cubic meter
    'm³',  # correct cubic meter
]

print("Searching for patterns...")
for pattern in patterns_to_find:
    idx = content_str.find(pattern)
    if idx >= 0:
        # Show context around the match
        start = max(0, idx - 20)
        end = min(len(content_str), idx + len(pattern) + 50)
        context = content_str[start:end]
        print(f"\nFound '{pattern}' at {idx}:")
        print(f"Context: {repr(context)}")

# Also search for the exact corrupted strings (as seen in file view)
corrupted_patterns = [
    'ðŸ"¦',  # package
    'ðŸ\'¡',  # lightbulb (with escaped quote)
    'âœ•',  # close
    'â†\'',  # arrow (with escaped quote) 
    'mÂ³',  # cubic meter
]

print("\n\nSearching for corrupted patterns...")
for cp in corrupted_patterns:
    if cp in content_str:
        print(f"Found corrupted pattern: {repr(cp)}")
    else:
        print(f"NOT found: {repr(cp)}")
