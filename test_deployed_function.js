/**
 * Test the deployed function to see the actual error
 */

async function testDeployedFunction() {
  try {
    console.log("Testing deployed function...");
    
    // Test with minimal data
    const testData = {
      rows: [
        ["Item", "Price", "Size"],
        ["ABC123", "10.50", "20x15x10mm"]
      ],
      preview: true
    };
    
    console.log("Sending request to deployed function...");
    
    const response = await fetch('https://analyzequotesheetv2-f3lqrbycya-uc.a.run.app/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testData)
    });
    
    console.log("Response status:", response.status);
    console.log("Response headers:", Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ Success:", JSON.stringify(data, null, 2));
    } else {
      const errorText = await response.text();
      console.error("❌ Error response:", errorText);
      
      // Try to parse as JSON
      try {
        const errorJson = JSON.parse(errorText);
        console.error("Error details:", errorJson);
      } catch (e) {
        console.error("Raw error text:", errorText);
      }
    }
    
  } catch (error) {
    console.error("❌ Request failed:", error.message);
  }
}

testDeployedFunction();