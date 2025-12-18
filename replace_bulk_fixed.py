import re

# Read the file
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# More flexible search - handle any whitespace
pattern_start = r'(\s*)function\s+BulkQuickView\s*\(\s*\{\s*priceRules'
pattern_end = r'(\s*)function\s+Calculator\s*\(\s*\)'

match_start = re.search(pattern_start, content)
match_end = re.search(pattern_end, content)

if not match_start or not match_end:
    print("ERROR: Could not find function boundaries")
    print(f"Start found: {bool(match_start)}, End found: {bool(match_end)}")
    exit(1)

start_pos = match_start.start()
end_pos = match_end.start()
indent = match_start.group(1)  # Capture the indentation

print(f"Found BulkQuickView at position {start_pos}")
print(f"Found Calculator at position {end_pos}")
print(f"Indent: '{indent}' ({len(indent)} chars)")

# Read new component
with open("BulkQuickView_NEW.jsx", "r", encoding="utf-8") as f:
    new_code = f.read()

# Remove any leading comment
if new_code.startswith("//"):
    new_code = new_code[new_code.find("function"):]

# Add indentation to each line
indented_lines = []
for line in new_code.split('\n'):
    if line.strip():  # Non-empty line
        indented_lines.append(indent + line)
    else:  # Empty line
        indented_lines.append('')

new_component = '\n'.join(indented_lines)

# Replace
new_content = content[:start_pos] + new_component + '\n\n' + content[end_pos:]

# Write
with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("SUCCESS: BulkQuickView replaced")
