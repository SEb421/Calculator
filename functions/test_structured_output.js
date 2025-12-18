/**
 * Test script to verify structured output works
 */
const admin = require("firebase-admin");

// Initialize admin
admin.initializeApp();

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
        MAPPING_FIELDS.map((k) => [k, { "$ref": "#/definitions/FieldMapping" }])
      ),
    },
    confidence: { type: "NUMBER", nullable: true },
    notes: { type: "STRING", nullable: true },
  },
  definitions: {
    FieldMapping: {
      type: "OBJECT",
      additionalProperties: false,
      required: ["col", "name", "unit"],
      properties: {
        col: { type: "INTEGER", nullable: true },
        name: { type: "STRING", nullable: true },
        unit: { type: "STRING", nullable: true },
      },
    },
  },
};

async function testStructuredOutput() {
  try {
    console.log("Testing structured output with Gemini 2.5 Flash...");
    
    const token = await admin.credential.applicationDefault().getAccessToken();
    const accessToken = token.access_token;

    const projectId = "landed-calculator";
    const location = "us-central1";
    const modelId = "gemini-2.5-flash";
    const apiEndpoint = `https://${location}-aiplatform.googleapis.com/v1beta1/projects/${projectId}/locations/${location}/publishers/google/models/${modelId}:generateContent`;

    const testPrompt = `Analyze this simple spreadsheet data:
Row 0: Item | Price | Size | Carton | Pack | Weight
Row 1: ABC123 | 10.50 | 20x15x10mm | 25x20x15cm | 12PC | 2.5kg

Return the mapping in the required JSON format.`;

    const requestBody = {
      contents: [{
        role: "user",
        parts: [{ text: testPrompt }]
      }],
      generationConfig: {
        responseMimeType: "application/json",
        responseSchema: RESPONSE_SCHEMA,
        temperature: 0.2,
        topP: 0.8,
        maxOutputTokens: 2048
      }
    };

    console.log("Sending request to:", apiEndpoint);
    
    const response = await fetch(apiEndpoint, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${accessToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    const responseJson = await response.json();
    
    if (responseJson.candidates && responseJson.candidates[0]) {
      const responseText = responseJson.candidates[0].content.parts[0].text;
      console.log("Raw response:", responseText);
      
      // Try to parse as JSON
      const parsed = JSON.parse(responseText);
      console.log("✅ Successfully parsed structured JSON:");
      console.log(JSON.stringify(parsed, null, 2));
    } else {
      console.error("❌ No candidates in response:", responseJson);
    }

  } catch (error) {
    console.error("❌ Test failed:", error.message);
    console.error(error.stack);
  }
}

// Run the test
testStructuredOutput();