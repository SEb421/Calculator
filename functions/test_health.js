/**
 * Test the health endpoint
 */
const fetch = require('node-fetch');

async function testHealth() {
  try {
    console.log("Testing health endpoint...");
    
    const response = await fetch('https://analyzequotesheetv2-f3lqrbycya-uc.a.run.app/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log("Health status:", response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ Health check passed:", data);
    } else {
      const errorText = await response.text();
      console.error("❌ Health check failed:", response.status, errorText);
    }
    
  } catch (error) {
    console.error("❌ Health test failed:", error.message);
  }
}

testHealth();