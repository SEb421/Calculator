# Enhanced Shipping Logic Implementation
# 1. Update courier rules with delivery estimates
# 2. Modify chooseCourier to return all options
# 3. Add CourierCard component to Simple view

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

LINE_END = b'\r\n'

with open(file_path, 'rb') as f:
    content = f.read()

# ===== 1. UPDATE COURIER RULES WITH DELIVERY ESTIMATES =====
old_rules = b'''const DEFAULT_COURIER_RULES = [
            { id: 'evri_packet', name: 'Evri / Packet', maxL: 120, maxGirth: 225, maxWeight: 2, maxVol: 40, price: 1.85, logo: 'Logos/evri_logo_png.png' },
            { id: 'evri_packet_large', name: 'Evri / Packet over 40L', maxL: 120, maxGirth: 225, maxWeight: 2, minVol: 40, price: 2.25, logo: 'Logos/evri_logo_png.png' },
            { id: 'evri_parcel', name: 'Evri / Parcel', maxL: 120, maxGirth: 225, maxWeight: 15, price: 2.33, logo: 'Logos/evri_logo_png.png' },
            { id: 'yodel_express', name: 'Yodel / Express', maxL: 90, maxVolCm3: 110000, maxWeight: 17, price: 2.30, logo: 'Logos/Yodel_logo.png' },
            { id: 'dpd_48', name: 'DPD / 48 Hour', maxL: 120, maxW: 70, maxH: 60, maxWeight: 30, price: 4.51, logo: 'Logos/DPD_logo(red)2015.png' },
            { id: 'pf_48', name: 'Parcelforce / 48 Hour', maxL: 150, maxGirth: 300, maxWeight: 30, price: 5.40, extraPerParcel: 2.70, type: 'multi', logo: 'Logos/Parcel Force Logo.png' },
            { id: 'evri_ll', name: 'Evri / L&L', maxL: 180, maxGirth: 380, maxWeight: 30, price: 8.00, logo: 'Logos/evri_logo_png.png' },
            { id: 'dx_std', name: 'DX / Standard', maxL: 150, maxWeight: 30, price: 5.40, extraPerParcel: 3.30, type: 'dx_std', logo: 'Logos/DX Standard Lengths.png' },
            { id: 'dx_len', name: 'DX / Lengths', maxL: 200, maxWeight: 30, price: 12.21, type: 'dx_len', logo: 'Logos/DX Standard Lengths.png' }
        ];'''

new_rules = b'''const DEFAULT_COURIER_RULES = [
            { id: 'evri_packet', name: 'Evri / Packet', maxL: 120, maxGirth: 225, maxWeight: 2, maxVol: 40, price: 1.85, days: '2-3', logo: 'Logos/evri_logo_png.png' },
            { id: 'evri_packet_large', name: 'Evri / Packet over 40L', maxL: 120, maxGirth: 225, maxWeight: 2, minVol: 40, price: 2.25, days: '2-3', logo: 'Logos/evri_logo_png.png' },
            { id: 'evri_parcel', name: 'Evri / Parcel', maxL: 120, maxGirth: 225, maxWeight: 15, price: 2.33, days: '2-3', logo: 'Logos/evri_logo_png.png' },
            { id: 'yodel_express', name: 'Yodel / Express', maxL: 90, maxVolCm3: 110000, maxWeight: 17, price: 2.30, days: '1-2', logo: 'Logos/Yodel_logo.png' },
            { id: 'dpd_48', name: 'DPD / 48 Hour', maxL: 120, maxW: 70, maxH: 60, maxWeight: 30, price: 4.51, days: '1-2', logo: 'Logos/DPD_logo(red)2015.png' },
            { id: 'pf_48', name: 'Parcelforce / 48 Hour', maxL: 150, maxGirth: 300, maxWeight: 30, price: 5.40, extraPerParcel: 2.70, type: 'multi', days: '1-2', logo: 'Logos/Parcel Force Logo.png' },
            { id: 'evri_ll', name: 'Evri / L&L', maxL: 180, maxGirth: 380, maxWeight: 30, price: 8.00, days: '3-5', logo: 'Logos/evri_logo_png.png' },
            { id: 'dx_std', name: 'DX / Standard', maxL: 150, maxWeight: 30, price: 5.40, extraPerParcel: 3.30, type: 'dx_std', days: '2-3', logo: 'Logos/DX Standard Lengths.png' },
            { id: 'dx_len', name: 'DX / Lengths', maxL: 200, maxWeight: 30, price: 12.21, type: 'dx_len', days: '2-3', logo: 'Logos/DX Standard Lengths.png' }
        ];'''

if old_rules in content:
    content = content.replace(old_rules, new_rules)
    print("1. Updated courier rules with delivery estimates")
else:
    print("1. WARN: Could not find courier rules to update")

# ===== 2. UPDATE chooseCourier TO RETURN ALL OPTIONS =====
old_choose = b'''function chooseCourier(l, w, h, weightKg, rules = DEFAULT_COURIER_RULES) {
            const L = Math.max(0, l | 0), W = Math.max(0, w | 0), H = Math.max(0, h | 0);
            const weight = Math.max(0, Number(weightKg || 0));
            const volumeCm3 = L * W * H;
            const volumeL = volumeCm3 / 1000;
            const girth = L + 2 * (W + H);
            const volKg = volumeCm3 / VOL_DIVISOR;

            const fits = [];
            for (const r of rules) {
                let ok = true;
                if (r.maxL && L > r.maxL) ok = false;
                if (r.maxW && W > r.maxW) ok = false;
                if (r.maxH && H > r.maxH) ok = false;
                if (r.maxGirth && girth > r.maxGirth) ok = false;
                if (r.maxWeight && weight > r.maxWeight) ok = false;
                if (r.maxVol && volumeL > r.maxVol) ok = false;
                if (r.minVol && volumeL <= r.minVol) ok = false;
                if (r.maxVolCm3 && volumeCm3 > r.maxVolCm3) ok = false;

                if (ok) {
                    let cost = r.price;
                    let parcels = 1;

                    if (r.type === 'multi') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, 0) / 30));
                        cost = r.price + Math.max(0, parcels - 1) * (r.extraPerParcel || 0);
                    } else if (r.type === 'dx_std') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, volKg) / 30));
                        const surcharge = (weight > DX_SURCHARGE_THRESHOLD || volKg > DX_SURCHARGE_THRESHOLD) ? 1.75 * parcels : 0;
                        cost = r.price + (parcels - 1) * (r.extraPerParcel || 0) + surcharge;
                    } else if (r.type === 'dx_len') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, volKg) / 30));
                        cost = r.price * parcels;
                    }

                    fits.push({
                        carrier: r.name.split('/')[0].trim(),
                        service: r.name.split('/')[1].trim(),
                        cost: cost,
                        parcels: parcels,
                        logo: r.logo,
                        id: r.id
                    });
                }
            }
            if (fits.length === 0) return null;
            fits.sort((a, b) => a.cost - b.cost);
            return fits[0];
        }'''

new_choose = b'''function chooseCourier(l, w, h, weightKg, rules = DEFAULT_COURIER_RULES) {
            const L = Math.max(0, l | 0), W = Math.max(0, w | 0), H = Math.max(0, h | 0);
            const weight = Math.max(0, Number(weightKg || 0));
            const volumeCm3 = L * W * H;
            const volumeL = volumeCm3 / 1000;
            const girth = L + 2 * (W + H);
            const volKg = volumeCm3 / VOL_DIVISOR;

            const fits = [];
            for (const r of rules) {
                let ok = true;
                let reasons = [];
                if (r.maxL && L > r.maxL) ok = false;
                if (r.maxW && W > r.maxW) ok = false;
                if (r.maxH && H > r.maxH) ok = false;
                if (r.maxGirth && girth > r.maxGirth) ok = false;
                if (r.maxWeight && weight > r.maxWeight) ok = false;
                if (r.maxVol && volumeL > r.maxVol) ok = false;
                if (r.minVol && volumeL <= r.minVol) ok = false;
                if (r.maxVolCm3 && volumeCm3 > r.maxVolCm3) ok = false;

                if (ok) {
                    if (r.maxWeight && weight <= r.maxWeight) reasons.push(`Under ${r.maxWeight}kg`);
                    if (r.maxVol && volumeL <= r.maxVol) reasons.push(`Under ${r.maxVol}L`);
                    if (r.maxL && L <= r.maxL) reasons.push(`Fits ${r.maxL}cm max`);

                    let cost = r.price;
                    let parcels = 1;

                    if (r.type === 'multi') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, 0) / 30));
                        cost = r.price + Math.max(0, parcels - 1) * (r.extraPerParcel || 0);
                    } else if (r.type === 'dx_std') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, volKg) / 30));
                        const surcharge = (weight > DX_SURCHARGE_THRESHOLD || volKg > DX_SURCHARGE_THRESHOLD) ? 1.75 * parcels : 0;
                        cost = r.price + (parcels - 1) * (r.extraPerParcel || 0) + surcharge;
                    } else if (r.type === 'dx_len') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, volKg) / 30));
                        cost = r.price * parcels;
                    }

                    fits.push({
                        carrier: r.name.split('/')[0].trim(),
                        service: r.name.split('/')[1].trim(),
                        cost: cost,
                        parcels: parcels,
                        logo: r.logo,
                        id: r.id,
                        days: r.days || '2-3',
                        reason: reasons.slice(0, 2).join(', ')
                    });
                }
            }
            if (fits.length === 0) return null;
            fits.sort((a, b) => a.cost - b.cost);
            return fits[0];
        }

        function getAllCouriers(l, w, h, weightKg, rules = DEFAULT_COURIER_RULES) {
            const L = Math.max(0, l | 0), W = Math.max(0, w | 0), H = Math.max(0, h | 0);
            const weight = Math.max(0, Number(weightKg || 0));
            const volumeCm3 = L * W * H;
            const volumeL = volumeCm3 / 1000;
            const girth = L + 2 * (W + H);
            const volKg = volumeCm3 / VOL_DIVISOR;

            const fits = [];
            for (const r of rules) {
                let ok = true;
                let reasons = [];
                if (r.maxL && L > r.maxL) ok = false;
                if (r.maxW && W > r.maxW) ok = false;
                if (r.maxH && H > r.maxH) ok = false;
                if (r.maxGirth && girth > r.maxGirth) ok = false;
                if (r.maxWeight && weight > r.maxWeight) ok = false;
                if (r.maxVol && volumeL > r.maxVol) ok = false;
                if (r.minVol && volumeL <= r.minVol) ok = false;
                if (r.maxVolCm3 && volumeCm3 > r.maxVolCm3) ok = false;

                if (ok) {
                    if (r.maxWeight && weight <= r.maxWeight) reasons.push(`Under ${r.maxWeight}kg`);
                    if (r.maxVol && volumeL <= r.maxVol) reasons.push(`Under ${r.maxVol}L`);
                    if (r.maxL && L <= r.maxL) reasons.push(`Fits ${r.maxL}cm max`);

                    let cost = r.price;
                    let parcels = 1;

                    if (r.type === 'multi') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, 0) / 30));
                        cost = r.price + Math.max(0, parcels - 1) * (r.extraPerParcel || 0);
                    } else if (r.type === 'dx_std') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, volKg) / 30));
                        const surcharge = (weight > DX_SURCHARGE_THRESHOLD || volKg > DX_SURCHARGE_THRESHOLD) ? 1.75 * parcels : 0;
                        cost = r.price + (parcels - 1) * (r.extraPerParcel || 0) + surcharge;
                    } else if (r.type === 'dx_len') {
                        parcels = Math.max(1, Math.ceil(Math.max(weight, volKg) / 30));
                        cost = r.price * parcels;
                    }

                    fits.push({
                        carrier: r.name.split('/')[0].trim(),
                        service: r.name.split('/')[1].trim(),
                        cost: cost,
                        parcels: parcels,
                        logo: r.logo,
                        id: r.id,
                        days: r.days || '2-3',
                        reason: reasons.slice(0, 2).join(', ')
                    });
                }
            }
            fits.sort((a, b) => a.cost - b.cost);
            return fits;
        }'''

if old_choose in content:
    content = content.replace(old_choose, new_choose)
    print("2. Updated chooseCourier and added getAllCouriers function")
else:
    print("2. WARN: Could not find chooseCourier function to update")

# ===== 3. ADD COURIER CARD COMPONENT =====
# Find a good insertion point after the Icons object
icons_end = content.find(b"Reset: () =>")
if icons_end != -1:
    # Find the end of Icons object
    icons_obj_end = content.find(b"};", icons_end)
    if icons_obj_end != -1:
        insert_point = icons_obj_end + 2
        
        courier_card = b'''

        function CourierCard({ courier, allCouriers, showAlternatives = true }) {
            const [expanded, setExpanded] = useState(false);
            const money = (n) => `\\u00a3${Number(n || 0).toFixed(2)}`;
            
            if (!courier) return (
                <div className="glass-card rounded-2xl p-4 border-l-4 border-l-gray-300">
                    <div className="text-sm text-gray-500">Enter dimensions to see shipping options</div>
                </div>
            );

            const alternatives = allCouriers?.slice(1, 4) || [];

            return (
                <div className="glass-card rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-800 hover:shadow-lg transition-all">
                    {/* Main Recommendation */}
                    <div className="p-4 bg-gradient-to-r from-emerald-50/50 to-transparent dark:from-emerald-900/20">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 text-[10px] font-black uppercase tracking-wide bg-emerald-500 text-white rounded-full">Recommended</span>
                                <span className="text-[10px] font-medium text-gray-400">{courier.days} days</span>
                            </div>
                            {courier.reason && <span className="text-[10px] text-gray-400 italic">{courier.reason}</span>}
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-white dark:bg-gray-800 shadow-sm flex items-center justify-center p-2 overflow-hidden">
                                {courier.logo ? <img src={courier.logo} alt={courier.carrier} className="w-full h-full object-contain" onError={(e) => { e.target.style.display='none'; }} /> : <span className="text-lg font-black text-gray-400">{courier.carrier[0]}</span>}
                            </div>
                            <div className="flex-1">
                                <div className="text-lg font-black text-gray-900 dark:text-white">{courier.carrier}</div>
                                <div className="text-sm text-gray-500">{courier.service}</div>
                            </div>
                            <div className="text-right">
                                <div className="text-2xl font-black text-emerald-600">{money(courier.cost)}</div>
                                {courier.parcels > 1 && <div className="text-[10px] text-gray-400">{courier.parcels} parcels</div>}
                            </div>
                        </div>
                    </div>

                    {/* Alternatives Toggle */}
                    {showAlternatives && alternatives.length > 0 && (
                        <>
                            <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors border-t border-gray-100 dark:border-gray-800">
                                <span className="text-xs font-bold text-gray-500">{alternatives.length} alternative{alternatives.length > 1 ? 's' : ''} available</span>
                                <span className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}>
                                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                </span>
                            </button>
                            <div className={`overflow-hidden transition-all duration-300 ${expanded ? 'max-h-80' : 'max-h-0'}`}>
                                <div className="p-3 space-y-2 bg-gray-50/50 dark:bg-gray-900/30">
                                    {alternatives.map((alt, i) => (
                                        <div key={alt.id || i} className="flex items-center gap-3 p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
                                            <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center p-1.5 overflow-hidden">
                                                {alt.logo ? <img src={alt.logo} alt={alt.carrier} className="w-full h-full object-contain" onError={(e) => { e.target.style.display='none'; }} /> : <span className="text-xs font-bold text-gray-400">{alt.carrier[0]}</span>}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-bold text-gray-700 dark:text-gray-200 truncate">{alt.carrier} / {alt.service}</div>
                                                <div className="text-[10px] text-gray-400">{alt.days} days</div>
                                            </div>
                                            <div className="text-sm font-black text-gray-600 dark:text-gray-300">{money(alt.cost)}</div>
                                            <div className="text-[10px] text-red-400">+{money(alt.cost - courier.cost)}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            );
        }'''

        content = content[:insert_point] + courier_card.replace(b'\n', LINE_END) + content[insert_point:]
        print("3. Added CourierCard component")
else:
    print("3. WARN: Could not find insertion point for CourierCard")

# ===== 4. UPDATE SIMPLE VIEW TO USE COURIER CARD =====
# Find the SimpleView and add allCouriers calculation
simple_courier_old = b'''const courier = useMemo(() => {
                const c1 = chooseCourier(num(s.L), num(s.W), num(s.H), num(s.weightKg), courierRules);'''

simple_courier_new = b'''const allCouriers = useMemo(() => {
                return getAllCouriers(num(s.L), num(s.W), num(s.H), num(s.weightKg), courierRules);
            }, [s.L, s.W, s.H, s.weightKg, courierRules]);

            const courier = useMemo(() => {
                const c1 = chooseCourier(num(s.L), num(s.W), num(s.H), num(s.weightKg), courierRules);'''

if simple_courier_old in content:
    content = content.replace(simple_courier_old, simple_courier_new)
    print("4. Added allCouriers calculation to SimpleView")
else:
    print("4. WARN: Could not find courier calculation in SimpleView")

# ===== 5. ADD COURIER CARD TO BREAKDOWN SECTION =====
breakdown_end = b'''<div className="metric-row flex justify-between items-center py-3 px-4 rounded-xl hover:bg-gray-100/70 dark:hover:bg-gray-700/50 transition-all"><div className="flex items-center gap-3 text-gray-700 dark:text-gray-300"><Icons.Ruler className="text-purple-500" /><span className="text-sm font-medium">Total CBM</span></div><span className="text-sm font-bold text-gray-900 dark:text-white tabular-nums">{fmt(setVol, 3)} m\\u00b3</span></div>
                            </div>
                        </div>
                    </div>'''

breakdown_with_courier = b'''<div className="metric-row flex justify-between items-center py-3 px-4 rounded-xl hover:bg-gray-100/70 dark:hover:bg-gray-700/50 transition-all"><div className="flex items-center gap-3 text-gray-700 dark:text-gray-300"><Icons.Ruler className="text-purple-500" /><span className="text-sm font-medium">Total CBM</span></div><span className="text-sm font-bold text-gray-900 dark:text-white tabular-nums">{fmt(setVol, 3)} m\\u00b3</span></div>
                            </div>
                            {/* Courier Recommendation Card */}
                            <div className="mt-4">
                                <div className="flex items-center gap-3 mb-3"><div className="w-2 h-7 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div><h3 className="text-base font-black uppercase tracking-wide text-gray-800 dark:text-white">Shipping</h3></div>
                                <CourierCard courier={courier} allCouriers={allCouriers} />
                            </div>
                        </div>
                    </div>'''

if breakdown_end in content:
    content = content.replace(breakdown_end, breakdown_with_courier)
    print("5. Added CourierCard to SimpleView breakdown section")
else:
    print("5. WARN: Could not find breakdown section to update")

with open(file_path, 'wb') as f:
    f.write(content)

print("\n=== Enhanced Shipping Logic Complete! ===")
print("- Courier rules now have delivery estimates (days)")
print("- Added getAllCouriers function returning all matching options")
print("- Created premium CourierCard component with:")
print("  * Carrier logo support")
print("  * Recommended badge")
print("  * Delivery estimate")
print("  * Why this courier reason")
print("  * Expandable alternatives section")
