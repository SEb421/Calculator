const fetch = require('node-fetch');
const XLSX = require('xlsx');

async function testChaos() {
    const url = 'https://analyzequotesheet-f3lqrbycya-uc.a.run.app';

    // BRUTAL TEST - Real messy data
    const data = [
        ["SUPPLIER QUOTE", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["ITEM NO", "DESCRIPTION", "SIZE", "", "MATERIAL", "PACKING", "FOB USD", "PORT", "CARTON SIZE", "CBM", "G.W"],
        ["", "", "", "", "", "", "", "", "(cm)", "", ""],
        ["EQ2402-025-S", "RIKJA 3-DOOR WARDROBE", "119.9X50X180CM", "", "PARTICLE BOARD", "1PC/3 BROWN CARTON", "$89.67", "XIAMEN", "CARTON: A:56X10X127CM B:48CM 90X104CM 27KGS", "0.320", "85"],
        ["FT2503-02", "DRESSING TABLE", "900x450x1600mm", "", "VENEER", "1PC/BROWN CARTON", "$17.60", "XIAMEN", "53  15.6  82", "0.029", "23"]
    ];

    const ws = XLSX.utils.aoa_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Quote");
    const buffer = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
    const base64 = buffer.toString('base64');

    console.log('🔥 CHAOS TEST - Testing with messy real-world data\n');

    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ xlsxBase64: base64, preview: false })
    });

    if (!res.ok) {
        console.log(`❌ Error ${res.status}: ${await res.text()}`);
        return;
    }

    const result = await res.json();

    if (!result.success || !result.products) {
        console.log('❌ AI extraction failed:', result.error || 'Unknown error');
        console.log('Full response:', JSON.stringify(result, null, 2));
        return;
    }

    console.log('\nRESULTS:');
    result.products.forEach((p, i) => {
        console.log(`\n${i + 1}. ${p.sku}:`);
        console.log(`   Product Dims: ${p.productLength || 0}×${p.productWidth || 0}×${p.productHeight || 0} (${p.productSource || 'N/A'})`);
        console.log(`   Carton Dims:  ${p.cartonLength || 0}×${p.cartonWidth || 0}×${p.cartonHeight || 0} (${p.cartonSource || 'N/A'})`);
        console.log(`   Pack: ${p.pack} ("${p.pack_text}")`);

        if (p.cartonLength === 0) console.log('   ❌ NO CARTON DIMS!');
        if (p.pack !== 1 && p.pack_text.includes('1PC')) console.log(`   ❌ Pack=${p.pack} but text says 1PC!`);
    });
}

testChaos().catch(console.error);
