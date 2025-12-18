/**
 * MINIMAL VERSION - Emergency fix for 500 errors
 * This version includes only the essential fix for the missing fields issue
 */

const { onRequest } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");
const XLSX = require("xlsx");

admin.initializeApp();

// Required mapping fields
const MAPPING_FIELDS = [
  "sku", "price", "productLength", "productWidth", "productHeight",
  "cartonLength", "cartonWidth", "cartonHeight", "dims_text", "pack",
  "totalCartons", "grossWeight", "netWeight", "supplierCBM"
];

/**
 * CRITICAL FIX: Ensure all required mapping fields exist
 */
function normalizeMapping(mapping) {
  const normalized = { ...mapping };
  
  MAPPING_FIELDS.forEach(field => {
    if (!normalized[field]) {
      normalized[field] = {
        col: null,
        name: null,
        unit: null
      };
    } else {
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
 * Extract text content from XLSX workbook for AI analysis
 */
function extractSheetData(xlsxData) {
  const workbook = XLSX.read(xlsxData, { type: "base64" });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  const jsonData = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    defval: "",
    raw: false
  });

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
  const previewRows = sheetData.data.slice(0, 15);
  const tableStr = previewRows.map((row, i) =>
    `Row ${i}: ${row.map(c => `"${c}"`).join(" | ")}`
  ).join("\n");

  return `You are a high-precision data extraction engine for a freight business.
  
  TASK: Map the columns of a supplier quote spreadsheet to our internal schema.
  
  DATA (first 15 rows):
  ${tableStr}
  
  INSTRUCTIONS:
  1. Identify the HEADER ROW index (0-based) where labels like "Item", "Price", "Size" appear.
  2. Map these fields (use col: null if not found):
     - sku: Item code/name
     - price: Unit FOB/Ex-Work price
     - productLength, productWidth, productHeight: The catalog item size
     - cartonLength, cartonWidth, cartonHeight: The shipping box size
     - dims_text: Any dimension text field
     - pack: Qty per carton
     - totalCartons: Total number of cartons
     - grossWeight: Shipping weight
     - netWeight: Net weight
     - supplierCBM: The volume provided by supplier
  
  OUTPUT FORMAT: Return ONLY valid JSON with ALL fields included.
  
  {
    "headerRow": 0,
    "mapping": {
      "sku": {"col": 1, "name": "Item No", "unit": null},
      "price": {"col": 10, "name": "Price", "unit": null},
      "productLength": {"col": null, "name": null, "unit": null},
      "productWidth": {"col": null, "name": null, "unit": null},
      "productHeight": {"col": null, "name": null, "unit": null},
      "cartonLength": {"col": null, "name": null, "unit": null},
      "cartonWidth": {"col": null, "name": null, "unit": null},
      "cartonHeight": {"col": null, "name": null, "unit": null},
      "dims_text": {"col": null, "name": null, "unit": null},
      "pack": {"col": null, "name": null, "unit": null},
      "totalCartons": {"col": null, "name": null, "unit": null},
      "grossWeight": {"col": null, "name": null, "unit": null},
      "netWeight": {"col": null, "name": null, "unit": null},
      "supplierCBM": {"col": null, "name": null, "unit": null}
    },
    "confidence": 1.0,
    "notes": "Mapping complete"
  }`;
}

/**
 * Parse AI response to extract JSON
 */
function parseAIResponse(responseText) {
  let cleaned = responseText.trim();

  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');
  }

  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');

  if (start === -1 || end === -1) {
    throw new Error("No JSON object found in AI response");
  }

  let jsonStr = cleaned.substring(start, end + 1);
  jsonStr = jsonStr.replace(/\/\/[^\n]*/g, '');
  jsonStr = jsonStr.replace(/,\s*([\}\]])/g, '$1');

  try {
    return JSON.parse(jsonStr);
  } catch (e) {
    console.error("Malformed JSON:", jsonStr.substring(0, 500));
    throw new Error("AI returned malformed JSON: " + e.message);
  }
}

/**
 * Extract product data based on AI mapping
 */
function extractProducts(sheetData, mapping, headerRow) {
  console.log(`Extracting products starting at row ${headerRow + 1}`);
  const dataRows = sheetData.data.slice(headerRow + 1);
  const products = [];

  for (let i = 0; i < dataRows.length; i++) {
    const row = dataRows[i];
    if (!row || !row.some(c => c && String(c).trim())) continue;

    const product = {
      sku: "",
      unitPrice: 0,
      productLength: 0,
      productWidth: 0,
      productHeight: 0,
      cartonLength: 0,
      cartonWidth: 0,
      cartonHeight: 0,
      pack: 1,
      pack_text: "",
      totalCartons: null,
      grossWeight: 0,
      netWeight: null,
      weightUnit: "kg",
      supplierCBM: null,
      dims_text: ""
    };

    // SAFE EXTRACTION with null checks
    const skuCol = mapping?.sku?.col;
    if (skuCol != null) {
      product.sku = String(row[skuCol] || "").trim();
    }

    const priceCol = mapping?.price?.col;
    if (priceCol != null) {
      const priceStr = String(row[priceCol] || "");
      product.unitPrice = parseFloat(priceStr.replace(/[^0-9.-]/g, "")) || 0;
    }

    // Add other field extractions with safe null checks...
    const dimsTextCol = mapping?.dims_text?.col;
    if (dimsTextCol != null) {
      product.dims_text = String(row[dimsTextCol] || "");
    }

    const packCol = mapping?.pack?.col;
    if (packCol != null) {
      const packStr = String(row[packCol] || "");
      product.pack_text = packStr;
      product.pack = parseInt(packStr.replace(/[^0-9]/g, "")) || 1;
    }

    const grossWeightCol = mapping?.grossWeight?.col;
    if (grossWeightCol != null) {
      const weightStr = String(row[grossWeightCol] || "");
      product.grossWeight = parseFloat(weightStr.replace(/[^0-9.-]/g, "")) || 0;
    }

    // Only add products with valid data
    if (product.sku || product.unitPrice > 0) {
      products.push(product);
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
    console.log("=== MINIMAL VERSION WITH FIX ===");
    
    try {
      const { rows, xlsxBase64, preview } = req.body;
      let sheetData;

      if (rows && Array.isArray(rows)) {
        sheetData = {
          sheetName: "Imported Data",
          headers: rows[0] || [],
          data: rows,
          rowCount: rows.length,
          colCount: rows[0]?.length || 0
        };
      } else if (xlsxBase64) {
        sheetData = extractSheetData(xlsxBase64);
      } else {
        res.status(400).json({ error: "Missing rows or xlsxBase64 in request body" });
        return;
      }

      const prompt = buildAnalysisPrompt(sheetData);

      // Get Access Token
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
          responseMimeType: "application/json",
          temperature: 0.2,
          topP: 0.8,
          maxOutputTokens: 2048
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

      if (!responseJson.candidates || responseJson.candidates.length === 0) {
        throw new Error("AI service returned an empty response");
      }

      const responseText = responseJson.candidates[0].content.parts[0].text;
      const aiMapping = parseAIResponse(responseText);
      
      // CRITICAL FIX: Normalize mapping to ensure all fields exist
      aiMapping.mapping = normalizeMapping(aiMapping.mapping);
      console.log("✅ Mapping normalized - all fields present");

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

      const safeHeaderRow = (aiMapping.headerRow > 20) ? 0 : aiMapping.headerRow;
      const products = extractProducts(sheetData, aiMapping.mapping, safeHeaderRow);

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
      console.error("=== ERROR ===", error.message);
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
    service: "quote-analyzer-minimal"
  });
});