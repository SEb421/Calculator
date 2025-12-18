/**
 * AI-Powered Quote Sheet Analyzer
 * Firebase Cloud Function for Landed Cost Calculator
 * 
 * Analyzes supplier quote spreadsheets using Gemini 3 Flash AI to extract
 * pricing data, dimensions, and product information from varied formats.
 * 
 * Gemini 3 Flash Features:
 * - Thinking levels for controlled reasoning (minimal, low, medium, high)
 * - Improved multimodal processing with media_resolution control
 * - Enhanced function calling with streaming support
 * - Better structured output validation
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
  const previewRows = sheetData.data.slice(0, 25); // More context for better analysis
  const tableStr = previewRows.map((row, i) =>
    `Row ${i}: ${row.map(c => `"${c}"`).join(" | ")}`
  ).join("\n");

  // Enhanced AI prompt leveraging Gemini 3 Flash's advanced reasoning
  return `ADVANCED SPREADSHEET ANALYSIS TASK

You are an expert data analyst with deep expertise in supplier spreadsheet analysis. Use your advanced reasoning capabilities to perform intelligent column mapping and data extraction.

REASONING PROCESS:
1. **ANALYZE STRUCTURE**: Examine the spreadsheet layout, identify header patterns, and understand the data organization
2. **PATTERN RECOGNITION**: Look beyond keywords - analyze data types, formats, and contextual relationships
3. **INTELLIGENT MAPPING**: Use multi-step reasoning to map columns based on content patterns, not just labels
4. **VALIDATION**: Cross-check your mappings against the actual data to ensure logical consistency

SPREADSHEET DATA (first 25 rows):
${tableStr}

INTELLIGENT ANALYSIS INSTRUCTIONS:
1. **Header Detection**: Identify the header row by looking for descriptive text rather than data values
2. **Pattern Recognition**: Look beyond keywords - analyze data patterns, formats, and context
3. **SKU Detection**: Find product codes (may be alphanumeric, have prefixes like PSP/COMP/CC, or be simple numbers)
4. **Title/Description**: Look for longer text fields describing products (may be in multiple languages)
5. **Price Analysis**: Identify monetary values (may have currency symbols, decimals, or be in different currencies)
6. **Dimension Intelligence**: 
   - Look for measurements in cm, mm, inches
   - May be combined (e.g., "25x20x15") or separate columns
   - Could be labeled as "size", "dimensions", "L×W×H", "carton size", etc.
   - **CRITICAL**: If you see "CARTON SIZE" followed by empty header columns, those are likely L, W, H dimensions
   - Look for 3 consecutive columns with numeric data that could be dimensions
   - **SPECIFIC PATTERN**: "CARTON SIZE" in column 8, empty headers in columns 9-10, "CBM" in column 11, "G.W" in column 12
7. **Pack Quantity**: Numbers followed by "PC", "PCS", "SET", "PACK" or in "PACKING" columns
8. **Weight**: Values with "kg", "g", "lb", "G.W", "GROSS WEIGHT" or in weight-appropriate ranges
9. **Volume**: CBM, m³, cubic measurements - often in columns labeled "CBM"
10. **Multi-Column Patterns**: 
    - Carton dimensions often split across 3 columns after "CARTON SIZE"
    - Empty headers may indicate continuation of previous column
    - Analyze data patterns in unnamed columns

SMART MAPPING RULES:
- If dimensions are combined in one cell (e.g., "25x20x15"), map all three dimension fields to that column
- If you find product descriptions, always map to title field
- Prioritize carton dimensions over product dimensions for shipping
- Look for data consistency patterns across rows
- Consider column position context (SKUs often first, prices often early, dimensions grouped)
- **CARTON DIMENSION DETECTION**: 
  * If "CARTON SIZE" contains combined dimensions (e.g., "56X10X127CM"), map cartonLength/Width/Height to that column
  * If "CARTON SIZE" is followed by empty columns with numeric data, map: cartonLength=col8, cartonWidth=col9, cartonHeight=col10
- **WEIGHT MAPPING**: "G.W" = grossWeight, look for numeric values in appropriate range (1-200kg typically)
- **CBM MAPPING**: "CBM" columns contain volume data, usually decimal values (0.001-1.000 range)  
- **PACK MAPPING**: "PACKING" columns contain quantity info, look for "PC", "SET", numbers
- **SPECIFIC TO THIS DATA**: Column 8="CARTON SIZE", Col 9&10=dimensions, Col 11="CBM", Col 12="G.W", Col 5="PACKING"

EXAMPLE ANALYSIS:
If you see headers like: ["IMAGE", "TIEM NO.", "DESCRIPTION", "SIZE", "MATERIAL", "PACKING", "FOB USD", "PORT", "CARTON SIZE", "", "", "CBM", "G.W", "FEST REMARK", ""]
Map as: sku=1, title=2, price=6, productLength=3, pack=5, cartonLength=8, cartonWidth=9, cartonHeight=10, supplierCBM=11, grossWeight=12

Return ONLY this JSON format (no extra text):
{
  "headerRow": [detected_header_row_index],
  "mapping": {
    "sku": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": null},
    "title": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": null},
    "price": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_currency]"},
    "productLength": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "productWidth": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "productHeight": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "cartonLength": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "cartonWidth": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "cartonHeight": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "dims_text": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": null},
    "pack": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "totalCartons": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": null},
    "grossWeight": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "netWeight": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"},
    "supplierCBM": {"col": [column_index_or_null], "name": "[detected_header_name]", "unit": "[detected_unit]"}
  }
}`;
}

/**
 * Ensure all required mapping fields exist with proper defaults
 */
function normalizeMapping(mapping) {
  const normalized = {};
  
  // Ensure all required fields exist and strip extra properties
  MAPPING_FIELDS.forEach(field => {
    if (mapping[field]) {
      // Only keep the required properties, strip confidence/pattern/etc
      normalized[field] = {
        col: mapping[field].col ?? null,
        name: mapping[field].name ?? null,
        unit: mapping[field].unit ?? null
      };
    } else {
      normalized[field] = {
        col: null,
        name: null,
        unit: null
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
    
    // Remove extra properties that might be causing issues
    fixedJson = fixedJson.replace(/"confidence":\s*[\d.]+,?\s*/g, '');
    fixedJson = fixedJson.replace(/"pattern":\s*"[^"]*",?\s*/g, '');
    
    // Fix trailing commas
    fixedJson = fixedJson.replace(/,\s*}/g, '}');
    fixedJson = fixedJson.replace(/,\s*]/g, ']');
    
    // Fix missing closing braces
    const openBraces = (fixedJson.match(/\{/g) || []).length;
    const closeBraces = (fixedJson.match(/\}/g) || []).length;
    if (openBraces > closeBraces) {
      fixedJson += '}'.repeat(openBraces - closeBraces);
    }
    
    console.log("Attempting to fix JSON issues...");
    try {
      const parsed = JSON.parse(fixedJson);
      console.log("JSON fix successful!");
      return parsed;
    } catch (e2) {
      console.error("Fix attempt failed:", e2.message);
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

    // Extract SKU with intelligent fallback (safe null check)
    const skuCol = mapping?.sku?.col;
    if (skuCol != null) {
      product.sku = String(row[skuCol] || "").trim();
    }
    
    // INTELLIGENT SKU FALLBACK: If no SKU found, look for product codes
    if (!product.sku && row && row.length > 0) {
      for (let colIdx = 0; colIdx < row.length; colIdx++) {
        const cellValue = String(row[colIdx] || "").trim();
        // Look for SKU patterns: alphanumeric codes, prefixed codes, etc.
        if (cellValue && (
            /^[A-Z]{2,5}\d+/.test(cellValue) || // PSP001, COMP002, etc.
            /^[A-Z0-9-]{4,15}$/.test(cellValue) || // General alphanumeric codes
            /^\d{4,10}$/.test(cellValue) // Numeric codes
          )) {
          product.sku = cellValue;
          console.log(`Intelligent SKU fallback for row ${i}: "${cellValue}"`);
          break;
        }
      }
    }

    // Extract title with intelligent fallback (safe null check)
    const titleCol = mapping?.title?.col;
    if (titleCol != null) {
      product.title = String(row[titleCol] || "").trim();
    }
    
    // INTELLIGENT TITLE FALLBACK: If no title found, look for longest text field
    if (!product.title && row && row.length > 0) {
      let longestText = "";
      let longestLength = 0;
      
      for (let colIdx = 0; colIdx < row.length; colIdx++) {
        const cellValue = String(row[colIdx] || "").trim();
        // Skip if it's clearly not a title (numbers, short codes, dimensions)
        if (cellValue.length > longestLength && 
            cellValue.length > 10 && // Must be reasonably long
            !/^\d+(\.\d+)?$/.test(cellValue) && // Not just a number
            !/^\d+x\d+x\d+/.test(cellValue) && // Not dimensions
            !/^[A-Z]{2,5}\d+$/.test(cellValue) && // Not a simple SKU pattern
            !cellValue.match(/^\d+\s*(PC|PCS|SET|KG|G|CM|MM)$/i)) { // Not quantity/measurement
          longestText = cellValue;
          longestLength = cellValue.length;
        }
      }
      
      if (longestText) {
        product.title = longestText;
        console.log(`Intelligent title fallback for row ${i}: "${longestText}"`);
      }
    }

    // Extract price with intelligent fallback (safe null check)
    const priceCol = mapping?.price?.col;
    if (priceCol != null) {
      const priceStr = String(row[priceCol] || "");
      product.unitPrice = parseFloat(priceStr.replace(/[^0-9.-]/g, "")) || 0;
    }
    
    // INTELLIGENT PRICE FALLBACK: If no price found, look for monetary values
    if (product.unitPrice === 0 && row && row.length > 0) {
      for (let colIdx = 0; colIdx < row.length; colIdx++) {
        const cellValue = String(row[colIdx] || "").trim();
        // Look for price patterns: numbers with currency symbols, decimal prices
        if (cellValue && (
            /^\$?\d+(\.\d{1,2})?$/.test(cellValue) || // $12.50 or 12.50
            /^\d+[.,]\d{2}$/.test(cellValue) || // 12,50 or 12.50
            /^USD?\s*\d+(\.\d{1,2})?/.test(cellValue) // USD 12.50
          )) {
          const price = parseFloat(cellValue.replace(/[^0-9.-]/g, ""));
          if (price > 0 && price < 10000) { // Reasonable price range
            product.unitPrice = price;
            console.log(`Intelligent price fallback for row ${i}: ${price}`);
            break;
          }
        }
      }
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
    const cartonWidthCol = mapping?.cartonWidth?.col;
    const cartonHeightCol = mapping?.cartonHeight?.col;
    
    // Try combined dimension string first (e.g., "25x20x15")
    let combinedDimensionsFound = false;
    if (cartonLengthCol != null) {
      const dimStr = String(row[cartonLengthCol] || "");
      const dims = dimStr.match(/[\d.]+/g);
      console.log(`Carton dimension parsing: "${dimStr}" -> [${dims?.join(', ') || 'no matches'}]`);
      if (dims && dims.length >= 3) {
        product.cartonLength = parseFloat(dims[0]) || 0;
        product.cartonWidth = parseFloat(dims[1]) || 0;
        product.cartonHeight = parseFloat(dims[2]) || 0;
        product.cartonSource = mapping.cartonLength.name || "";
        combinedDimensionsFound = true;
        console.log(`Combined dimensions found: ${product.cartonLength}×${product.cartonWidth}×${product.cartonHeight}`);
      } else {
        // Single dimension value
        product.cartonLength = parseFloat(dimStr.replace(/[^0-9.-]/g, "")) || 0;
      }
    }
    
    // Extract individual width/height if mapped separately AND combined dimensions not found
    if (!combinedDimensionsFound && cartonWidthCol != null && cartonWidthCol !== cartonLengthCol) {
      const dimStr = String(row[cartonWidthCol] || "");
      const width = parseFloat(dimStr.replace(/[^0-9.-]/g, "")) || 0;
      if (width > 0) {
        product.cartonWidth = width;
      }
    }
    
    if (!combinedDimensionsFound && cartonHeightCol != null && cartonHeightCol !== cartonLengthCol) {
      const dimStr = String(row[cartonHeightCol] || "");
      const height = parseFloat(dimStr.replace(/[^0-9.-]/g, "")) || 0;
      if (height > 0) {
        product.cartonHeight = height;
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

      // INTELLIGENT PACK PARSING
      const packRaw = packStr.toUpperCase();
      console.log(`Pack parsing: "${packStr}" -> "${packRaw}"`);

      // Extract number followed by PC, PCS, SET, etc.
      const match = packRaw.match(/(\d+)\s*(PC|PCS|SET|PACK|PIECE)/);
      if (match && match[1]) {
        product.pack = parseInt(match[1]);
        console.log(`Pack regex match: ${match[1]} -> ${product.pack}`);
      } else {
        // Fallback: extract any number from the string
        const numberMatch = packStr.match(/\d+/);
        if (numberMatch) {
          product.pack = parseInt(numberMatch[0]);
          console.log(`Pack fallback: ${numberMatch[0]} -> ${product.pack}`);
        } else {
          product.pack = 1; // Default
          console.log(`Pack default: 1`);
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
      const modelId = "gemini-3-flash-preview";
      const apiEndpoint = `https://${location}-aiplatform.googleapis.com/v1beta1/projects/${projectId}/locations/${location}/publishers/google/models/${modelId}:generateContent`;

      const requestBody = {
        contents: [{
          role: "user",
          parts: [{ text: prompt }]
        }],
        generationConfig: {
          temperature: 0.1,
          topP: 0.9,
          maxOutputTokens: 8192, // Increased for better analysis
          // Gemini 3 Flash: Use medium thinking level for complex spreadsheet analysis
          thinking_level: "MEDIUM",
          // Gemini 3 Flash: Enhanced structured output
          response_mime_type: "application/json",
          response_schema: {
            type: "object",
            properties: {
              headerRow: { type: "integer" },
              mapping: {
                type: "object",
                properties: {
                  sku: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  title: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  price: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  productLength: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  productWidth: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  productHeight: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  cartonLength: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  cartonWidth: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  cartonHeight: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  dims_text: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  pack: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  totalCartons: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  grossWeight: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  netWeight: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  },
                  supplierCBM: {
                    type: "object",
                    properties: {
                      col: { type: ["integer", "null"] },
                      name: { type: ["string", "null"] },
                      unit: { type: ["string", "null"] }
                    },
                    required: ["col", "name", "unit"]
                  }
                },
                required: ["sku", "title", "price", "productLength", "productWidth", "productHeight", "cartonLength", "cartonWidth", "cartonHeight", "dims_text", "pack", "totalCartons", "grossWeight", "netWeight", "supplierCBM"]
              }
            },
            required: ["headerRow", "mapping"]
          }
        },
        // Gemini 3 Flash: Enhanced system instruction for better reasoning
        systemInstruction: {
          parts: [{
            text: `You are an expert data analyst specializing in supplier spreadsheet analysis with advanced pattern recognition capabilities. 

CORE EXPERTISE:
- Intelligent column mapping beyond simple keyword matching
- Complex data pattern recognition across varied supplier formats
- Robust handling of messy, inconsistent spreadsheet layouts
- Advanced dimension parsing (combined strings, separate columns, mixed units)
- Multi-language product description analysis
- Currency and measurement unit standardization

ANALYSIS APPROACH:
1. DEEP PATTERN ANALYSIS: Look for data consistency patterns, not just keywords
2. CONTEXTUAL REASONING: Use surrounding data to infer column purposes
3. INTELLIGENT FALLBACKS: When primary mapping fails, use secondary indicators
4. VALIDATION: Cross-reference extracted data for logical consistency

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON with exact field structure
- Ensure all required mapping fields are present
- Use null for unmapped fields, never omit them
- Include confidence indicators in your reasoning process`
          }]
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
