/**
 * Test what the AI is actually returning
 */

async function testAIResponse() {
  try {
    console.log("Testing AI response directly...");
    
    // Simple test data
    const testData = {
      rows: [
        ["ITEM NO.", "DESCRIPTION", "SIZE", "PACK", "WEIGHT", "CBM", "FOB USD"],
        ["ABC001", "Test Product 1", "20x15x10cm", "12PC", "2.5kg", "0.003", "10.50"],
        ["DEF002", "Test Product 2", "25x20x15cm", "6PC", "3.2kg", "0.0075", "15.75"]
      ],
      preview: true
    };
    
    console.log("Sending request...");
    
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
      console.log("✅ Success! AI is working properly now.");
      console.log("Mapping keys:", Object.keys(data.mapping || {}));
      
      // Check if all required fields are present
      const requiredFields = ["sku", "price", "dims_text", "totalCartons", "netWeight"];
      const missingFields = requiredFields.filter(field => !data.mapping[field]);
      
      if (missingFields.length === 0) {
        console.log("✅ All required fields are present - normalizeMapping is working!");
      } else {
        console.log("❌ Missing fields:", missingFields);
      }
      
    } else {
      const errorText = await response.text();
      console.error("❌ Error:", response.status);
      console.error("Error details:", errorText);
      
      // Try to parse error details
      try {
        const errorJson = JSON.parse(errorText);
        if (errorJson.error) {
          console.error("Specific error:", errorJson.error);
        }
      } catch (e) {
        // Not JSON
      }
    }
    
  } catch (error) {
    console.error("❌ Request failed:", error.message);
  }
}

testAIResponse();