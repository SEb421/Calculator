/**
 * Test with larger data that might cause the JSON truncation issue
 */

async function testLargeData() {
  try {
    console.log("Testing with larger dataset...");
    
    // Create a larger dataset similar to what was in the logs (53 rows, 14 columns)
    const headers = ["ITEM NO.", "DESCRIPTION", "SIZE", "PACK", "WEIGHT", "CBM", "FOB USD", "COL8", "COL9", "COL10", "COL11", "COL12", "COL13", "COL14"];
    const rows = [headers];
    
    // Add 52 data rows to match the "53 rows" from the logs
    for (let i = 1; i <= 52; i++) {
      rows.push([
        `ITEM${i.toString().padStart(3, '0')}`,
        `Product Description ${i}`,
        `${20+i}x${15+i}x${10+i}cm`,
        `${Math.floor(Math.random() * 20) + 1}PC`,
        `${(Math.random() * 5 + 1).toFixed(1)}kg`,
        `${(Math.random() * 0.01).toFixed(4)}`,
        `${(Math.random() * 50 + 10).toFixed(2)}`,
        `Data${i}`, `Data${i}`, `Data${i}`, `Data${i}`, `Data${i}`, `Data${i}`, `Data${i}`
      ]);
    }
    
    const testData = {
      rows: rows,
      preview: false  // Test full extraction like the error logs
    };
    
    console.log(`Testing with ${rows.length} rows, ${headers.length} columns...`);
    
    const response = await fetch('https://analyzequotesheetv2-f3lqrbycya-uc.a.run.app/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testData)
    });
    
    console.log("Response status:", response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ Large dataset test successful!");
      console.log("Products extracted:", data.products?.length || 0);
      console.log("Mapping has all fields:", Object.keys(data.mapping || {}).length);
    } else {
      const errorText = await response.text();
      console.error("❌ Large dataset test failed:", response.status);
      console.error("Error details:", errorText);
      
      try {
        const errorJson = JSON.parse(errorText);
        console.error("Parsed error:", errorJson.error);
        if (errorJson.error.includes("malformed JSON")) {
          console.error("🔍 This is the same JSON parsing error from the logs!");
        }
      } catch (e) {
        console.error("Raw error:", errorText);
      }
    }
    
  } catch (error) {
    console.error("❌ Request failed:", error.message);
  }
}

testLargeData();