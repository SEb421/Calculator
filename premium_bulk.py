# Premium Bulk View - Integration Script
# Creates split-layout bulk view with real-time calculation

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

LINE_END = b'\r\n'

with open(file_path, 'rb') as f:
    content = f.read()

# Find BulkQuickView function
start_marker = b'function BulkQuickView({ priceRules, courierRules, active }) {'
end_marker = b'function Calculator()'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Cannot find function boundaries")
    exit(1)

# Find function end
func_content = content[start_idx:end_idx]
brace_count = 0
func_end = None
for i, byte in enumerate(func_content):
    if byte == ord('{'):
        brace_count += 1
    elif byte == ord('}'):
        brace_count -= 1
        if brace_count == 0:
            func_end = start_idx + i + 1
            break

print(f"Replacing BulkQuickView at {start_idx}-{func_end}")

# New premium component
new_component = '''        function BulkQuickView({ priceRules, courierRules, active }) {
            const [pricesText, setPricesText] = useState('');
            const [dimsText, setDimsText] = useState('');
            const [showAdvanced, setShowAdvanced] = useState(false);
            const [packText, setPackText] = useState('');
            const [weightText, setWeightText] = useState('');
            const [settings, setSettings] = useState({ margin: 25, commission: 15.3, ppCost: 2.70 });

            const rows = useMemo(() => {
                const prices = pricesText.split('\\n').map(l => l.trim()).filter(Boolean);
                const dims = dimsText.split('\\n').map(l => l.trim());
                const packs = packText.split('\\n').map(l => l.trim());
                const weights = weightText.split('\\n').map(l => l.trim());

                return prices.map((priceLine, i) => {
                    const priceParts = priceLine.split(/[,\\s]+/);
                    const unitUSD = parseFloat(priceParts[0]) || 0;
                    const pack = parseInt(priceParts[1] || packs[i]) || 1;

                    const dimLine = dims[i] || '';
                    const dimParts = dimLine.split(/[x,\\s-]+/).map(d => parseFloat(d)).filter(d => !isNaN(d));
                    const [L = 0, W = 0, H = 0] = dimParts;

                    const weight = parseFloat(weights[i]) || 0;

                    if (unitUSD <= 0) return null;

                    const fx = 1.28;
                    const sea = 2800;
                    const vol = (L / 100) * (W / 100) * (H / 100);
                    const effCBM = 76 * 0.895;
                    const cartons = vol > 0 ? Math.floor(effCBM / vol) : 0;
                    const units = cartons * pack;

                    const unitGBP = unitUSD / fx;
                    const freight = units > 0 ? sea / units : 0;
                    const landedUnit = unitGBP + freight;
                    const landedPack = landedUnit * pack;
                    const purchaseInc = pack > 1 ? landedPack : landedUnit;

                    const sell = requiredSellForMargin(settings.margin, purchaseInc, settings.commission, settings.ppCost, 0);
                    const profit = sell > 0 ? computeProfit(sell, purchaseInc, settings.commission, settings.ppCost, 0) : 0;
                    const marginPct = sell > 0 ? (profit / sell) * 100 : 0;

                    const courier = L > 0 && W > 0 && H > 0 ? chooseCourier(L, W, H, weight, courierRules) : null;

                    return { i: i + 1, unitUSD, pack, L, W, H, weight, landedUnit, landedPack, sell, profit, marginPct, courier, units };
                }).filter(Boolean);
            }, [pricesText, dimsText, packText, weightText, settings, courierRules]);

            const stats = useMemo(() => ({
                total: rows.length,
                good: rows.filter(r => r.marginPct >= settings.margin).length,
                review: rows.filter(r => r.marginPct >= 15 && r.marginPct < settings.margin).length,
                low: rows.filter(r => r.marginPct < 15).length
            }), [rows, settings.margin]);

            const money = (n) => Number.isFinite(n) ? `\\u00a3${n.toFixed(2)}` : '\\u2014';
            const getColor = (m) => m >= settings.margin ? 'text-green-600 dark:text-green-400' : m >= 15 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400';
            const getBg = (m) => m >= settings.margin ? 'bg-green-500' : m >= 15 ? 'bg-amber-500' : 'bg-red-500';

            if (!active) return null;

            return (
                <div className="space-y-6">
                    {/* Main Split Layout */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* INPUT SIDE (LEFT) */}
                        <div className="lg:col-span-5 space-y-5">
                            {/* Primary: Unit Prices */}
                            <div className="relative">
                                <div className="absolute -inset-1 bg-gradient-to-r from-blue-400/20 to-indigo-500/20 rounded-2xl blur-sm"></div>
                                <div className="relative glass-card rounded-2xl p-5 ring-2 ring-blue-300/60 dark:ring-indigo-400/50">
                                    <label className="flex items-center gap-2 text-xs font-bold text-blue-600 dark:text-blue-300 uppercase tracking-wide mb-3">
                                        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                                        Unit Prices (USD)
                                    </label>
                                    <textarea 
                                        className="w-full h-36 glass-input rounded-xl p-4 text-sm font-bold !bg-blue-50/50 dark:!bg-indigo-900/30 font-mono leading-relaxed resize-none" 
                                        placeholder="2.35&#10;3.50&#10;4.20, 2  (price, pack)"
                                        value={pricesText}
                                        onChange={e => setPricesText(e.target.value)}
                                    />
                                    <div className="text-[10px] text-gray-500 mt-2">One per line. Optional: price, pack</div>
                                </div>
                            </div>

                            {/* Required: Dimensions */}
                            <div className="glass-card rounded-2xl p-5">
                                <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3 block">Dimensions (L x W x H cm)</label>
                                <textarea 
                                    className="w-full h-36 glass-input rounded-xl p-4 text-sm font-mono leading-relaxed resize-none" 
                                    placeholder="76x43x47&#10;80 40 50&#10;75, 45, 48"
                                    value={dimsText}
                                    onChange={e => setDimsText(e.target.value)}
                                />
                                <div className="text-[10px] text-gray-500 mt-2">Any separator: x, space, comma, dash</div>
                            </div>

                            {/* Advanced (Collapsed) */}
                            <div className="glass-card rounded-2xl overflow-hidden">
                                <button 
                                    onClick={() => setShowAdvanced(!showAdvanced)} 
                                    className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                                >
                                    <span className="text-sm font-bold text-gray-500">+ Advanced (Pack, Weight)</span>
                                    <span className={`transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>\\u25bc</span>
                                </button>
                                {showAdvanced && (
                                    <div className="px-4 pb-4 space-y-4 border-t border-gray-100 dark:border-gray-800 pt-4">
                                        <div>
                                            <label className="text-xs font-medium text-gray-500 mb-1 block">Pack Size (optional)</label>
                                            <textarea className="w-full h-20 glass-input rounded-xl p-3 text-sm font-mono resize-none" placeholder="1&#10;2&#10;1" value={packText} onChange={e => setPackText(e.target.value)} />
                                        </div>
                                        <div>
                                            <label className="text-xs font-medium text-gray-500 mb-1 block">Weight kg (optional)</label>
                                            <textarea className="w-full h-20 glass-input rounded-xl p-3 text-sm font-mono resize-none" placeholder="2.5&#10;3.0&#10;1.8" value={weightText} onChange={e => setWeightText(e.target.value)} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* OUTPUT SIDE (RIGHT) */}
                        <div className="lg:col-span-7 space-y-5">
                            {/* Summary Cards */}
                            {rows.length > 0 && (
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="glass-card rounded-xl p-4 bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/20 border border-green-200 dark:border-green-800">
                                        <div className="text-xs font-bold text-green-700 dark:text-green-300 uppercase mb-1">Good</div>
                                        <div className="text-3xl font-black text-green-600">{stats.good}</div>
                                        <div className="text-[10px] text-green-600/70">\\u2265 {settings.margin}% margin</div>
                                    </div>
                                    <div className="glass-card rounded-xl p-4 bg-gradient-to-br from-amber-50 to-orange-100 dark:from-amber-900/30 dark:to-orange-900/20 border border-amber-200 dark:border-amber-800">
                                        <div className="text-xs font-bold text-amber-700 dark:text-amber-300 uppercase mb-1">Review</div>
                                        <div className="text-3xl font-black text-amber-600">{stats.review}</div>
                                        <div className="text-[10px] text-amber-600/70">15-{settings.margin}% margin</div>
                                    </div>
                                    <div className="glass-card rounded-xl p-4 bg-gradient-to-br from-red-50 to-rose-100 dark:from-red-900/30 dark:to-rose-900/20 border border-red-200 dark:border-red-800">
                                        <div className="text-xs font-bold text-red-700 dark:text-red-300 uppercase mb-1">Low</div>
                                        <div className="text-3xl font-black text-red-600">{stats.low}</div>
                                        <div className="text-[10px] text-red-600/70">&lt; 15% margin</div>
                                    </div>
                                </div>
                            )}

                            {/* Results Table */}
                            {rows.length > 0 ? (
                                <div className="glass-card rounded-2xl overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-gray-50 dark:bg-gray-800/80 text-xs uppercase font-bold text-gray-500 sticky top-0">
                                                <tr>
                                                    <th className="px-4 py-3 text-center w-10">#</th>
                                                    <th className="px-4 py-3 text-left">Target Sell</th>
                                                    <th className="px-4 py-3 text-center">Margin</th>
                                                    <th className="px-4 py-3 text-right">Profit</th>
                                                    <th className="px-4 py-3 text-right">Landed</th>
                                                    <th className="px-4 py-3 text-left">Courier</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                                {rows.map(r => (
                                                    <tr key={r.i} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                                        <td className="px-4 py-3 text-center text-gray-400 font-mono">{r.i}</td>
                                                        <td className="px-4 py-3">
                                                            <div className="text-xl font-black text-indigo-600 dark:text-blue-300">{money(r.sell)}</div>
                                                            {r.pack > 1 && <div className="text-[10px] text-gray-400">Pack of {r.pack}</div>}
                                                        </td>
                                                        <td className="px-4 py-3 text-center">
                                                            <div className={`text-lg font-bold ${getColor(r.marginPct)}`}>{r.marginPct.toFixed(1)}%</div>
                                                            <div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full mt-1">
                                                                <div className={`h-full rounded-full ${getBg(r.marginPct)}`} style={{width: `${Math.min(100, r.marginPct * 2)}%`}}></div>
                                                            </div>
                                                        </td>
                                                        <td className={`px-4 py-3 text-right font-bold ${getColor(r.marginPct)}`}>{money(r.profit)}</td>
                                                        <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">{money(r.landedUnit)}</td>
                                                        <td className="px-4 py-3">
                                                            {r.courier ? (
                                                                <div className="text-xs">
                                                                    <div className="font-bold">{r.courier.carrier}</div>
                                                                    <div className="text-gray-400">{money(r.courier.cost)}</div>
                                                                </div>
                                                            ) : (
                                                                <span className="text-xs text-gray-400">\\u2014</span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ) : (
                                <div className="glass-card rounded-2xl p-12 text-center">
                                    <div className="text-gray-400 text-sm">Enter prices on the left to see results</div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Settings Bar (Bottom) */}
                    <div className="glass-card rounded-xl p-4">
                        <div className="flex flex-wrap items-center gap-6">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-gray-500 uppercase">Target Margin</span>
                                <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
                                    {[20, 25].map(m => (
                                        <button key={m} onClick={() => setSettings(s => ({...s, margin: m}))} className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${settings.margin === m ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow' : 'text-gray-600 dark:text-gray-400'}`}>{m}%</button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-gray-500 uppercase">Marketplace %</span>
                                <input type="number" value={settings.commission} onChange={e => setSettings(s => ({...s, commission: parseFloat(e.target.value) || 0}))} className="w-16 glass-input rounded-lg px-2 py-1.5 text-sm font-bold text-center" />
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-gray-500 uppercase">Outbound</span>
                                <input type="number" step="0.01" value={settings.ppCost} onChange={e => setSettings(s => ({...s, ppCost: parseFloat(e.target.value) || 0}))} className="w-16 glass-input rounded-lg px-2 py-1.5 text-sm font-bold text-center" />
                            </div>
                        </div>
                    </div>
                </div>
            );
        }'''

# Convert and preserve line endings
new_bytes = new_component.encode('utf-8')
new_bytes = new_bytes.replace(b'\n', LINE_END)

# Build new content
prefix = content[:start_idx]
suffix = content[end_idx:]
new_content = prefix + new_bytes + LINE_END + LINE_END + suffix

# Write
with open(file_path, 'wb') as f:
    f.write(new_content)

# Verify
check = new_content.decode('utf-8', errors='replace')
print(f"Integration complete!")
print(f"Script tags: {check.count('<script')} open, {check.count('</script>')} close")
print(f"Features: split layout, real-time calc, summary cards, premium styling")
