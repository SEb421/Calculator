
import os

file_path = "C:\\Users\\shuli\\Downloads\\Calculator\\index.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """<div className="grid grid-cols-3 gap-2">
                                                            <div><label className="text-[10px] uppercase text-gray-500 font-bold">Max Kg</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.maxWeight || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxWeight: val } : pr)); }} /></div>
                                                            <div><label className="text-[10px] uppercase text-gray-500 font-bold">Max L</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.maxL || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxL: val } : pr)); }} /></div>
                                                            <div><label className="text-[10px] uppercase text-gray-500 font-bold">Price £</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.price || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, price: val } : pr)); }} /></div>
                                                        </div>"""

replacement_block = """<div className="grid gap-2" style={{gridTemplateColumns: `repeat(${3 + (r.additionalPrice && r.additionalPrice !== r.price ? 1 : 0) + (r.surcharge25kg ? 1 : 0)}, minmax(0, 1fr))`}}>
                                                            <div><label className="text-[10px] uppercase text-gray-500 font-bold">Max Kg</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.maxWeight || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxWeight: val } : pr)); }} /></div>
                                                            <div><label className="text-[10px] uppercase text-gray-500 font-bold">Max L</label><input className="glass-input w-full px-2 py-1 text-xs rounded" type="number" value={r.maxL || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, maxL: val } : pr)); }} /></div>
                                                            <div><label className="text-[10px] uppercase text-gray-500 font-bold">1st £</label><input className="glass-input w-full px-2 py-1 text-xs rounded tabular-nums" type="number" step="0.01" value={r.price || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, price: val } : pr)); }} /></div>
                                                            {r.additionalPrice && r.additionalPrice !== r.price && <div><label className="text-[10px] uppercase text-gray-500 font-bold">Add £</label><input className="glass-input w-full px-2 py-1 text-xs rounded tabular-nums" type="number" step="0.01" value={r.additionalPrice || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, additionalPrice: val } : pr)); }} /></div>}
                                                            {r.surcharge25kg > 0 && <div><label className="text-[10px] uppercase text-gray-500 font-bold">25kg+ £</label><input className="glass-input w-full px-2 py-1 text-xs rounded tabular-nums" type="number" step="0.01" value={r.surcharge25kg || ''} onChange={(e) => { const val = parseFloat(e.target.value); setCourierRules(prev => prev.map((pr, pi) => pi === i ? { ...pr, surcharge25kg: val } : pr)); }} /></div>}
                                                        </div>"""

if target_block in content:
    new_content = content.replace(target_block, replacement_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Content replaced successfully.")
else:
    print("ERROR: Target block not found. Checking indentation...")
    # Attempt with normalized whitespace
    import re
    norm_target = re.sub(r'\s+', ' ', target_block).strip()
    norm_content = re.sub(r'\s+', ' ', content)
    if norm_target in norm_content:
         print("Found via regex normalization (whitespace issue). Trying fuzzy match replacement.")
         # Not doing fuzzy replace automatically to be safe, stick to strict string replace first.
         print("Please adjust script to exact whitespace match.")
    else:
        print("Target block really not found.")

