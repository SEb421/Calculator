/**
 * AI-Powered Quote Sheet Analyzer
 * Firebase Cloud Function for Landed Cost Calculator
 * 
 * Analyzes supplier quote spreadsheets using Gemini Pro AI to extract
 * pricing data, dimensions, and product information from varied formats.
 */

const { onRequest } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");
const XLSX = require("xlsx");

// Initialize admin if not already done
if (!admin.apps.length) {
  admin.initializeApp();
}

// Required mapping fields for AI analysis
const MAPPING_FIELDS = [
  "sku", "title", "price", "productLength", "productWidth", "productHeight",
  "cartonLength", "cartonWidth", "cartonHeight", "dims_text", "pack",
  "totalCartons", "grossWeight", "netWeight", "supplierCBM"
];

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
  const previewRows = sheetData.data.slice(0, 20); // More context for better analysis
  const tableStr = previewRows.map((row, i) =>
    `Row ${i}: ${row.map(c => `"${c}"`).join(" | ")}`
  ).join("\n");

  // Enhanced AI prompt with pattern recognition
  return `You are Eli's Brain - an advanced AI system specialized in analyzing supplier quote spreadsheets with intelligent pattern recognition.

MISSION: Extract and map supplier data with probabilistic reasoning and pattern matching.

INTELLIGENCE RULES:
1. SKU PATTERNS: Look for codes starting with "PSP", "COMP", or "CC" - these are always SKUs
2. PRICE PATTERNS: Identify currency symbols (£, $, €, USD, GBP) and decimal numbers
3. DIMENSION PATTERNS: Look for measurements with units (mm, cm, inches) and "x" separators
4. WEIGHT PATTERNS: Numbers followed by kg, g, lbs, oz
5. PACKING PATTERNS: Numbers followed by PC, PCS, SET, PACK, or similar
6. TITLE PATTERNS: Look for product names, descriptions, or titles (usually longest text fields)

PROBABILISTIC REASONING:
- If multiple columns could be SKU, choose the one with consistent prefixes (PSP/COMP/CC)
- If multiple price columns exist, prioritize FOB/EXW over retail prices
- For dimensions, prioritize carton/shipping sizes over product sizes for freight calculations
- Look for hidden patterns in seemingly random data

DATA ANALYSIS (first 20 rows):
${tableStr}

ENHANCED MAPPING REQUIREMENTS:
Map these fields using pattern recognition and probability:
- sku: Item codes (prioritize PSP/COMP/CC prefixes)
- title: Product names/descriptions (longest descriptive text)
- price: FOB/EXW unit prices (look for currency indicators)
- productLength/Width/Height: Catalog item dimensions (usually mm)
- cartonLength/Width/Height: Shipping box dimensions (usually cm) - PRIORITY
- dims_text: Any dimension text that doesn't fit standard format
- pack: Quantity per carton/box
- totalCartons: Total number of cartons (if specified)
- grossWeight: Shipping weight (kg preferred)
- netWeight: Product weight without packaging
- supplierCBM: Volume measurements (m³ or similar)

SMART ANALYSIS:
1. Examine column headers for semantic meaning
2. Analyze data patterns within columns
3. Use probability to resolve ambiguous mappings
4. Consider supplier naming conventions

OUTPUT: Return ONLY valid JSON with confidence scoring:

{
  "headerRow": 0,
  "mapping": {
    "sku": {"col": 1, "name": "Item Code", "unit": null, "confidence": 0.95, "pattern": "PSP prefix detected"},
    "title": {"col": 2, "name": "Description", "unit": null, "confidence": 0.90, "pattern": "longest text field"},
    "price": {"col": 10, "name": "FOB USD", "unit": "USD", "confidence": 0.85, "pattern": "currency symbol found"},
    "productLength": {"col": null, "name": null, "unit": null, "confidence": 0.0, "pattern": "not found"},
    "productWidth": {"col": null, "name": null, "unit": null, "confidence": 0.0, "pattern": "not found"},
    "productHeight": {"col": null, "name": null, "unit": null, "confidence": 0.0, "pattern": "not found"},
    "cartonLength": {"col": 7, "name": "Carton L", "unit": "cm", "confidence": 0.80, "pattern": "dimension with cm unit"},
    "cartonWidth": {"col": 8, "name": "Carton W", "unit": "cm", "confidence": 0.80, "pattern": "dimension with cm unit"},
    "cartonHeight": {"col": 9, "name": "Carton H", "unit": "cm", "confidence": 0.80, "pattern": "dimension with cm unit"},
    "dims_text": {"col": null, "name": null, "unit": null, "confidence": 0.0, "pattern": "not found"},
    "pack": {"col": 6, "name": "Packing", "unit": "PC", "confidence": 0.75, "pattern": "number with PC suffix"},
    "totalCartons": {"col": null, "name": null, "unit": null, "confidence": 0.0, "pattern": "not found"},
    "grossWeight": {"col": 11, "name": "G.W", "unit": "kg", "confidence": 0.70, "pattern": "weight abbreviation"},
    "netWeight": {"col": null, "name": null, "unit": null, "confidence": 0.0, "pattern": "not found"},
    "supplierCBM": {"col": 12, "name": "CBM", "unit": "m³", "confidence": 0.65, "pattern": "volume abbreviation"}
  },
  "confidence": 0.82,
  "notes": "Applied pattern recognition for PSP SKU prefix, identified shipping dimensions in cm, detected FOB pricing"
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
      title: "",
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

    // Extract title (safe null check)
    const titleCol = mapping?.title?.col;
    if (titleCol != null) {
      product.title = String(row[titleCol] || "").trim();
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

/**
 * Debug endpoint for monitoring AI calls
 */
exports.debug = onRequest({ cors: true }, async (req, res) => {
  console.log("=== DEBUG ENDPOINT ===");
  console.log("Request method:", req.method);
  console.log("Request body:", JSON.stringify(req.body, null, 2));
  
  try {
    // Test auth token
    const token = await admin.credential.applicationDefault().getAccessToken();
    console.log("Auth token acquired successfully");
    
    res.json({
      status: "debug-ok",
      timestamp: new Date().toISOString(),
      auth: "token-acquired",
      body: req.body
    });
  } catch (error) {
    console.error("Debug error:", error);
    res.status(500).json({
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});
