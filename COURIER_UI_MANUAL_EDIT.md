# MANUAL COURIER UI UPDATE

**Location:** Line 1145-1160 in `index.html`

**Current code (REPLACE THIS):**
```jsx
<h3 className="font-bold text-lg mb-4">Courier / Shipping Parameters</h3>
<div className="space-y-4">
    {courierRules.map((r, i) => (
        <div key={r.id} className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2 font-bold text-sm">
                {r.logo && <img src={r.logo} className="h-4 object-contain" />}
                {r.name}
            </div>
            <div className="grid grid-cols-3 gap-2">
                <div><label className="text-[10px] uppercase text-gray-500 font-bold">Max Kg</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.maxWeight || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxWeight: val } : pr)); }} /></div>
                <div><label className="text-[10px] uppercase text-gray-500 font-bold">Max L</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.maxL || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxL: val } : pr)); }} /></div>
                <div><label className="text-[10px] uppercase text-gray-500 font-bold">Price £</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.price || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, price: val } : pr)); }} /></div>
            </div>
        </div>
    ))}
</div>
```

**NEW code (USE THIS):**
See attached file: `courier_ui_replacement.txt`

I've created a separate file with the exact replacement code.
