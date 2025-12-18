/**
 * Debug the AI mapping to see what's missing
 */

async function testMappingDebug() {
  try {
    console.log("Testing AI mapping structure...");
    
    const testData = {
      rows: [
        ["Item", "Price", "Size", "Pack", "Weight"],
        ["ABC123", "10.50", "20x15x10mm", "12PC", "2.5kg"]
      ],
      preview: true  // Get the mapping first
    };
    
    const response = await fetch('https://analyzequotesheetv2-f3lqrbycya-uc.a.run.app/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testData)
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ Preview success");
      console.log("Full mapping structure:");
      console.log(JSON.stringify(data.mapping, null, 2));
      
      // Check which fields are missing
      const requiredFields = [
        "sku", "price", "productLength", "productWidth", "productHeight",
        "cartonLength", "cartonWidth", "cartonHeight", "dims_text", "pack",
        "totalCartons", "grossWeight", "netWeight", "supplierCBM"
      ];
      
      console.log("\nField analysis:");
      requiredFields.forEach(field => {
        const fieldData = data.mapping[field];
        if (fieldData === undefined) {
          console.log(`❌ ${field}: COMPLETELY MISSING`);
        } else if (fieldData === null) {
          console.log(`⚠️  ${field}: null`);
        } else if (fieldData.col === undefined) {
          console.log(`❌ ${field}.col: MISSING (field exists but no col property)`);
        } else {
          console.log(`✅ ${field}: col=${fieldData.col}, name="${fieldData.name}"`);
        }
      });
      
    } else {
      console.error("❌ Preview failed:", response.status);
    }
    
  } catch (error) {
    console.error("❌ Test failed:", error.message);
  }
}

testMappingDebug();