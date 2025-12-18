/**
 * Minimal test to isolate the issue
 */
const admin = require("firebase-admin");

// Initialize admin
admin.initializeApp();

async function testMinimal() {
  try {
    console.log("Testing minimal function...");
    
    // Test 1: Check if admin works
    const token = await admin.credential.applicationDefault().getAccessToken();
    console.log("✅ Admin token acquired");
    
    // Test 2: Check if the schema is valid
    const MAPPING_FIELDS = [
      "sku", "price", "productLength", "productWidth", "productHeight",
      "cartonLength", "cartonWidth", "cartonHeight", "dims_text", "pack",
      "totalCartons", "grossWeight", "netWeight", "supplierCBM"
    ];

    const RESPONSE_SCHEMA = {
      type: "OBJECT",
      additionalProperties: false,
      required: ["headerRow", "mapping", "confidence", "notes"],
      properties: {
        headerRow: { type: "INTEGER" },
        mapping: {
          type: "OBJECT",
          additionalProperties: false,
          required: MAPPING_FIELDS,
          properties: Object.fromEntries(
            MAPPING_FIELDS.map((k) => [k, {
              type: "OBJECT",
              additionalProperties: false,
              required: ["col", "name", "unit"],
              properties: {
                col: { type: "INTEGER", nullable: true },
                name: { type: "STRING", nullable: true },
                unit: { type: "STRING", nullable: true },
              },
            }])
          ),
        },
        confidence: { type: "NUMBER", nullable: true },
        notes: { type: "STRING", nullable: true },
      },
    };
    
    console.log("✅ Schema created successfully");
    console.log("Schema keys:", Object.keys(RESPONSE_SCHEMA.properties.mapping.properties));
    
    // Test 3: Try a simple API call
    const projectId = "landed-calculator";
    const location = "us-central1";
    const modelId = "gemini-2.5-flash";
    const apiEndpoint = `https://${location}-aiplatform.googleapis.com/v1beta1/projects/${projectId}/locations/${location}/publishers/google/models/${modelId}:generateContent`;
    
    console.log("API Endpoint:", apiEndpoint);
    
    const requestBody = {
      contents: [{
        role: "user",
        parts: [{ text: "Return a simple JSON object: {\"test\": \"hello\"}" }]
      }],
      generationConfig: {
        temperature: 0.1,
        maxOutputTokens: 100
      }
    };
    
    const response = await fetch(apiEndpoint, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token.access_token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestBody)
    });
    
    console.log("Response status:", response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ API call successful");
      console.log("Response:", JSON.stringify(data, null, 2));
    } else {
      const errorText = await response.text();
      console.error("❌ API call failed:", response.status, errorText);
    }
    
  } catch (error) {
    console.error("❌ Test failed:", error.message);
    console.error(error.stack);
  }
}

testMinimal();