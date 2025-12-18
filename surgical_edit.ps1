# CAREFUL surgical approach - read file as array, modify specific lines
$file = "C:\Users\shuli\Downloads\Calculator\index.html"
$lines = Get-Content $file

# Find the line with courier mapping
$courierMapLine = $lines | Select-String -Pattern "courierRules.map" | Select-Object -First 1
$startIdx = $courierMapLine.LineNumber - 1

Write-Host "Found courier section at line: $($startIdx + 1)"

# Replace line 1148: change div to details
$lines[1147] = $lines[1147] -replace '<div key=\{r\.id\}', '<details key={r.id}'

# Replace line 1149-1151: change header to summary
$lines[1148] = '                                                        <summary className="cursor-pointer font-bold text-sm mb-3 flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 list-none">'
$lines[1149] = '                                                            {r.logo && <img src={r.logo} className="h-5 object-contain" />}'
$lines[1150] = '                                                            <span>{r.carrier || "Unknown"} - {r.service || r.name}</span>'
$lines[1151] = '                                                        </summary>'

# Replace lines 1152-1156 with comprehensive fields
$newContent = @'
                                                        <div className="space-y-3 mt-3">
                                                            <div className="pb-3 border-b border-gray-200 dark:border-gray-700">
                                                                <h4 className="text-xs font-bold uppercase text-gray-500 dark:text-gray-400 mb-2">Weight & Pricing</h4>
                                                                <div className="grid grid-cols-2 gap-2">
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Max Weight (kg)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" value={r.maxWeight || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxWeight: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">1st Parcel (£)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" step="0.01" value={r.price || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, price: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Additional (£)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" step="0.01" value={r.additionalPrice || r.price || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, additionalPrice: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">25kg+ Surcharge (£)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" step="0.01" value={r.surcharge25kg || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, surcharge25kg: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                </div>
                                                            </div>
                                                            <details className="cursor-pointer">
                                                                <summary className="text-xs font-bold uppercase text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400">▶ Dimension Limits</summary>
                                                                <div className="grid grid-cols-3 gap-2 mt-2">
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Max Length (cm)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" value={r.maxL || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxL: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Max Width (cm)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" value={r.maxW || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxW: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Max Height (cm)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" value={r.maxH || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxH: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Max Girth (cm)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" value={r.maxGirth || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxGirth: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Max CBM (m³)</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" step="0.001" value={r.maxCBM || ''} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxCBM: parseFloat(e.target.value) || 0 } : pr))} /></div>
                                                                    <div><label className="text-[10px] uppercase text-gray-500 dark:text-gray-400 font-semibold">Vol Wt Divisor</label><input className="glass-input w-full px-2 py-1.5 text-xs rounded tabular-nums" type="number" value={r.volWeightDivisor || 5000} onChange={(e) => setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, volWeightDivisor: parseFloat(e.target.value) || 5000 } : pr))} /></div>
                                                                </div>
                                                            </details>
                                                        </div>
'@

# Remove old lines 1152-1157 (6 lines) and insert new content
$newLines = $newContent -split "`r`n"
$lines = $lines[0..1151] + $newLines + $lines[1157..($lines.Length - 1)]

# Change closing div to details at line 1157 (now shifted)
$closeIdx = $lines | Select-String -Pattern "^\s+</div>\s*$" -AllMatches | Where-Object { $_.LineNumber -gt 1150 -and $_.LineNumber -lt 1165 } | Select-Object -First 1
if ($closeIdx) {
    $lines[$closeIdx.LineNumber - 1] = $lines[$closeIdx.LineNumber - 1] -replace '</div>', '</details>'
}

# Write back
$lines | Set-Content $file
Write-Host "Surgical edit complete!"
