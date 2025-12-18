# Premium Bulk View Design Polish
# Focus on visual design improvements

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

LINE_END = b'\r\n'

with open(file_path, 'rb') as f:
    content = f.read()

start_marker = b'function BulkQuickView({ priceRules, courierRules, active }) {'
end_marker = b'function Calculator()'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Cannot find function boundaries")
    exit(1)

print(f"Replacing Bulk view at {start_idx} with premium design")

# Premium Bulk with enhanced design
new_component = '''        function BulkQuickView({ priceRules, courierRules, active }) {
            const [pricesText, setPricesText] = useState('');
            const [dimsText, setDimsText] = useState('');
            const [skusText, setSkusText] = useState('');
            const [showAdvanced, setShowAdvanced] = useState(false);
            const [packText, setPackText] = useState('');
            const [weightText, setWeightText] = useState('');
            const [settings, setSettings] = useState({ margin: 25, commission: 15.3, ppCost: 2.70 });
            const [expandedRow, setExpandedRow] = useState(null);
            const [copied, setCopied] = useState(false);
            const [sortBy, setSortBy] = useState('order');
            const [starred, setStarred] = useState(new Set());
            const [priceEnding, setPriceEnding] = useState(null);

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
                setSkusText('');
                setPackText('');
                setWeightText('');
                setStarred(new Set());
                setPriceEnding(null);
            };

            const applyEnding = (ending) => setPriceEnding(ending);

            const getEndedPrice = (price, ending) => {
                if (!ending) return price;
                if (ending === 'round') return Math.round(price);
                if (ending === '.99') return Math.floor(price) + 0.99;
                if (ending === '.95') return Math.floor(price) + 0.95;
                if (ending === '.49') return Math.floor(price) + 0.49;
                return price;
            };

            const rows = useMemo(() => {
                const prices = pricesText.split('\\n').map(l => l.trim()).filter(Boolean);
                const dims = dimsText.split('\\n').map(l => l.trim());
                const skus = skusText.split('\\n').map(l => l.trim());
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
                    const sku = skus[i] || '';

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
                    const rawSell = requiredSellForMargin(settings.margin, purchaseInc, settings.commission, settings.ppCost, 0);
                    const sell = getEndedPrice(rawSell, priceEnding);
                    const profit = sell > 0 ? computeProfit(sell, purchaseInc, settings.commission, settings.ppCost, 0) : 0;
                    const marginPct = sell > 0 ? (profit / sell) * 100 : 0;
                    const courier = L > 0 && W > 0 && H > 0 ? chooseCourier(L, W, H, weight, courierRules) : null;
                    const status = marginPct >= settings.margin ? 'good' : marginPct >= 15 ? 'review' : 'low';

                    return { i: i + 1, sku, unitUSD, pack, L, W, H, weight, vol, units, cartons, landedUnit, landedPack, sell, rawSell, profit, marginPct, courier, status, dims: `${L}x${W}x${H}` };
                }).filter(Boolean);
            }, [pricesText, dimsText, skusText, packText, weightText, settings, courierRules, priceEnding]);

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
                avgMargin: rows.length ? (rows.reduce((s, r) => s + r.marginPct, 0) / rows.length) : 0,
                totalProfit: rows.reduce((s, r) => s + r.profit, 0),
                totalRevenue: rows.reduce((s, r) => s + r.sell, 0)
            }), [rows, starred]);

            const copyAllPrices = () => {
                const prices = rows.map(r => r.sell.toFixed(2)).join('\\n');
                navigator.clipboard.writeText(prices);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            };

            const exportToCSV = () => {
                const headers = ['#', 'SKU', 'Starred', 'Buy (USD)', 'Dims (cm)', 'Pack', 'Landed (GBP)', 'Target Sell', 'Margin %', 'Profit', 'Units/40HQ', 'Courier', 'Courier Cost'];
                const csvRows = rows.map(r => [
                    r.i, r.sku, starred.has(r.i) ? 'Yes' : '', r.unitUSD.toFixed(2), r.dims, r.pack, r.landedUnit.toFixed(2), r.sell.toFixed(2), r.marginPct.toFixed(1), r.profit.toFixed(2), r.units, r.courier?.carrier || '', r.courier?.cost?.toFixed(2) || ''
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
                good: { border: 'border-l-emerald-500', bg: 'bg-gradient-to-r from-emerald-50/80 to-transparent dark:from-emerald-900/20', text: 'text-emerald-600', label: 'GOOD' },
                review: { border: 'border-l-amber-500', bg: 'bg-gradient-to-r from-amber-50/80 to-transparent dark:from-amber-900/20', text: 'text-amber-600', label: 'CHECK' },
                low: { border: 'border-l-rose-500', bg: 'bg-gradient-to-r from-rose-50/80 to-transparent dark:from-rose-900/20', text: 'text-rose-600', label: 'LOW' }
            };

            if (!active) return null;

            return (
                <div className="space-y-6">
                    {/* Decorative Background */}
                    <div className="absolute inset-0 overflow-hidden pointer-events-none">
                        <div className="absolute top-20 right-10 w-72 h-72 bg-gradient-to-br from-blue-400/5 to-purple-500/5 rounded-full blur-3xl"></div>
                        <div className="absolute bottom-20 left-10 w-64 h-64 bg-gradient-to-tr from-emerald-400/5 to-cyan-500/5 rounded-full blur-3xl"></div>
                    </div>

                    <div className="relative grid grid-cols-1 lg:grid-cols-12 gap-8">
                        {/* INPUT SIDE */}
                        <div className="lg:col-span-5 space-y-5">
                            {/* Header Card */}
                            <div className="flex items-center justify-between bg-gradient-to-r from-gray-50 to-transparent dark:from-gray-800/50 rounded-xl px-4 py-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                    </div>
                                    <div>
                                        <div className="text-sm font-black text-gray-800 dark:text-white">Bulk Calculator</div>
                                        <div className="text-xs text-gray-500">Paste multiple products</div>
                                    </div>
                                </div>
                                {(pricesText || dimsText) && <button onClick={clearAll} className="px-3 py-1.5 rounded-lg text-xs font-bold text-rose-500 bg-rose-50 dark:bg-rose-900/20 hover:bg-rose-100 transition-all">Clear All</button>}
                            </div>

                            {/* SKU/Name */}
                            <div className="group glass-card rounded-2xl p-5 hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-gray-900/50 transition-all duration-300 border border-gray-100 dark:border-gray-800">
                                <div className="flex items-center justify-between mb-3">
                                    <label className="flex items-center gap-2 text-xs font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wide">
                                        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                                        SKU / Name
                                    </label>
                                    <span className="text-[10px] text-gray-400 font-medium bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">Optional</span>
                                </div>
                                <textarea className="w-full h-20 glass-input rounded-xl p-4 text-sm font-mono resize-none focus:ring-2 focus:ring-indigo-300 dark:focus:ring-indigo-600 transition-all" placeholder="PROD-001&#10;Blue Widget&#10;RED-XL" value={skusText} onChange={e => setSkusText(e.target.value)} />
                            </div>

                            {/* Primary: Unit Prices */}
                            <div className="relative group">
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-2xl opacity-75 blur group-hover:opacity-100 transition-all duration-300 animate-pulse"></div>
                                <div className="relative glass-card rounded-2xl p-5 bg-white dark:bg-gray-900 border-2 border-transparent">
                                    <div className="flex items-center justify-between mb-3">
                                        <label className="flex items-center gap-2 text-xs font-black text-indigo-600 dark:text-indigo-300 uppercase tracking-wide">
                                            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse shadow-lg shadow-indigo-500/50"></span>
                                            Unit Prices (USD)
                                        </label>
                                        <span className="text-[10px] text-indigo-400 font-bold bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full">Paste from Excel</span>
                                    </div>
                                    <textarea className="w-full h-32 glass-input rounded-xl p-4 text-base font-bold !bg-indigo-50/50 dark:!bg-indigo-950/30 font-mono leading-relaxed resize-none placeholder:text-indigo-300 dark:placeholder:text-indigo-500 focus:ring-2 focus:ring-indigo-400 transition-all" placeholder="2.35&#10;3.50&#10;4.20, 2" value={pricesText} onChange={e => setPricesText(e.target.value)} />
                                </div>
                            </div>

                            {/* Dimensions */}
                            <div className="group glass-card rounded-2xl p-5 hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-gray-900/50 transition-all duration-300 border border-gray-100 dark:border-gray-800">
                                <div className="flex items-center justify-between mb-3">
                                    <label className="flex items-center gap-2 text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                                        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
                                        Dimensions (cm)
                                    </label>
                                    <span className="text-[10px] text-gray-400 font-medium">L x W x H</span>
                                </div>
                                <textarea className="w-full h-24 glass-input rounded-xl p-4 text-sm font-mono leading-relaxed resize-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600 transition-all" placeholder="76x43x47&#10;80 40 50&#10;75-45-48" value={dimsText} onChange={e => setDimsText(e.target.value)} />
                            </div>

                            {/* Advanced Collapsed */}
                            <div className="glass-card rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 transition-all">
                                <button onClick={() => setShowAdvanced(!showAdvanced)} className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                    <span className="flex items-center gap-2 text-sm font-bold text-gray-500">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                                        Pack Size, Weight
                                    </span>
                                    <span className={`transition-transform duration-300 ${showAdvanced ? 'rotate-180' : ''}`}>
                                        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                    </span>
                                </button>
                                <div className={`overflow-hidden transition-all duration-300 ${showAdvanced ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
                                    <div className="px-4 pb-4 space-y-3 border-t border-gray-100 dark:border-gray-800 pt-3">
                                        <div><label className="text-[10px] font-bold text-gray-400 mb-1.5 block uppercase tracking-wide">Pack Size</label><textarea className="w-full h-16 glass-input rounded-lg p-3 text-sm font-mono resize-none" placeholder="1&#10;2" value={packText} onChange={e => setPackText(e.target.value)} /></div>
                                        <div><label className="text-[10px] font-bold text-gray-400 mb-1.5 block uppercase tracking-wide">Weight (kg)</label><textarea className="w-full h-16 glass-input rounded-lg p-3 text-sm font-mono resize-none" placeholder="2.5&#10;3.0" value={weightText} onChange={e => setWeightText(e.target.value)} /></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* OUTPUT SIDE */}
                        <div className="lg:col-span-7 space-y-5">
                            {/* Settings Bar - Premium Design */}
                            <div className="glass-card rounded-2xl p-4 bg-gradient-to-r from-gray-50 via-white to-gray-50 dark:from-gray-800/80 dark:via-gray-900 dark:to-gray-800/80 border border-gray-100 dark:border-gray-800">
                                <div className="flex flex-wrap items-center justify-between gap-4">
                                    <div className="flex flex-wrap items-center gap-5">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Margin</span>
                                            <div className="flex bg-gray-100 dark:bg-gray-800 rounded-xl p-1 shadow-inner">
                                                {[20, 25, 30].map(m => (
                                                    <button key={m} onClick={() => setSettings(s => ({...s, margin: m}))} className={`px-3 py-1.5 text-xs font-black rounded-lg transition-all duration-200 ${settings.margin === m ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/30 scale-105' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'}`}>{m}%</button>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                                            <span className="text-[10px] font-black text-gray-400 uppercase">Fee</span>
                                            <input type="number" value={settings.commission} onChange={e => setSettings(s => ({...s, commission: parseFloat(e.target.value) || 0}))} className="w-14 bg-white dark:bg-gray-900 rounded-lg px-2 py-1 text-xs font-bold text-center border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-indigo-400" />
                                            <span className="text-xs font-bold text-gray-400">%</span>
                                        </div>
                                        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                                            <span className="text-[10px] font-black text-gray-400 uppercase">P&P</span>
                                            <span className="text-xs font-bold text-gray-400">\\u00a3</span>
                                            <input type="number" step="0.01" value={settings.ppCost} onChange={e => setSettings(s => ({...s, ppCost: parseFloat(e.target.value) || 0}))} className="w-14 bg-white dark:bg-gray-900 rounded-lg px-2 py-1 text-xs font-bold text-center border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-indigo-400" />
                                        </div>
                                    </div>
                                    {rows.length > 0 && (
                                        <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="bg-white dark:bg-gray-800 rounded-xl px-4 py-2 text-xs font-bold border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-indigo-400 cursor-pointer">
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
                                    {/* Price Endings + Profit Summary */}
                                    <div className="glass-card rounded-2xl p-4 border border-gray-100 dark:border-gray-800">
                                        <div className="flex flex-wrap items-center justify-between gap-4">
                                            <div className="flex items-center gap-3">
                                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Endings</span>
                                                <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
                                                    {[null, 'round', '.99', '.95', '.49'].map(e => (
                                                        <button key={e || 'auto'} onClick={() => applyEnding(e)} className={`px-2.5 py-1 text-[10px] font-bold rounded-lg transition-all ${priceEnding === e ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700 hover:bg-white dark:hover:bg-gray-700'}`}>
                                                            {e === null ? 'Auto' : e === 'round' ? 'Round' : e}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-6">
                                                <div className="text-right">
                                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wide">Total Profit</div>
                                                    <div className="text-xl font-black bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-transparent">{money(stats.totalProfit)}</div>
                                                </div>
                                                <div className="w-px h-10 bg-gradient-to-b from-transparent via-gray-200 dark:via-gray-700 to-transparent"></div>
                                                <div className="text-right">
                                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wide">Avg Margin</div>
                                                    <div className="text-xl font-black text-gray-700 dark:text-gray-200">{stats.avgMargin.toFixed(1)}%</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Status Pills + Actions */}
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="flex items-center gap-2">
                                            {[['good', 'emerald'], ['review', 'amber'], ['low', 'rose']].map(([key, color]) => (
                                                <div key={key} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-${color}-100 dark:bg-${color}-900/30 border border-${color}-200 dark:border-${color}-800/50`}>
                                                    <span className={`w-2 h-2 rounded-full bg-${color}-500`}></span>
                                                    <span className={`text-sm font-bold text-${color}-700 dark:text-${color}-300`}>{stats[key]}</span>
                                                </div>
                                            ))}
                                            {stats.starred > 0 && <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800/50"><span className="text-yellow-500">\\u2605</span><span className="text-sm font-bold text-yellow-700 dark:text-yellow-300">{stats.starred}</span></div>}
                                        </div>
                                        <div className="flex gap-2">
                                            <button onClick={copyAllPrices} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${copied ? 'bg-emerald-500 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 hover:shadow-md'}`}>{copied ? '\\u2713 Copied' : 'Copy Prices'}</button>
                                            <button onClick={exportToCSV} className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-lg shadow-indigo-500/25 transition-all hover:shadow-xl hover:shadow-indigo-500/30 hover:scale-105">
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                                Export
                                            </button>
                                        </div>
                                    </div>

                                    {/* Results Cards */}
                                    <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1 scrollbar-thin">
                                        {sortedRows.map(r => (
                                            <div key={r.i} className={`glass-card rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl hover:scale-[1.01] border-l-4 ${statusColors[r.status].border} ${statusColors[r.status].bg} ${starred.has(r.i) ? 'ring-2 ring-yellow-400 ring-offset-2 dark:ring-offset-gray-900' : 'border border-gray-100 dark:border-gray-800'}`}>
                                                <div className="p-4 flex items-center gap-4">
                                                    <button onClick={(e) => { e.stopPropagation(); toggleStar(r.i); }} className={`text-2xl transition-all hover:scale-125 ${starred.has(r.i) ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-400'}`}>
                                                        {starred.has(r.i) ? '\\u2605' : '\\u2606'}
                                                    </button>
                                                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center text-sm font-black text-gray-500 shadow-inner">{r.i}</div>
                                                    <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setExpandedRow(expandedRow === r.i ? null : r.i)}>
                                                        {r.sku && <div className="text-xs font-medium text-gray-500 truncate mb-0.5">{r.sku}</div>}
                                                        <div className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">{money(r.sell)}</div>
                                                        {r.pack > 1 && <div className="text-[10px] font-bold text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full inline-block mt-1">Pack of {r.pack}</div>}
                                                    </div>
                                                    <div className="text-right">
                                                        <div className={`text-2xl font-black ${statusColors[r.status].text}`}>{r.marginPct.toFixed(1)}%</div>
                                                        <div className={`text-[10px] font-black uppercase tracking-wide ${statusColors[r.status].text}`}>{statusColors[r.status].label}</div>
                                                    </div>
                                                    <div className="text-right px-4 border-l border-gray-200 dark:border-gray-700">
                                                        <div className="text-[10px] text-gray-400 uppercase font-bold">Profit</div>
                                                        <div className={`text-lg font-black ${statusColors[r.status].text}`}>{money(r.profit)}</div>
                                                    </div>
                                                    <div onClick={() => setExpandedRow(expandedRow === r.i ? null : r.i)} className={`w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-all ${expandedRow === r.i ? 'rotate-180' : ''}`}>
                                                        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                    </div>
                                                </div>
                                                <div className={`overflow-hidden transition-all duration-300 ${expandedRow === r.i ? 'max-h-44 opacity-100' : 'max-h-0 opacity-0'}`}>
                                                    <div className="px-5 pb-5 pt-3 border-t border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/30 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Buy (USD)</span><span className="font-black text-gray-900 dark:text-white">${r.unitUSD.toFixed(2)}</span></div>
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Landed</span><span className="font-black text-gray-900 dark:text-white">{money(r.landedUnit)}</span></div>
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Dims</span><span className="font-black text-gray-900 dark:text-white">{r.dims}cm</span></div>
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Courier</span><span className="font-black text-gray-900 dark:text-white">{r.courier ? r.courier.carrier : '\\u2014'}</span></div>
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Units/40HQ</span><span className="font-black text-gray-900 dark:text-white">{r.units.toLocaleString()}</span></div>
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Cartons</span><span className="font-black text-gray-900 dark:text-white">{r.cartons.toLocaleString()}</span></div>
                                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">CBM</span><span className="font-black text-gray-900 dark:text-white">{r.vol.toFixed(3)}</span></div>
                                                        {r.courier && <div className="bg-white dark:bg-gray-900 rounded-xl p-3 shadow-sm"><span className="text-gray-400 block text-[10px] uppercase font-bold mb-1">Ship Cost</span><span className="font-black text-gray-900 dark:text-white">{money(r.courier.cost)}</span></div>}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            ) : (
                                /* PREMIUM EMPTY STATE */
                                <div className="relative glass-card rounded-3xl p-12 text-center overflow-hidden border border-gray-100 dark:border-gray-800">
                                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-pink-500/5"></div>
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 bg-gradient-to-b from-indigo-400/10 to-transparent rounded-full blur-3xl"></div>
                                    <div className="relative">
                                        <div className="w-24 h-24 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-indigo-500/30 animate-pulse">
                                            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                        </div>
                                        <h3 className="text-2xl font-black text-gray-800 dark:text-white mb-3">Bulk Price Calculator</h3>
                                        <p className="text-gray-500 dark:text-gray-400 max-w-sm mx-auto mb-6">Paste your product prices and dimensions to instantly calculate target sell prices for all items.</p>
                                        <div className="flex justify-center gap-3">
                                            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-full">
                                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                                <span className="text-xs font-bold text-gray-600 dark:text-gray-300">Margins</span>
                                            </div>
                                            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-full">
                                                <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                                                <span className="text-xs font-bold text-gray-600 dark:text-gray-300">Profits</span>
                                            </div>
                                            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-full">
                                                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                                <span className="text-xs font-bold text-gray-600 dark:text-gray-300">Export</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Mobile Sticky */}
                    {rows.length > 0 && (
                        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-t border-gray-200/50 dark:border-gray-700/50 px-4 py-3 safe-area-bottom">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2"><span className="text-2xl font-black text-gray-900 dark:text-white">{stats.total}</span><span className="text-xs text-gray-500">products</span></div>
                                <div className="text-center">
                                    <div className="text-[10px] text-gray-400 uppercase font-bold">Total Profit</div>
                                    <div className="text-lg font-black text-emerald-600">{money(stats.totalProfit)}</div>
                                </div>
                                <button onClick={exportToCSV} className="px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg">Export</button>
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

with open(file_path, 'wb') as f:
    f.write(content)

print("Premium Bulk Design Complete!")
print("- Hero empty state with gradient background")
print("- Polished input cards with icons and hover effects")
print("- Premium settings bar with shadow effects")
print("- Result cards with gradient status colors")
print("- Expanded breakdown in mini-cards")
print("- Decorative background elements")
print("- Micro-animations throughout")
