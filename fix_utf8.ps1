# UTF-8 Symbol Fixer for Calculator
# Fixes corrupted UTF-8 encoded symbols back to proper Unicode

$file = "c:\Users\shuli\Downloads\Calculator\index.html"
$content = [System.IO.File]::ReadAllText($file)

# Store original for comparison
$original = $content

# Fix corrupted UTF-8 symbols
$content = $content -replace 'ðŸ"¦', '📦'
$content = $content -replace "ðŸ'¡", '💡'
$content = $content -replace 'âœ•', '✕'
$content = $content -replace 'â†'', '→'
$content = $content -replace 'mÂ³', 'm³'

if ($content -ne $original) {
    [System.IO.File]::WriteAllText($file, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "UTF-8 symbols fixed successfully!"
    Write-Host "Symbols replaced: package, lightbulb, close, arrow, cubic meter"
} else {
    Write-Host "No changes needed - symbols may already be correct or patterns not found"
}
