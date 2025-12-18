# -*- coding: utf-8 -*-
"""
Bulk View Complete Redesign
Creates premium entry interface with settings bar, paste/upload areas
"""

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

# The file uses \r\r\r\n line endings
LINE_END = b'\r\r\r\n'

with open(file_path, 'rb') as f:
    content = f.read()

# Find BulkQuickView function boundaries
start_marker = b'function BulkQuickView({ priceRules, courierRules, active }) {'
end_marker = b'function Calculator()'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Cannot find function boundaries")
    exit(1)

# Find function end by counting braces
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

print(f"Replacing BulkQuickView from byte {start_idx} to {func_end}")

# The new premium Bulk view component
new_component = '''        function BulkQuickView({ priceRules, courierRules, active }) {
            const [text, setText] = useState("");
            const [rows, setRows] = useState([]);
            const [filter, setFilter] = useState('all');
            const [sortBy, setSortBy] = useState('margin');
            const [mode, setMode] = useState('simple');
            const [settings, setSettings] = useState({ targetMargin: 25, marketplaceFee: 15, fxRate: 1.28 });
            const [dragOver, setDragOver] = useState(false);

            const handleFileUpload = (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (ev) => setText(ev.target?.result || '');
                reader.readAsText(file);
            };

            const handleDrop = (e) => {
                e.preventDefault();
                setDragOver(false);
                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (ev) => setText(ev.target?.result || '');
                    reader.readAsText(file);
                }
            };

            useEffect(() => {
                if (!text.trim()) { setRows([]); return; }
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
                        const landed = buy + (c1 ? c1.cost : 0);
                        const profit = targetSell - landed - (targetSell * settings.marketplaceFee / 100);
                        const margin = (profit / targetSell) * 100;
                        return { sku, sell: targetSell, buy, landed, profit, marginPct: margin, courier: c1, dims: `${L}x${W}x${H}`, weight: `${weight}kg` };
                    } catch (e) { return null; }
                }).filter(Boolean);
                setRows(res);
            }, [text, courierRules, settings]);

            const filteredRows = rows.filter(r => {
                if (filter === 'profitable') return r.marginPct >= settings.targetMargin;
                if (filter === 'review') return r.marginPct >= 10 && r.marginPct < settings.targetMargin;
                if (filter === 'poor') return r.marginPct < 10;
                return true;
            });

            const sortedRows = [...filteredRows].sort((a, b) => {
                if (sortBy === 'margin') return b.marginPct - a.marginPct;
                if (sortBy === 'sku') return a.sku.localeCompare(b.sku);
                if (sortBy === 'courier') return (a.courier?.cost || 999) - (b.courier?.cost || 999);
                return 0;
            });

            const stats = { total: rows.length, profitable: rows.filter(r => r.marginPct >= settings.targetMargin).length, review: rows.filter(r => r.marginPct >= 10 && r.marginPct < settings.targetMargin).length, poor: rows.filter(r => r.marginPct < 10).length, avgMargin: rows.length ? (rows.reduce((sum, r) => sum + r.marginPct, 0) / rows.length) : 0 };

            const getColor = (m) => m >= settings.targetMargin ? 'text-green-600 dark:text-green-400' : m >= 10 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400';
            const getBg = (m) => m >= settings.targetMargin ? 'bg-green-500' : m >= 10 ? 'bg-amber-500' : 'bg-red-500';
            const getStatus = (m) => m >= settings.targetMargin ? 'STRONG' : m >= 10 ? 'REVIEW' : 'POOR';
            const getBorder = (m) => m >= settings.targetMargin ? 'border-green-500' : m >= 10 ? 'border-amber-500' : 'border-red-500';

            if (!active) return null;

            return (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Header with Mode Toggle */}
                    <div className="flex justify-between items-center">
                        <div>
                            <h2 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">Bulk Product Analyzer</h2>
                            <p className="text-sm text-gray-500 mt-1">Analyze multiple products at once</p>
                        </div>
                        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
                            <button onClick={() => setMode('simple')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${mode === 'simple' ? 'bg-white dark:bg-gray-700 shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}>Simple</button>
                            <button onClick={() => setMode('advanced')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${mode === 'advanced' ? 'bg-white dark:bg-gray-700 shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}>Advanced</button>
                        </div>
                    </div>

                    {/* Settings Bar */}
                    <div className="glass-card rounded-xl p-4">
                        <div className="flex flex-wrap items-center gap-6">
                            <div className="flex items-center gap-2">
                                <label className="text-xs font-bold text-gray-500 uppercase">Target Margin</label>
                                <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-1.5">
                                    <input type="number" value={settings.targetMargin} onChange={e => setSettings(s => ({...s, targetMargin: parseFloat(e.target.value) || 0}))} className="w-12 bg-transparent text-sm font-bold text-center focus:outline-none" />
                                    <span className="text-sm text-gray-400">%</span>
                                </div>
                            </div>
                            <div className="h-6 w-px bg-gray-200 dark:bg-gray-700"></div>
                            <div className="flex items-center gap-2">
                                <label className="text-xs font-bold text-gray-500 uppercase">Marketplace Fee</label>
                                <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-1.5">
                                    <input type="number" value={settings.marketplaceFee} onChange={e => setSettings(s => ({...s, marketplaceFee: parseFloat(e.target.value) || 0}))} className="w-12 bg-transparent text-sm font-bold text-center focus:outline-none" />
                                    <span className="text-sm text-gray-400">%</span>
                                </div>
                            </div>
                            {mode === 'advanced' && (
                                <>
                                    <div className="h-6 w-px bg-gray-200 dark:bg-gray-700"></div>
                                    <div className="flex items-center gap-2">
                                        <label className="text-xs font-bold text-gray-500 uppercase">FX Rate</label>
                                        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-1.5">
                                            <input type="number" step="0.01" value={settings.fxRate} onChange={e => setSettings(s => ({...s, fxRate: parseFloat(e.target.value) || 1}))} className="w-16 bg-transparent text-sm font-bold text-center focus:outline-none" />
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Data Entry Section */}
                    <div className="glass-card rounded-2xl p-6 border border-indigo-50 dark:border-indigo-900/20">
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Paste Area */}
                            <div className={`relative rounded-xl border-2 border-dashed transition-all ${dragOver ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'}`} onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={handleDrop}>
                                <div className="absolute top-3 left-4 right-4 flex justify-between items-center pointer-events-none">
                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wide">Paste Data</span>
                                    <span className="text-xs text-gray-400">or drag CSV here</span>
                                </div>
                                <textarea className="w-full h-40 pt-10 px-4 pb-4 bg-transparent rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none" placeholder="SKU, Sell Price, Buy Price, L, W, H, Weight&#10;PROD-001, 29.99, 8.50, 45, 30, 20, 2.5&#10;PROD-002, 19.99, 12.00, 30, 25, 15, 1.2" value={text} onChange={e => setText(e.target.value)} />
                            </div>

                            {/* Instructions + Upload */}
                            <div className="flex flex-col gap-4">
                                <div className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-xl p-5 space-y-3">
                                    <div className="text-xs font-bold text-gray-500 uppercase mb-3">Expected Format</div>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">1</span><span className="text-gray-600 dark:text-gray-300">SKU / Product ID</span></div>
                                        <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">2</span><span className="text-gray-600 dark:text-gray-300">Target Sell Price</span></div>
                                        <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">3</span><span className="text-gray-600 dark:text-gray-300">Buy/Cost Price</span></div>
                                        <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">4-6</span><span className="text-gray-600 dark:text-gray-300">Dimensions (L, W, H in cm)</span></div>
                                        <div className="flex items-center gap-3"><span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">7</span><span className="text-gray-600 dark:text-gray-300">Weight (kg)</span></div>
                                    </div>
                                </div>
                                <label className="flex items-center justify-center gap-3 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl cursor-pointer transition-all font-bold text-sm">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                                    Upload CSV File
                                    <input type="file" accept=".csv,.txt" onChange={handleFileUpload} className="hidden" />
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Results Section */}
                    {rows.length > 0 && (
                        <>
                            {/* Stats Bar */}
                            <div className="glass-card rounded-xl p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20">
                                <div className="flex flex-wrap items-center gap-6">
                                    <div><div className="text-xs uppercase text-gray-500 font-bold">Products</div><div className="text-2xl font-black">{stats.total}</div></div>
                                    <div className="h-8 w-px bg-gray-300 dark:bg-gray-700"></div>
                                    <div className="flex gap-4">
                                        <div><div className="text-xs text-gray-500">Profitable</div><div className="font-bold text-green-600">{stats.profitable}</div></div>
                                        <div><div className="text-xs text-gray-500">Review</div><div className="font-bold text-amber-600">{stats.review}</div></div>
                                        <div><div className="text-xs text-gray-500">Poor</div><div className="font-bold text-red-600">{stats.poor}</div></div>
                                    </div>
                                    <div className="h-8 w-px bg-gray-300 dark:bg-gray-700"></div>
                                    <div><div className="text-xs text-gray-500">Avg Margin</div><div className="font-bold text-lg">{stats.avgMargin.toFixed(1)}%</div></div>
                                </div>
                            </div>

                            {/* Filters */}
                            <div className="flex flex-wrap gap-3 items-center">
                                <div className="flex gap-2">
                                    {['all', 'profitable', 'review', 'poor'].map(f => (
                                        <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-all ${filter === f ? (f === 'profitable' ? 'bg-green-600 text-white' : f === 'review' ? 'bg-amber-600 text-white' : f === 'poor' ? 'bg-red-600 text-white' : 'bg-indigo-600 text-white') : 'bg-gray-100 dark:bg-gray-800 text-gray-600 hover:bg-gray-200'}`}>{f}</button>
                                    ))}
                                </div>
                                <div className="h-6 w-px bg-gray-300 dark:bg-gray-700"></div>
                                <div className="flex gap-2 items-center">
                                    <span className="text-xs text-gray-500 font-bold">SORT:</span>
                                    {['margin', 'sku', 'courier'].map(s => (
                                        <button key={s} onClick={() => setSortBy(s)} className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-all ${sortBy === s ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 hover:bg-gray-200'}`}>{s}</button>
                                    ))}
                                </div>
                            </div>

                            {/* Results Table */}
                            <div className="glass-card rounded-2xl overflow-hidden shadow-xl border border-gray-100 dark:border-gray-800">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50/80 dark:bg-gray-800/80 font-bold text-gray-500 uppercase text-[10px] tracking-wider">
                                            <tr><th className="px-4 py-4 text-center">#</th><th className="px-6 py-4 text-left">Product</th><th className="px-6 py-4 text-center">Margin</th><th className="px-6 py-4 text-right">Profit</th><th className="px-6 py-4 text-right">Courier</th></tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                            {sortedRows.map((r, i) => (
                                                <tr key={i} className="hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 transition-colors">
                                                    <td className="px-4 py-4 text-center text-gray-400">#{i+1}</td>
                                                    <td className="px-6 py-4"><div className="font-bold">{r.sku}</div><div className="text-xs text-gray-400">{r.dims} - {r.weight}</div></td>
                                                    <td className="px-6 py-4 text-center"><div className={`text-xl font-black ${getColor(r.marginPct)}`}>{r.marginPct.toFixed(1)}%</div><div className="w-full h-1 bg-gray-200 rounded-full mt-1"><div className={`h-full rounded-full ${getBg(r.marginPct)}`} style={{width:`${Math.min(100,r.marginPct*2)}%`}}/></div><div className={`text-[10px] font-bold ${getColor(r.marginPct)} mt-1`}>{getStatus(r.marginPct)}</div></td>
                                                    <td className="px-6 py-4 text-right"><div className="text-xs text-gray-400">Sell: {fmt(r.sell)}</div><div className={`font-bold ${getColor(r.marginPct)}`}>+{fmt(r.profit)}</div></td>
                                                    <td className="px-6 py-4 text-right">{r.courier ? <div><div className="font-bold text-indigo-600">{r.courier.carrier}</div><div className="text-xs text-gray-500">{fmt(r.courier.cost)}</div></div> : <span className="text-xs text-red-400">N/A</span>}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            );
        }'''

# Convert to bytes with correct line endings
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
print(f"New features: mode toggle, settings bar, CSV upload, drag-drop")
