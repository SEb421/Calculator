/**
 * Simple debug test - just check if the function loads without errors
 */

console.log("=== SIMPLE DEBUG TEST ===");

try {
  console.log("1. Testing basic requires...");
  
  const { onRequest } = require("firebase-functions/v2/https");
  console.log("✅ firebase-functions/v2/https loaded");
  
  const admin = require("firebase-admin");
  console.log("✅ firebase-admin loaded");
  
  const XLSX = require("xlsx");
  console.log("✅ xlsx loaded");
  
  console.log("2. Testing admin initialization...");
  admin.initializeApp();
  console.log("✅ admin initialized");
  
  console.log("3. Testing schema creation...");
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
  console.log("Schema has", Object.keys(RESPONSE_SCHEMA.properties.mapping.properties).length, "mapping fields");
  
  console.log("4. Testing function creation...");
  const testFunction = onRequest({ cors: true }, (req, res) => {
    res.json({ status: "ok", test: true });
  });
  console.log("✅ Function created successfully");
  
  console.log("=== ALL TESTS PASSED ===");
  
} catch (error) {
  console.error("❌ ERROR:", error.message);
  console.error("Stack:", error.stack);
  process.exit(1);
}