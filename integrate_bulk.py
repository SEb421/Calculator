# -*- coding: utf-8 -*-
"""
Enhanced BulkQuickView Integration
CRITICAL: Preserves the file's \r\r\r\n line ending pattern
"""

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

# Read file
with open(file_path, 'rb') as f:
    content = f.read()

# The file uses \r\r\r\n line endings - we must preserve this
LINE_END = b'\r\r\r\n'

# Find the old BulkQuickView function boundaries
start_marker = b'function BulkQuickView({ priceRules, courierRules, active }) {'
end_marker = b'function Calculator()'

start_idx = content.find(start_marker)
if start_idx == -1:
    print("ERROR: Cannot find BulkQuickView function start")
    exit(1)

end_idx = content.find(end_marker)
if end_idx == -1:
    print("ERROR: Cannot find Calculator function")
    exit(1)

# Find the actual end of BulkQuickView by counting braces
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

if func_end is None:
    print("ERROR: Cannot find function end")
    exit(1)

print(f"Found BulkQuickView at bytes {start_idx}-{func_end}")
print(f"Calculator() starts at byte {end_idx}")

# The enhanced BulkQuickView - using the file's line ending pattern
# Note: Convert \n to \r\r\r\n to match file format
enhanced = '''        function BulkQuickView({ priceRules, courierRules, active }) {
            const [text, setText] = useState("");
            const [rows, setRows] = useState([]);
            const [filter, setFilter] = useState('all');
            const [sortBy, setSortBy] = useState('margin');

            useEffect(() => {
                if (!text.trim()) { setRows([]); return; }
                const calculate = () => {
                    const lines = text.split("\\n").filter(l => l.trim());
                    const res = lines.map(line => {
                        const parts = line.split(/[\\t,]+/).map(p => p.trim()).filter(Boolean);
                        if (parts.length < 7) return null;
                        try {
                            const sku = parts[0];
                            const targetSell = parseFloat(parts[1]);
                            const buy = parseFloat(parts[2]);
                            const L = parseFloat(parts[3]);
                            const W = parseFloat(parts[4]);
                            const H = parseFloat(parts[5]);
                            const weight = parseFloat(parts[6]);
                            const c1 = chooseCourier(L, W, H, weight, courierRules);
                            const courierCost = c1 ? c1.cost : 0;
                            const landed = buy + courierCost;
                            const profit = targetSell - landed;
                            const margin = (profit / targetSell) * 100;
                            return { sku, sell: targetSell, buy, landed, profit, marginPct: margin, courier: c1 ? { ...c1, reason: "Best option" } : null, dims: `${L}x${W}x${H}cm`, weight: `${weight}kg` };
                        } catch (e) { return null; }
                    }).filter(Boolean);
                    setRows(res);
                };
                calculate();
            }, [text, courierRules]);

            const filteredRows = rows.filter(r => {
                if (filter === 'profitable') return r.marginPct >= 20;
                if (filter === 'review') return r.marginPct >= 10 && r.marginPct < 20;
                if (filter === 'poor') return r.marginPct < 10;
                return true;
            });

            const sortedRows = [...filteredRows].sort((a, b) => {
                if (sortBy === 'margin') return b.marginPct - a.marginPct;
                if (sortBy === 'sku') return a.sku.localeCompare(b.sku);
                if (sortBy === 'courier') return (a.courier?.cost || 999) - (b.courier?.cost || 999);
                return 0;
            });

            const stats = { total: rows.length, profitable: rows.filter(r => r.marginPct >= 20).length, review: rows.filter(r => r.marginPct >= 10 && r.marginPct < 20).length, poor: rows.filter(r => r.marginPct < 10).length, avgMargin: rows.length ? (rows.reduce((sum, r) => sum + r.marginPct, 0) / rows.length) : 0 };

            const getStatusColor = (m) => m >= 20 ? 'text-green-600 dark:text-green-400' : m >= 10 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400';
            const getStatusBg = (m) => m >= 20 ? 'bg-green-500' : m >= 10 ? 'bg-amber-500' : 'bg-red-500';
            const getStatusText = (m) => m >= 20 ? 'STRONG' : m >= 10 ? 'REVIEW' : 'POOR';
            const getBorderColor = (m) => m >= 20 ? 'border-green-500' : m >= 10 ? 'border-amber-500' : 'border-red-500';

            if (!active) return null;

            return (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="glass-card rounded-2xl p-6 border border-indigo-50 dark:border-indigo-900/20">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">Bulk Analysis</h2>
                                <p className="text-sm text-gray-500">Paste data to instantly screen profitable products.</p>
                            </div>
                            {rows.length > 0 && <div className="text-xs px-3 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-full font-medium">{rows.length} Products</div>}
                        </div>
                        <div className="grid md:grid-cols-2 gap-6">
                            <div>
                                <label className="text-xs font-bold uppercase text-gray-400 mb-2 block">Paste Data (Excel/CSV)</label>
                                <textarea className="w-full h-32 glass-input rounded-xl p-4 text-xs font-mono leading-relaxed" placeholder={`Format: SKU, Sell, Buy, L, W, H, Weight\\nExample:\\nPROD-001, 29.99, 8.50, 45, 30, 20, 2.5`} value={text} onChange={e => setText(e.target.value)} />
                            </div>
                            <div className="flex flex-col justify-center gap-4 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-dashed border-gray-200 dark:border-gray-700">
                                <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-bold">1</span> <span>Copy columns from Excel</span></div>
                                <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">2</span> <span>Paste left</span></div>
                                <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-xs font-bold">3</span> <span>See insights</span></div>
                            </div>
                        </div>
                    </div>

                    {rows.length > 0 && (
                        <div className="glass-card rounded-xl p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20">
                            <div className="flex flex-wrap items-center gap-6">
                                <div><div className="text-xs uppercase text-gray-500 font-bold">Analyzing</div><div className="text-2xl font-black">{stats.total}</div></div>
                                <div className="h-8 w-px bg-gray-300 dark:bg-gray-700"></div>
                                <div className="flex gap-4">
                                    <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-green-500"></div><div><div className="text-xs text-gray-500">Profitable</div><div className="font-bold text-green-600">{stats.profitable}</div></div></div>
                                    <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-amber-500"></div><div><div className="text-xs text-gray-500">Review</div><div className="font-bold text-amber-600">{stats.review}</div></div></div>
                                    <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-500"></div><div><div className="text-xs text-gray-500">Poor</div><div className="font-bold text-red-600">{stats.poor}</div></div></div>
                                </div>
                                <div className="h-8 w-px bg-gray-300 dark:bg-gray-700"></div>
                                <div><div className="text-xs text-gray-500">Avg Margin</div><div className="font-bold text-lg">{stats.avgMargin.toFixed(1)}%</div></div>
                            </div>
                        </div>
                    )}

                    {rows.length > 0 && (
                        <div className="flex flex-wrap gap-3 items-center">
                            <div className="flex gap-2">
                                <button onClick={() => setFilter('all')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${filter === 'all' ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>All</button>
                                <button onClick={() => setFilter('profitable')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${filter === 'profitable' ? 'bg-green-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>Profitable</button>
                                <button onClick={() => setFilter('review')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${filter === 'review' ? 'bg-amber-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>Review</button>
                                <button onClick={() => setFilter('poor')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${filter === 'poor' ? 'bg-red-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>Poor</button>
                            </div>
                            <div className="h-6 w-px bg-gray-300 dark:bg-gray-700"></div>
                            <div className="flex gap-2 items-center">
                                <span className="text-xs text-gray-500 font-bold">SORT:</span>
                                <button onClick={() => setSortBy('margin')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${sortBy === 'margin' ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>Margin</button>
                                <button onClick={() => setSortBy('sku')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${sortBy === 'sku' ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>SKU</button>
                                <button onClick={() => setSortBy('courier')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${sortBy === 'courier' ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}>Courier</button>
                            </div>
                        </div>
                    )}

                    {sortedRows.length > 0 && (
                        <div className="block md:hidden space-y-4">
                            {sortedRows.map((r, i) => (
                                <div key={i} className={`glass-card rounded-xl p-4 border-l-4 ${getBorderColor(r.marginPct)}`}>
                                    <div className="flex justify-between items-start mb-3">
                                        <div><div className="font-bold text-lg">{r.sku}</div><div className="text-xs text-gray-400">{r.dims} - {r.weight}</div></div>
                                        <div className="text-xs text-gray-400">#{i + 1}</div>
                                    </div>
                                    <div className="mb-3">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className={`text-3xl font-black ${getStatusColor(r.marginPct)}`}>{r.marginPct.toFixed(1)}%</span>
                                            <span className={`text-xs font-bold ${getStatusColor(r.marginPct)} uppercase px-2 py-1 rounded ${r.marginPct >= 20 ? 'bg-green-100 dark:bg-green-900/30' : r.marginPct >= 10 ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>{getStatusText(r.marginPct)}</span>
                                        </div>
                                        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><div className={`h-full ${getStatusBg(r.marginPct)}`} style={{ width: `${Math.min(100, Math.max(0, r.marginPct * 2))}%` }} /></div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                                        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-2"><div className="text-xs text-gray-500">Sell</div><div className="font-bold">{fmt(r.sell)}</div></div>
                                        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-2"><div className="text-xs text-gray-500">Profit</div><div className={`font-bold ${getStatusColor(r.marginPct)}`}>{fmt(r.profit)}</div></div>
                                    </div>
                                    {r.courier && <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-3 border border-indigo-200 dark:border-indigo-800"><div className="flex items-center justify-between"><div><div className="text-sm font-bold text-indigo-700 dark:text-indigo-300">{r.courier.carrier}</div><div className="text-xs text-gray-500">{fmt(r.courier.cost)}</div></div><div className="text-xs text-green-600 font-bold">Fits</div></div></div>}
                                </div>
                            ))}
                        </div>
                    )}

                    {sortedRows.length > 0 && (
                        <div className="hidden md:block glass-card rounded-2xl overflow-hidden shadow-xl border border-gray-100 dark:border-gray-800">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50/80 dark:bg-gray-800/80 backdrop-blur font-bold text-gray-500 dark:text-gray-400 uppercase text-[10px] tracking-wider sticky top-0 z-10">
                                        <tr><th className="px-4 py-4 text-center w-16">#</th><th className="px-6 py-4 text-left">Product</th><th className="px-6 py-4 text-center w-32">Margin</th><th className="px-6 py-4 text-right">Finances</th><th className="px-6 py-4 text-right">Courier</th></tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                        {sortedRows.map((r, i) => (
                                            <tr key={i} className="group hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 transition-colors">
                                                <td className="px-4 py-4 text-center"><span className="text-gray-400">#{i + 1}</span></td>
                                                <td className="px-6 py-4"><div className="font-bold text-gray-900 dark:text-white">{r.sku}</div><div className="text-xs text-gray-400 font-mono mt-0.5">{r.dims} - {r.weight}</div></td>
                                                <td className="px-6 py-4"><div className="flex flex-col items-center"><div className={`text-2xl font-black ${getStatusColor(r.marginPct)} mb-1`}>{r.marginPct.toFixed(1)}%</div><div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><div className={`h-full ${getStatusBg(r.marginPct)}`} style={{width: `${Math.min(100, Math.max(0, r.marginPct * 2))}%`}} /></div><div className={`text-[10px] font-bold ${getStatusColor(r.marginPct)} uppercase mt-1`}>{getStatusText(r.marginPct)}</div></div></td>
                                                <td className="px-6 py-4 text-right"><div className="flex flex-col items-end gap-1"><div className="text-xs text-gray-400">Sell: <span className="font-bold text-gray-700 dark:text-gray-300">{fmt(r.sell)}</span></div><div className="text-xs text-gray-400">Buy: {fmt(r.buy)}</div><div className={`text-sm font-bold ${getStatusColor(r.marginPct)}`}>+{fmt(r.profit)}</div></div></td>
                                                <td className="px-6 py-4 text-right">{r.courier ? <div className="flex flex-col items-end"><span className="font-bold text-indigo-600 dark:text-indigo-400">{r.courier.carrier}</span><span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full font-mono mt-1">{fmt(r.courier.cost)}</span></div> : <span className="text-xs text-red-400 font-bold bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">No Courier</span>}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            );
        }'''

# Convert to bytes with the correct line endings
enhanced_bytes = enhanced.encode('utf-8')
# Replace \n with \r\r\r\n
enhanced_bytes = enhanced_bytes.replace(b'\n', LINE_END)

# Build new content
prefix = content[:start_idx]
suffix = content[end_idx:]

# Need to find whitespace between old function end and Calculator
between = content[func_end:end_idx]
# Keep the line endings before Calculator()
new_content = prefix + enhanced_bytes + LINE_END + LINE_END + suffix

# Write
with open(file_path, 'wb') as f:
    f.write(new_content)

# Verify
check = new_content.decode('utf-8', errors='replace')
script_open = check.count('<script')
script_close = check.count('</script>')
has_filter = 'setFilter' in check
has_sort = 'setSortBy' in check

print(f"\nIntegration complete!")
print(f"Script tags: {script_open} open, {script_close} close")
print(f"New features: filter={has_filter}, sort={has_sort}")

if script_open != script_close:
    print("WARNING: Script tags unbalanced!")
