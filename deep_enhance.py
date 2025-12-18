# Enhancement 2: Add Price Endings toggle and Clear All, Row Starring

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

LINE_END = b'\r\n'

with open(file_path, 'rb') as f:
    content = f.read()

# === Enhancement 1: Price Endings Toggle in Simple View ===
# Find the Target Sell display and add price ending buttons

target_sell_marker = b'<div className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest">Target Sell</div>'
pos = content.find(target_sell_marker)

if pos == -1:
    print("Could not find Target Sell marker")
else:
    # Find the main sell display line
    sell_display = b'<div className="text-4xl md:text-5xl lg:text-6xl font-black text-gray-900 dark:text-white tracking-tight">{sell > 0 ? money(sell) : '
    sell_pos = content.find(sell_display, pos)
    
    if sell_pos != -1:
        # Find closing of this div
        close_pos = content.find(b'</div>', sell_pos)
        after_sell = close_pos + len(b'</div>')
        
        # Add price endings buttons
        price_endings = '''
                                    {/* Price Endings */}
                                    {sell > 0 && (
                                        <div className="flex gap-1 mt-2">
                                            <span className="text-[10px] text-gray-400 font-medium mr-1">End:</span>
                                            {[
                                                { label: 'Round', fn: (v) => Math.round(v) },
                                                { label: '.99', fn: (v) => Math.floor(v) + 0.99 },
                                                { label: '.95', fn: (v) => Math.floor(v) + 0.95 },
                                                { label: '.49', fn: (v) => Math.floor(v) + 0.49 }
                                            ].map(e => (
                                                <button 
                                                    key={e.label} 
                                                    onClick={() => setS(prev => ({ ...prev, manualTarget: e.fn(sell).toFixed(2) }))}
                                                    className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-all"
                                                >{e.label}</button>
                                            ))}
                                        </div>
                                    )}'''
        
        endings_bytes = price_endings.encode('utf-8').replace(b'\n', LINE_END)
        content = content[:after_sell] + LINE_END + endings_bytes + content[after_sell:]
        print("Added Price Endings toggle to Simple view")
    else:
        print("Could not find sell display")

# === Enhancement 2: Add Clear All and Row Starring to Bulk View ===
# Replace Bulk view again with enhanced version including starring

start_marker = b'function BulkQuickView({ priceRules, courierRules, active }) {'
end_marker = b'function Calculator()'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Cannot find Bulk function boundaries")
else:
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
    
    # Enhanced Bulk with starring
    new_component = '''        function BulkQuickView({ priceRules, courierRules, active }) {
            const [pricesText, setPricesText] = useState('');
            const [dimsText, setDimsText] = useState('');
            const [showAdvanced, setShowAdvanced] = useState(false);
            const [packText, setPackText] = useState('');
            const [weightText, setWeightText] = useState('');
            const [settings, setSettings] = useState({ margin: 25, commission: 15.3, ppCost: 2.70 });
            const [expandedRow, setExpandedRow] = useState(null);
            const [copied, setCopied] = useState(false);
            const [sortBy, setSortBy] = useState('order');
            const [starred, setStarred] = useState(new Set());

            const toggleStar = (i) => {
                setStarred(prev => {
                    const next = new Set(prev);
                    if (next.has(i)) next.delete(i);
                    else next.add(i);
                    return next;
                });
            };

            const clearAll = () => {
                setPricesText('');
                setDimsText('');
                setPackText('');
                setWeightText('');
                setStarred(new Set());
            };

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

                    const fx = 1.28, sea = 2800;
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
                    const status = marginPct >= settings.margin ? 'good' : marginPct >= 15 ? 'review' : 'low';

                    return { i: i + 1, unitUSD, pack, L, W, H, weight, vol, units, cartons, landedUnit, landedPack, sell, profit, marginPct, courier, status, dims: `${L}x${W}x${H}` };
                }).filter(Boolean);
            }, [pricesText, dimsText, packText, weightText, settings, courierRules]);

            const sortedRows = useMemo(() => {
                let sorted = [...rows];
                if (sortBy === 'starred') sorted = sorted.filter(r => starred.has(r.i));
                else if (sortBy === 'margin-asc') sorted.sort((a, b) => a.marginPct - b.marginPct);
                else if (sortBy === 'margin-desc') sorted.sort((a, b) => b.marginPct - a.marginPct);
                else if (sortBy === 'price') sorted.sort((a, b) => b.sell - a.sell);
                return sorted;
            }, [rows, sortBy, starred]);

            const stats = useMemo(() => ({
                total: rows.length,
                good: rows.filter(r => r.status === 'good').length,
                review: rows.filter(r => r.status === 'review').length,
                low: rows.filter(r => r.status === 'low').length,
                starred: starred.size,
                avgMargin: rows.length ? (rows.reduce((s, r) => s + r.marginPct, 0) / rows.length) : 0
            }), [rows, starred]);

            const copyAllPrices = () => {
                const prices = rows.map(r => r.sell.toFixed(2)).join('\\n');
                navigator.clipboard.writeText(prices);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            };

            const exportToCSV = () => {
                const headers = ['#', 'Starred', 'Buy (USD)', 'Dims (cm)', 'Pack', 'Landed (GBP)', 'Target Sell', 'Margin %', 'Profit', 'Units/40HQ', 'Courier', 'Courier Cost'];
                const csvRows = rows.map(r => [
                    r.i, starred.has(r.i) ? 'Yes' : '', r.unitUSD.toFixed(2), r.dims, r.pack, r.landedUnit.toFixed(2), r.sell.toFixed(2), r.marginPct.toFixed(1), r.profit.toFixed(2), r.units, r.courier?.carrier || '', r.courier?.cost?.toFixed(2) || ''
                ]);
                const csv = [headers.join(','), ...csvRows.map(r => r.join(','))].join('\\n');
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'bulk_pricing_' + new Date().toISOString().split('T')[0] + '.csv';
                a.click();
                URL.revokeObjectURL(url);
            };

            const money = (n) => Number.isFinite(n) ? `\\u00a3${n.toFixed(2)}` : '\\u2014';
            const statusColors = {
                good: { border: 'border-l-green-500', bg: 'bg-green-50/50 dark:bg-green-900/10', text: 'text-green-600', label: 'GOOD' },
                review: { border: 'border-l-amber-500', bg: 'bg-amber-50/50 dark:bg-amber-900/10', text: 'text-amber-600', label: 'CHECK' },
                low: { border: 'border-l-red-500', bg: 'bg-red-50/50 dark:bg-red-900/10', text: 'text-red-600', label: 'LOW' }
            };

            if (!active) return null;

            return (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* INPUT SIDE */}
                        <div className="lg:col-span-5 space-y-5">
                            {/* Header with Clear */}
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-bold text-gray-500">Enter product data</span>
                                {(pricesText || dimsText) && <button onClick={clearAll} className="text-xs font-bold text-red-500 hover:text-red-600">Clear All</button>}
                            </div>

                            {/* Primary: Unit Prices */}
                            <div className="relative">
                                <div className="absolute -inset-1 bg-gradient-to-r from-blue-400/25 to-indigo-500/25 rounded-2xl blur-md animate-pulse"></div>
                                <div className="relative glass-card rounded-2xl p-5 ring-2 ring-blue-400/60 dark:ring-indigo-400/60 shadow-xl shadow-blue-500/10">
                                    <div className="flex items-center justify-between mb-3">
                                        <label className="flex items-center gap-2 text-xs font-black text-blue-600 dark:text-blue-300 uppercase tracking-wide">
                                            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse shadow-lg shadow-blue-500/50"></span>
                                            Unit Prices (USD)
                                        </label>
                                        <span className="text-[10px] text-blue-400 font-medium">Paste from Excel</span>
                                    </div>
                                    <textarea className="w-full h-40 glass-input rounded-xl p-4 text-base font-bold !bg-blue-50/70 dark:!bg-indigo-900/40 font-mono leading-relaxed resize-none placeholder:text-blue-300 dark:placeholder:text-indigo-400 focus:ring-2 focus:ring-blue-400 transition-all" placeholder="2.35&#10;3.50&#10;4.20, 2  \\u2190 price, pack" value={pricesText} onChange={e => setPricesText(e.target.value)} />
                                </div>
                            </div>

                            {/* Dimensions */}
                            <div className="glass-card rounded-2xl p-5 hover:shadow-lg transition-shadow">
                                <div className="flex items-center justify-between mb-3">
                                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">Dimensions (cm)</label>
                                    <span className="text-[10px] text-gray-400">L x W x H</span>
                                </div>
                                <textarea className="w-full h-32 glass-input rounded-xl p-4 text-sm font-mono leading-relaxed resize-none focus:ring-2 focus:ring-gray-300 transition-all" placeholder="76x43x47&#10;80 40 50&#10;75-45-48" value={dimsText} onChange={e => setDimsText(e.target.value)} />
                            </div>

                            {/* Advanced Collapsed */}
                            <div className="glass-card rounded-2xl overflow-hidden hover:shadow-md transition-shadow">
                                <button onClick={() => setShowAdvanced(!showAdvanced)} className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                    <span className="text-sm font-bold text-gray-400">+ Pack Size, Weight (Optional)</span>
                                    <span className={`transition-transform duration-200 ${showAdvanced ? 'rotate-180' : ''}`}>\\u25bc</span>
                                </button>
                                <div className={`overflow-hidden transition-all duration-300 ${showAdvanced ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
                                    <div className="px-4 pb-4 space-y-3 border-t border-gray-100 dark:border-gray-800 pt-3">
                                        <div><label className="text-[10px] font-medium text-gray-400 mb-1 block uppercase">Pack Size</label><textarea className="w-full h-16 glass-input rounded-lg p-2 text-sm font-mono resize-none" placeholder="1&#10;2" value={packText} onChange={e => setPackText(e.target.value)} /></div>
                                        <div><label className="text-[10px] font-medium text-gray-400 mb-1 block uppercase">Weight (kg)</label><textarea className="w-full h-16 glass-input rounded-lg p-2 text-sm font-mono resize-none" placeholder="2.5&#10;3.0" value={weightText} onChange={e => setWeightText(e.target.value)} /></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* OUTPUT SIDE */}
                        <div className="lg:col-span-7 space-y-4">
                            {/* Settings + Actions Bar */}
                            <div className="glass-card rounded-xl p-4">
                                <div className="flex flex-wrap items-center justify-between gap-4">
                                    <div className="flex flex-wrap items-center gap-4">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-bold text-gray-400 uppercase">Margin</span>
                                            <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
                                                {[20, 25, 30].map(m => (
                                                    <button key={m} onClick={() => setSettings(s => ({...s, margin: m}))} className={`px-2.5 py-1 text-xs font-bold rounded-md transition-all ${settings.margin === m ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-md' : 'text-gray-500 hover:text-gray-700'}`}>{m}%</button>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <span className="text-[10px] font-bold text-gray-400 uppercase">Fee</span>
                                            <input type="number" value={settings.commission} onChange={e => setSettings(s => ({...s, commission: parseFloat(e.target.value) || 0}))} className="w-14 glass-input rounded-md px-2 py-1 text-xs font-bold text-center" />%
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <span className="text-[10px] font-bold text-gray-400 uppercase">P&P</span>
                                            \\u00a3<input type="number" step="0.01" value={settings.ppCost} onChange={e => setSettings(s => ({...s, ppCost: parseFloat(e.target.value) || 0}))} className="w-14 glass-input rounded-md px-2 py-1 text-xs font-bold text-center" />
                                        </div>
                                    </div>
                                    {rows.length > 0 && (
                                        <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="glass-input rounded-lg px-3 py-1.5 text-xs font-bold">
                                            <option value="order">Original Order</option>
                                            <option value="starred">\\u2605 Starred Only</option>
                                            <option value="margin-asc">Margin \\u2191 Low</option>
                                            <option value="margin-desc">Margin \\u2193 High</option>
                                            <option value="price">Price \\u2193 High</option>
                                        </select>
                                    )}
                                </div>
                            </div>

                            {rows.length > 0 ? (
                                <>
                                    {/* Summary + Export */}
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="flex items-center gap-3">
                                            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-100 dark:bg-green-900/30"><span className="w-2 h-2 rounded-full bg-green-500"></span><span className="text-sm font-bold text-green-700 dark:text-green-300">{stats.good}</span></div>
                                            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-100 dark:bg-amber-900/30"><span className="w-2 h-2 rounded-full bg-amber-500"></span><span className="text-sm font-bold text-amber-700 dark:text-amber-300">{stats.review}</span></div>
                                            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-100 dark:bg-red-900/30"><span className="w-2 h-2 rounded-full bg-red-500"></span><span className="text-sm font-bold text-red-700 dark:text-red-300">{stats.low}</span></div>
                                            {stats.starred > 0 && <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30"><span className="text-yellow-500">\\u2605</span><span className="text-sm font-bold text-yellow-700 dark:text-yellow-300">{stats.starred}</span></div>}
                                        </div>
                                        <div className="flex gap-2">
                                            <button onClick={copyAllPrices} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${copied ? 'bg-green-500 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200'}`}>{copied ? '\\u2713 Copied' : 'Copy Prices'}</button>
                                            <button onClick={exportToCSV} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 transition-all shadow-md">
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                                Export
                                            </button>
                                        </div>
                                    </div>

                                    {/* Results Cards */}
                                    <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
                                        {sortedRows.map(r => (
                                            <div key={r.i} className={`glass-card rounded-xl overflow-hidden transition-all duration-200 hover:shadow-lg border-l-4 ${statusColors[r.status].border} ${statusColors[r.status].bg} ${starred.has(r.i) ? 'ring-2 ring-yellow-400' : ''}`}>
                                                <div className="p-4 flex items-center gap-4">
                                                    {/* Star Button */}
                                                    <button onClick={(e) => { e.stopPropagation(); toggleStar(r.i); }} className={`text-xl transition-all ${starred.has(r.i) ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-400'}`}>
                                                        {starred.has(r.i) ? '\\u2605' : '\\u2606'}
                                                    </button>
                                                    <div className="w-8 h-8 rounded-lg bg-gray-200/50 dark:bg-gray-700/50 flex items-center justify-center text-xs font-bold text-gray-500">{r.i}</div>
                                                    <div className="flex-1 cursor-pointer" onClick={() => setExpandedRow(expandedRow === r.i ? null : r.i)}>
                                                        <div className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">{money(r.sell)}</div>
                                                        {r.pack > 1 && <div className="text-[10px] font-medium text-gray-400">Pack of {r.pack}</div>}
                                                    </div>
                                                    <div className="text-right">
                                                        <div className={`text-2xl font-black ${statusColors[r.status].text}`}>{r.marginPct.toFixed(1)}%</div>
                                                        <div className={`text-[10px] font-bold ${statusColors[r.status].text}`}>{statusColors[r.status].label}</div>
                                                    </div>
                                                    <div className="text-right min-w-[60px]">
                                                        <div className="text-xs text-gray-400 uppercase font-medium">Profit</div>
                                                        <div className={`text-lg font-bold ${statusColors[r.status].text}`}>{money(r.profit)}</div>
                                                    </div>
                                                    <div onClick={() => setExpandedRow(expandedRow === r.i ? null : r.i)} className={`cursor-pointer transition-transform duration-200 ${expandedRow === r.i ? 'rotate-180' : ''}`}><svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg></div>
                                                </div>
                                                <div className={`overflow-hidden transition-all duration-200 ${expandedRow === r.i ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}`}>
                                                    <div className="px-4 pb-4 pt-2 border-t border-gray-200/50 dark:border-gray-700/50 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                                                        <div><span className="text-gray-400 block">Buy (USD)</span><span className="font-bold">${r.unitUSD.toFixed(2)}</span></div>
                                                        <div><span className="text-gray-400 block">Landed</span><span className="font-bold">{money(r.landedUnit)}</span></div>
                                                        <div><span className="text-gray-400 block">Dims</span><span className="font-bold">{r.dims}cm</span></div>
                                                        <div><span className="text-gray-400 block">Courier</span><span className="font-bold">{r.courier ? `${r.courier.carrier} ${money(r.courier.cost)}` : '\\u2014'}</span></div>
                                                        <div><span className="text-gray-400 block">Units/40HQ</span><span className="font-bold">{r.units.toLocaleString()}</span></div>
                                                        <div><span className="text-gray-400 block">Cartons</span><span className="font-bold">{r.cartons.toLocaleString()}</span></div>
                                                        <div><span className="text-gray-400 block">CBM</span><span className="font-bold">{r.vol.toFixed(3)}</span></div>
                                                        {r.pack > 1 && <div><span className="text-gray-400 block">Landed/Pack</span><span className="font-bold">{money(r.landedPack)}</span></div>}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            ) : (
                                <div className="glass-card rounded-2xl p-12 text-center">
                                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 flex items-center justify-center"><svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg></div>
                                    <div className="text-lg font-bold text-gray-700 dark:text-gray-200 mb-2">Paste your prices</div>
                                    <div className="text-sm text-gray-400 max-w-xs mx-auto">Enter unit prices on the left and see instant calculations</div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Mobile Sticky */}
                    {rows.length > 0 && (
                        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-t border-gray-200/50 dark:border-gray-700/50 px-4 py-3 safe-area-bottom">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2"><span className="text-2xl font-black text-gray-900 dark:text-white">{stats.total}</span><span className="text-xs text-gray-500">products</span></div>
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center gap-1 text-green-600"><span className="font-bold">{stats.good}</span><span className="w-2 h-2 rounded-full bg-green-500"></span></div>
                                    <div className="flex items-center gap-1 text-amber-600"><span className="font-bold">{stats.review}</span><span className="w-2 h-2 rounded-full bg-amber-500"></span></div>
                                    <div className="flex items-center gap-1 text-red-600"><span className="font-bold">{stats.low}</span><span className="w-2 h-2 rounded-full bg-red-500"></span></div>
                                </div>
                                <button onClick={exportToCSV} className="px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white">Export</button>
                            </div>
                        </div>
                    )}
                </div>
            );
        }'''

    new_bytes = new_component.encode('utf-8').replace(b'\n', LINE_END)
    prefix = content[:start_idx]
    suffix = content[end_idx:]
    content = prefix + new_bytes + LINE_END + LINE_END + suffix
    print("Added Row Starring and Clear All to Bulk view")

with open(file_path, 'wb') as f:
    f.write(content)

print("\\nAll enhancements complete!")
print("- Price Endings toggle in Simple view")
print("- Clear All button in Bulk view")
print("- Row Starring with filter in Bulk view")
