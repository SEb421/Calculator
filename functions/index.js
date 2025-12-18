/**
 * AI-Powered Quote Sheet Analyzer
 * Firebase Cloud Function for Landed Cost Calculator
 * 
 * Analyzes supplier quote spreadsheets using Gemini Pro AI to extract
 * pricing data, dimensions, and product information from varied formats.
 */
exports.monitorAICall = require('./debug_monitor').monitorAICall;

const { onRequest } = require("firebase-functions/v2/https");
const { VertexAI } = require("@google-cloud/vertexai");
const admin = require("firebase-admin");
const XLSX = require("xlsx");

// Initialize admin if not already done
if (!admin.apps.length) {
  admin.initializeApp();
}

// JSON Schema for structured output
const MAPPING_FIELDS = [
  "sku", "price", "productLength", "productWidth", "productHeight",
  "cartonLength", "cartonWidth", "cartonHeight", "dims_text", "pack",
  "totalCartons", "grossWeight", "netWeight", "supplierCBM"
];

const RESPONSE_SCHEMA = {
  type: "OBJECT",
  additionalProperties: false,
  required: ["headerRow", "mapping"],
  properties: {
    headerRow: { type: "INTEGER" },
    mapping: {
      type: "OBJECT",
      additionalProperties: false,
      properties: Object.fromEntries(
        MAPPING_FIELDS.map((k) => [k, {
          type: "OBJECT",
          additionalProperties: false,
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

/**
 * Extract text content from XLSX workbook for AI analysis
 */
function extractSheetData(xlsxData) {
  const workbook = XLSX.read(xlsxData, { type: "base64" });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  // Get raw data as JSON
  const jsonData = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    defval: "",
    raw: false
  });

  // Filter empty rows
  const rows = jsonData.filter(row =>
    row.some(cell => cell && String(cell).trim())
  );

  return {
    sheetName,
    headers: rows[0] || [],
    data: rows,
    rowCount: rows.length,
    colCount: rows[0]?.length || 0
  };
}

/**
 * Build the AI prompt for quote sheet analysis
 */
function buildAnalysisPrompt(sheetData) {
  const previewRows = sheetData.data.slice(0, 15); // First 15 rows for context
  const tableStr = previewRows.map((row, i) =>
    `Row ${i}: ${row.map(c => `"${c}"`).join(" | ")}`
  ).join("\n");

  // Ensure we are getting exactly what we need
  return `You are a high-precision data extraction engine for a freight business.
  
  TASK: Map the columns of a supplier quote spreadsheet to our internal schema.
  
  CONTEXT: Suppliers often include:
  - Product Size (mm, for catalog)
  - Carton Size (cm, for shipping/freight) - THIS IS THE PRIORITY
  - G.W. (Gross Weight)
  - CBM (Total or Unit)
  - Packing (Qty per Box)
  
  DATA (first 15 rows):
  ${tableStr}
  
  SCHEMATIC INSTRUCTIONS:
  1. Identify the HEADER ROW index (0-based) where labels like "Item", "Price", "Size" appear.
  2. Map these fields:
     - sku: Item code/name
     - price: Unit FOB/Ex-Work price
     - productLength, productWidth, productHeight: The catalog item size
     - cartonLength, cartonWidth, cartonHeight: The shipping box size
     - pack: Qty per carton
     - grossWeight: Shipping weight
     - supplierCBM: The volume provided by supplier
  3. If a field is not found, use col: null.
  
  OUTPUT FORMAT: Return ONLY valid JSON.
  
  {
    "headerRow": 0,
    "mapping": {
      "sku": {"col": 1, "name": "Item No"},
      "price": {"col": 10, "name": "Price"},
      "productLength": {"col": 3, "name": "Size", "unit": "mm"},
      "productWidth": {"col": 3, "name": "Size", "unit": "mm"},
      "productHeight": {"col": 3, "name": "Size", "unit": "mm"},
      "cartonLength": {"col": 7, "name": "Carton", "unit": "cm"},
      "cartonWidth": {"col": 8, "name": "Carton", "unit": "cm"},
      "cartonHeight": {"col": 9, "name": "Carton", "unit": "cm"},
      "pack": {"col": 6, "name": "Packing"},
      "grossWeight": {"col": 11, "name": "G.W"},
      "supplierCBM": {"col": 12, "name": "CBM"}
    },
    "confidence": 1.0,
    "notes": "Semantic reasoning"
  }`;
}

/**
 * Ensure all required mapping fields exist with proper defaults
 */
function normalizeMapping(mapping) {
  const normalized = { ...mapping };
  
  // Ensure all required fields exist
  MAPPING_FIELDS.forEach(field => {
    if (!normalized[field]) {
      normalized[field] = {
        col: null,
        name: null,
        unit: null
      };
    } else {
      // Ensure each field has all required properties
      normalized[field] = {
        col: normalized[field].col ?? null,
        name: normalized[field].name ?? null,
        unit: normalized[field].unit ?? null
      };
    }
  });
  
  return normalized;
}

/**
 * Parse AI response to extract JSON (tolerant of LLM quirks)
 */
function parseAIResponse(responseText) {
  let cleaned = responseText.trim();

  // Strip markdown backticks if present
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');
  }

  // Find the first { and last } to isolate the JSON object
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');

  if (start === -1 || end === -1) {
    throw new Error("No JSON object found in AI response. Text: " + responseText.substring(0, 200));
  }

  let jsonStr = cleaned.substring(start, end + 1);

  // --- JSON Sanitization for LLM quirks ---
  // 1. Remove single-line comments (// ...)
  jsonStr = jsonStr.replace(/\/\/[^\n]*/g, '');
  // 2. Remove trailing commas before } or ]
  jsonStr = jsonStr.replace(/,\s*([\}\]])/g, '$1');

  try {
    return JSON.parse(jsonStr);
  } catch (e) {
    // Enhanced error logging with position context
    const m = e.message.match(/position (\d+)/);
    if (m) {
      const pos = Number(m[1]);
      console.error("Malformed JSON around pos", pos, jsonStr.slice(Math.max(0, pos - 80), pos + 80));
    }
    console.error("Malformed JSON (first 500 chars):", jsonStr.substring(0, 500));
    console.error("Full response length:", responseText.length);
    
    // Try to fix common JSON issues
    let fixedJson = jsonStr;
    
    // Fix missing closing braces
    const openBraces = (fixedJson.match(/\{/g) || []).length;
    const closeBraces = (fixedJson.match(/\}/g) || []).length;
    if (openBraces > closeBraces) {
      fixedJson += '}'.repeat(openBraces - closeBraces);
      console.log("Attempting to fix missing closing braces...");
      try {
        return JSON.parse(fixedJson);
      } catch (e2) {
        console.error("Fix attempt failed");
      }
    }
    
    throw new Error("AI returned malformed JSON: " + e.message);
  }
}

/**
 * Extract product data based on AI mapping
 */
function extractProducts(sheetData, mapping, headerRow) {
  console.log(`Extracting products starting at row ${headerRow + 1}`);
  console.log(`Extracting products starting at row ${headerRow + 1}`);
  const dataRows = sheetData.data.slice(headerRow + 1);

  // LOG DATA DUMP
  console.log("DATA DUMP (First 3 rows):", JSON.stringify(dataRows.slice(0, 3)));

  const products = [];

  for (let i = 0; i < dataRows.length; i++) {
    const row = dataRows[i];

    // Skip empty rows
    if (!row || !row.some(c => c && String(c).trim())) continue;

    const product = {
      sku: "",
      unitPrice: 0,
      // Product dimensions (reference only)
      productLength: 0,
      productWidth: 0,
      productHeight: 0,
      productSource: "",
      // Carton dimensions (for freight)
      cartonLength: 0,
      cartonWidth: 0,
      cartonHeight: 0,
      cartonSource: "",
      // Packing
      pack: 1,
      pack_text: "",
      totalCartons: null,
      // Weight
      grossWeight: 0,
      netWeight: null,
      weightUnit: "kg",
      // CBM
      supplierCBM: null,
      cbmSource: "",
      // Fallback dims text
      dims_text: ""
    };

    // Extract SKU (safe null check)
    const skuCol = mapping?.sku?.col;
    if (skuCol != null) {
      product.sku = String(row[skuCol] || "").trim();
    }

    // Extract price (safe null check)
    const priceCol = mapping?.price?.col;
    if (priceCol != null) {
      const priceStr = String(row[priceCol] || "");
      product.unitPrice = parseFloat(priceStr.replace(/[^0-9.-]/g, "")) || 0;
    }

    // Extract PRODUCT dimensions (reference) - safe null checks
    const productLengthCol = mapping?.productLength?.col;
    if (productLengthCol != null) {
      const dimStr = String(row[productLengthCol] || "");
      const dims = dimStr.match(/[\d.]+/g);
      if (dims && dims.length >= 3) {
        product.productLength = parseFloat(dims[0]) || 0;
        product.productWidth = parseFloat(dims[1]) || 0;
        product.productHeight = parseFloat(dims[2]) || 0;
        product.productSource = mapping.productLength.name || "";
      } else {
        const productWidthCol = mapping?.productWidth?.col;
        const productHeightCol = mapping?.productHeight?.col;
        
        product.productLength = productLengthCol != null ? parseFloat(String(row[productLengthCol]).replace(/[^0-9.-]/g, "")) || 0 : 0;
        product.productWidth = productWidthCol != null ? parseFloat(String(row[productWidthCol]).replace(/[^0-9.-]/g, "")) || 0 : 0;
        product.productHeight = productHeightCol != null ? parseFloat(String(row[productHeightCol]).replace(/[^0-9.-]/g, "")) || 0 : 0;
      }
    }

    // Extract CARTON dimensions (freight - PRIORITY) - safe null checks
    const cartonLengthCol = mapping?.cartonLength?.col;
    if (cartonLengthCol != null) {
      const dimStr = String(row[cartonLengthCol] || "");
      const dims = dimStr.match(/[\d.]+/g);
      if (dims && dims.length >= 3) {
        product.cartonLength = parseFloat(dims[0]) || 0;
        product.cartonWidth = parseFloat(dims[1]) || 0;
        product.cartonHeight = parseFloat(dims[2]) || 0;
        product.cartonSource = mapping.cartonLength.name || "";
      } else {
        const cartonWidthCol = mapping?.cartonWidth?.col;
        const cartonHeightCol = mapping?.cartonHeight?.col;
        
        product.cartonLength = cartonLengthCol != null ? parseFloat(String(row[cartonLengthCol]).replace(/[^0-9.-]/g, "")) || 0 : 0;
        product.cartonWidth = cartonWidthCol != null ? parseFloat(String(row[cartonWidthCol]).replace(/[^0-9.-]/g, "")) || 0 : 0;
        product.cartonHeight = cartonHeightCol != null ? parseFloat(String(row[cartonHeightCol]).replace(/[^0-9.-]/g, "")) || 0 : 0;
      }
    }

    // Dims text fallback (safe null check)
    const dimsTextCol = mapping?.dims_text?.col;
    if (dimsTextCol != null) {
      product.dims_text = String(row[dimsTextCol] || "");
    }

    // Extract pack (safe null check)
    const packCol = mapping?.pack?.col;
    if (packCol != null) {
      const packStr = String(row[packCol] || "");
      product.pack_text = packStr;

      // INTELLIGENT PACK PARSING (same as frontend)
      const packRaw = packStr.toUpperCase();

      // If "1PC" or "1 SET", force Pack = 1
      if (packRaw.includes('1PC') || packRaw.includes('1 PC') || packRaw.includes('1 SET') || packRaw.includes('1SET')) {
        product.pack = 1;
      }
      // Otherwise try regex
      else {
        const match = packRaw.match(/(\d+)\s*(PC|SET|PCS)/);
        if (match && match[1]) {
          product.pack = parseInt(match[1]);
        } else {
          // Fallback to simple number extraction
          product.pack = parseInt(packStr.replace(/[^0-9]/g, "")) || 1;
        }
      }
    }

    // Extract total cartons (for split packing) - safe null check
    const totalCartonsCol = mapping?.totalCartons?.col;
    if (totalCartonsCol != null) {
      product.totalCartons = parseInt(String(row[totalCartonsCol]).replace(/[^0-9]/g, "")) || null;
    }

    // Extract weight (safe null checks)
    const grossWeightCol = mapping?.grossWeight?.col;
    if (grossWeightCol != null) {
      const weightStr = String(row[grossWeightCol] || "");
      product.grossWeight = parseFloat(weightStr.replace(/[^0-9.-]/g, "")) || 0;
      product.weightUnit = mapping.grossWeight.unit || "kg";
    }

    const netWeightCol = mapping?.netWeight?.col;
    if (netWeightCol != null) {
      const weightStr = String(row[netWeightCol] || "");
      product.netWeight = parseFloat(weightStr.replace(/[^0-9.-]/g, "")) || null;
    }

    // Extract supplier CBM (safe null check)
    const supplierCBMCol = mapping?.supplierCBM?.col;
    if (supplierCBMCol != null) {
      const cbmStr = String(row[supplierCBMCol] || "");
      product.supplierCBM = parseFloat(cbmStr.replace(/[^0-9.-]/g, "")) || null;
      product.cbmSource = mapping.supplierCBM.name || "";
    }

    // Only add products with valid SKU or price
    // Only add products with valid SKU, Price, OR Dimensions
    // Relaxed constraint: If we have physical dimensions, it's likely a product.
    const hasDims = (product.productLength && product.productWidth) || (product.cartonLength && product.cartonWidth);

    if (product.sku || product.unitPrice > 0 || hasDims) {
      products.push(product);
    } else {
      // Log skipped row for debugging
      if (i < 50) console.log(`Skipped row ${i} - SKU: "${product.sku}", Price: ${product.unitPrice}, Dims: ${hasDims}`);
    }
  }

  return products;
}

/**
 * Main Cloud Function: Analyze Quote Sheet
 */
exports.analyzeQuoteSheetV2 = onRequest(
  {
    cors: true,
    maxInstances: 10,
    timeoutSeconds: 60,
    memory: "2GiB"
  },
  async (req, res) => {
    console.log("=== FUNCTION START - WITH FIXES ===");
    console.log("Request method:", req.method);
    console.log("Request headers:", JSON.stringify(req.headers, null, 2));
    console.log("Request body keys:", Object.keys(req.body || {}));
    
    // Native CORS handled via options above.
    try {
      const { rows, xlsxBase64, preview } = req.body;
      let sheetData;

      if (rows && Array.isArray(rows)) {
        console.log("Using provided rows (Lightweight JSON mode)");
        sheetData = {
          sheetName: "Imported Data",
          headers: rows[0] || [],
          data: rows,
          rowCount: rows.length,
          colCount: rows[0]?.length || 0
        };
      } else if (xlsxBase64) {
        console.log("Parsing XLSX file (Legacy Base64 mode)...");
        sheetData = extractSheetData(xlsxBase64);
      } else {
        res.status(400).json({ error: "Missing rows or xlsxBase64 in request body" });
        return;
      }

      console.log(`Processing ${sheetData.rowCount} rows, ${sheetData.colCount} columns`);

      // 2. Build prompt
      const prompt = buildAnalysisPrompt(sheetData);

      console.log("Generating AI content via REST API...");

      // Get Access Token via Firebase Admin
      const token = await admin.credential.applicationDefault().getAccessToken();
      const accessToken = token.access_token;

      const projectId = "landed-calculator";
      const location = "us-central1";
      const modelId = "gemini-2.5-flash";
      const apiEndpoint = `https://${location}-aiplatform.googleapis.com/v1beta1/projects/${projectId}/locations/${location}/publishers/google/models/${modelId}:generateContent`;

      const requestBody = {
        contents: [{
          role: "user",
          parts: [{ text: prompt }]
        }],
        generationConfig: {
          temperature: 0.1,
          topP: 0.9,
          maxOutputTokens: 4096
        }
      };

      const aiResponse = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${accessToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestBody)
      });

      if (!aiResponse.ok) {
        const errorText = await aiResponse.text();
        throw new Error(`Vertex AI REST Error ${aiResponse.status}: ${errorText}`);
      }

      const responseJson = await aiResponse.json();

      // SAFETY CHECK: Ensure we have content
      if (!responseJson.candidates || responseJson.candidates.length === 0 || !responseJson.candidates[0].content || !responseJson.candidates[0].content.parts || responseJson.candidates[0].content.parts.length === 0) {
        console.error("AI returned empty response or was blocked:", JSON.stringify(responseJson));
        throw new Error("AI service returned an empty response. This might be due to safety filters.");
      }

      const responseText = responseJson.candidates[0].content.parts[0].text;
      console.log("AI Response received (length: " + responseText.length + ")");

      // 3. Parse AI response
      const aiMapping = parseAIResponse(responseText);
      
      // 3.5. Normalize mapping to ensure all fields exist
      aiMapping.mapping = normalizeMapping(aiMapping.mapping);
      console.log("Normalized Mapping:", JSON.stringify(aiMapping.mapping));

      // 4. If preview mode, just return the mapping for user confirmation
      if (preview) {
        res.json({
          success: true,
          mode: "preview",
          sheetInfo: {
            name: sheetData.sheetName,
            rows: sheetData.rowCount,
            cols: sheetData.colCount,
            headers: sheetData.headers
          },
          mapping: aiMapping.mapping,
          headerRow: aiMapping.headerRow,
          confidence: aiMapping.confidence,
          notes: aiMapping.notes,
          sampleData: sheetData.data.slice(0, 5)
        });
        return;
      }

      // 5. Extract products based on mapping
      // FAILSAFE: Clamp headerRow to reasonable start
      const safeHeaderRow = (aiMapping.headerRow > 20) ? 0 : aiMapping.headerRow;
      const products = extractProducts(sheetData, aiMapping.mapping, safeHeaderRow);
      console.log(`Extracted ${products.length} products`);

      res.json({
        success: true,
        mode: "extract",
        products,
        mapping: aiMapping.mapping,
        confidence: aiMapping.confidence,
        originalData: {
          sheetName: sheetData.sheetName,
          headers: sheetData.headers,
          headerRow: aiMapping.headerRow,
          rawData: sheetData.data
        }
      });

    } catch (error) {
      console.error("=== FUNCTION ERROR ===");
      console.error("Error message:", error.message);
      console.error("Error stack:", error.stack);
      console.error("Error name:", error.name);
      console.error("=== END ERROR ===");
      
      res.status(500).json({
        error: error.message,
        details: error.stack,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Health check endpoint
 */
exports.health = onRequest({ cors: true }, (req, res) => {
  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    service: "quote-analyzer"
  });
});
