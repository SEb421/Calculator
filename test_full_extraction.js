/**
 * Test the full extraction (preview: false) to find the 500 error
 */

async function testFullExtraction() {
  try {
    console.log("Testing full extraction (preview: false)...");
    
    // Test with the same data but preview: false
    const testData = {
      rows: [
        ["Item", "Price", "Size", "Pack", "Weight"],
        ["ABC123", "10.50", "20x15x10mm", "12PC", "2.5kg"],
        ["DEF456", "15.75", "25x20x15mm", "6PC", "3.2kg"],
        ["GHI789", "8.25", "15x10x8mm", "24PC", "1.8kg"]
      ],
      preview: false  // This is the key difference
    };
    
    console.log("Sending full extraction request...");
    
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
      console.log("✅ Full extraction success!");
      console.log("Products found:", data.products?.length || 0);
      console.log("First product:", JSON.stringify(data.products?.[0], null, 2));
    } else {
      const errorText = await response.text();
      console.error("❌ Full extraction failed:", response.status);
      console.error("Error response:", errorText);
      
      // Try to parse error details
      try {
        const errorJson = JSON.parse(errorText);
        console.error("Parsed error:", errorJson);
        if (errorJson.details) {
          console.error("Stack trace:", errorJson.details);
        }
      } catch (e) {
        console.error("Raw error (not JSON):", errorText);
      }
    }
    
  } catch (error) {
    console.error("❌ Request failed:", error.message);
  }
}

testFullExtraction();