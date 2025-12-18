/**
 * Test full extraction with the correct mapping
 */

async function testFullExtraction() {
    console.log("🔍 Full Extraction Test");
    console.log("=======================");
    
    // Exact data from the Excel file
    const testData = {
        rows: [
            ["IMAGE", "TIEM NO.", "DESCRIPTION", "SIZE", "MATERIAL", "PACKING", "FOB USD", "PORT", "CARTON SIZE", "", "", "CBM", "G.W", "FEST REMARK", ""],
            ["", "EG2402-025-3", "RIGA 3-DOOR 6-DRAWER", "119.9X50X180CM", "12/15MM PARTICLE BOA", "1PC/3 BROWN CARTON", "$89.67 ", "FUZHOU ", "CARTON A:56X10X127CM", "", "", "0.220 ", "85", "YOU HAVE BOUGHT 2 DO", ""],
            ["", "FT2303-169-3", "FUJI 3-Door 4-Drawer", "111X50X179CM", "12/15MM PARTICLE BOA", "1PC/3 BROWN CARTON", "$71.43 ", "FUZHOU ", "CARTON A:53X9.5X120.", "", "", "0.193 ", "82.9", "YOU HAVE BOUGHT 2 DO", ""],
            ["", "FT2503-02", "DRESSING TABLE AND S", "DRESSING TABLE：500x4", "12/15MM PARTICLE BOA", "1SET/BROWN CARTON", "$24.00 ", "FUZHOU ", "53", "18", "82", "0.078 ", "30", "PRICE IS CONFIRMED", ""],
            ["", "FT2503-02 DR", "DRESSING TABLE", "500x450x1500mm", "12/15MM PARTICLE BOA", "1PC/BROWN CARTON", "$17.60 ", "FUZHOU ", "53", "13.5", "82", "0.059 ", "23", "", ""],
            ["", "FT2503-02 ST", "DRESSING STOOL", "400x300x450mm", "15MM PARTICLE BOARD ", "1PC/BROWN CARTON", "$7.32 ", "FUZHOU ", "32", "11", "46.5", "0.016 ", "7.2", "", ""]
        ],
        preview: false  // Full extraction
    };
    
    console.log("📊 Sending full extraction to AI...");
    
    try {
        const response = await fetch('https://analyzequotesheetv2-f3lqrbycya-uc.a.run.app/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log("\n✅ FULL EXTRACTION RESULT:");
            console.log("==========================");
            
            console.log(`📦 Products found: ${result.products?.length || 0}`);
            
            if (result.products && result.products.length > 0) {
                result.products.slice(0, 3).forEach((product, i) => {
                    console.log(`\n🏷️  Product ${i + 1}:`);
                    console.log(`   SKU: "${product.sku || 'MISSING'}"`);
                    console.log(`   Title: "${product.title || 'MISSING'}"`);
                    console.log(`   Price: $${product.unitPrice || 0}`);
                    console.log(`   Product Dims: ${product.productLength || 0}×${product.productWidth || 0}×${product.productHeight || 0}`);
                    console.log(`   Carton Dims: ${product.cartonLength || 0}×${product.cartonWidth || 0}×${product.cartonHeight || 0}`);
                    console.log(`   Pack: ${product.pack || 1} (text: "${product.pack_text || ''}")`);
                    console.log(`   Weight: ${product.grossWeight || 0}kg`);
                    console.log(`   CBM: ${product.supplierCBM || 'N/A'}`);
                    console.log(`   Dims Text: "${product.dims_text || ''}"`);
                });
            }
            
            // Check mapping
            console.log("\n🗺️  MAPPING USED:");
            console.log("=================");
            Object.entries(result.mapping || {}).forEach(([field, mapping]) => {
                if (mapping.col !== null) {
                    console.log(`✅ ${field.padEnd(15)}: Col ${mapping.col} "${mapping.name}"`);
                }
            });
            
        } else {
            console.error("❌ AI Request failed:", response.status);
            const errorText = await response.text();
            console.error("Error:", errorText);
        }
        
    } catch (error) {
        console.error("❌ Test failed:", error.message);
    }
}

testFullExtraction();