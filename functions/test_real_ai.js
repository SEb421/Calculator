const fetch = require('node-fetch');
const XLSX = require('xlsx');

async function testRealAI() {
    const url = 'https://analyzequotesheet-f3lqrbycya-uc.a.run.app';
    console.log(`Target: ${url}`);

    // 1. Create a realistic XLSX with BOTH Product Size and Carton Size
    console.log('Generating test XLSX file...');
    const data = [
        ["Supplier Quote", "", "", "", "", "", "", ""],
        ["Item No", "Product Size", "Carton Size", "Qty/ctn", "Unit Price", "G.W", "CBM", ""],
        ["WD-001", "119x50x180cm", "56x50x127cm", "1PC/3 CTNS", "$89.67", "20kg", "0.35", ""],
        ["WD-002", "111x50x179cm", "55x48x125cm", "1PC", "$71.43", "18kg", "0.33", ""]
    ];

    const ws = XLSX.utils.aoa_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Quote");

    // Write to base64 buffer
    const buffer = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
    const base64 = buffer.toString('base64');
    console.log(`Generated XLSX base64 (${base64.length} chars)`);

    // 2. Send to Cloud Function
    console.log('\nSending to AI for analysis...');
    try {
        const startTime = Date.now();
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                xlsxBase64: base64,
                preview: false // We want full extraction
            })
        });

        const duration = (Date.now() - startTime) / 1000;
        console.log(`Response received in ${duration.toFixed(1)}s`);

        if (!res.ok) {
            console.log(`Error ${res.status}: ${await res.text()}`);
            return;
        }

        const result = await res.json();

        // 3. Display Results
        console.log('\n========================================');
        console.log('DUAL DIMENSION EXTRACTION TEST');
        console.log('========================================');
        console.log(`Success: ${result.success}`);
        console.log(`Confidence: ${result.confidence}`);
        console.log(`Header Row: ${result.originalData.headerRow}`);

        console.log('\n--- EXTRACTED PRODUCTS ---');
        result.products.forEach((p, i) => {
            console.log(`\nProduct ${i + 1}: ${p.sku}`);
            console.log(`  Price: $${p.unitPrice}`);
            console.log(`  PRODUCT Dims: ${p.productLength || 0}x${p.productWidth || 0}x${p.productHeight || 0} cm (Source: ${p.productSource || 'N/A'})`);
            console.log(`  CARTON Dims: ${p.cartonLength || 0}x${p.cartonWidth || 0}x${p.cartonHeight || 0} cm (Source: ${p.cartonSource || 'N/A'})`);
            console.log(`  Pack: ${p.pack} (Text: "${p.pack_text}")`);
            console.log(`  Weight: ${p.grossWeight || 0} kg`);
            console.log(`  Supplier CBM: ${p.supplierCBM || 'N/A'}`);
        });

        console.log('\n--- AI MAPPING ---');
        console.log(JSON.stringify(result.mapping, null, 2));
        console.log('========================================\n');

        // CHECK FOR ISSUES
        const issues = [];
        result.products.forEach((p, i) => {
            if ((p.cartonLength || 0) === 0 && (p.productLength || 0) > 0) {
                issues.push(`Product ${i + 1}: AI extracted product dims but NOT carton dims`);
            }
            if ((p.productLength || 0) > 400 || (p.cartonLength || 0) > 400) {
                issues.push(`Product ${i + 1}: Dimensions >400 detected (likely mm, needs conversion)`);
            }
        });

        if (issues.length > 0) {
            console.log('⚠️  ISSUES DETECTED:');
            issues.forEach(iss => console.log(`  - ${iss}`));
        } else {
            console.log('✅ No obvious issues detected');
        }

    } catch (e) {
        console.error('Test Failed:', e);
    }
}

testRealAI();
