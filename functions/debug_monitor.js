const functions = require("firebase-functions");
const axios = require("axios");
const { GoogleAuth } = require("google-auth-library");

/**
 * This function acts as a high-visibility monitor.
 * Use this as your endpoint in your website code to see exactly what is failing.
 */
exports.monitorAICall = functions.https.onRequest(async (req, res) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] --- NEW DEBUG SESSION STARTED ---`);

    try {
        // --- STEP 1: CAPTURE INCOMING DATA FROM WEBSITE ---
        console.log("[DEBUG 1] Incoming Request Body:", JSON.stringify(req.body, null, 2));

        // --- STEP 2: VARIABLE INSPECTION ---
        // We use string literals here to avoid the "subtraction/hyphen" JS error
        const config = {
            location: "us-central1",
            projectId: "landed-calculator", 
            modelId: "gemini-3-flash-preview" 
        };

        console.log("[DEBUG 2] Variables used for URL construction:");
        console.log(`  - Location: "${config.location}"`);
        console.log(`  - Project:  "${config.projectId}"`);
        console.log(`  - Model:    "${config.modelId}"`);

        // --- STEP 3: URL CONSTRUCTION LOGGING ---
        // This is where you see if hyphens caused a "NaN" or "undefined" issue
        const urlBase = `https://${config.location}-aiplatform.googleapis.com`;
        const urlPath = `/v1/projects/${config.projectId}/locations/${config.location}/publishers/google/models/${config.modelId}:generateContent`;
        const finalFullUrl = urlBase + urlPath;

        console.log("[DEBUG 3] FINAL URL CONSTRUCTED:");
        console.log(`  ${finalFullUrl}`);
        
        // Validation check
        if (finalFullUrl.includes("NaN") || finalFullUrl.includes("undefined") || finalFullUrl.includes("//locations")) {
            console.error("[!!!] ERROR: URL is malformed! Check for empty variables or hyphenated variable names.");
        }

        // --- STEP 4: AUTHENTICATION CHECK ---
        console.log("[DEBUG 4] Fetching Auth Token...");
        const auth = new GoogleAuth({
            scopes: 'https://www.googleapis.com/auth/cloud-platform'
        });
        const client = await auth.getClient();
        const tokenHeaders = await client.getRequestHeaders();
        console.log("[DEBUG 4] Token acquired. Header detected:", tokenHeaders.Authorization ? "YES" : "NO");

        // --- STEP 5: THE OUTGOING CALL ---
        console.log("[DEBUG 5] Executing POST request to Google...");
        
        // We use 'validateStatus' to prevent the script from crashing on a 404
        // This allows us to actually read Google's error message.
        const response = await axios({
            method: 'post',
            url: finalFullUrl,
            data: req.body, // Pass through what your website sent
            headers: {
                ...tokenHeaders,
                "Content-Type": "application/json"
            },
            validateStatus: (status) => true 
        });

        // --- STEP 6: RESPONSE ANALYSIS ---
        console.log(`[DEBUG 6] Response Code: ${response.status} (${response.statusText})`);
        
        if (response.status === 404) {
            console.error("[CRITICAL 404] Google says this resource does not exist.");
            console.error("Payload from Google:", JSON.stringify(response.data, null, 2));
            
            // Log common causes based on the exact status
            if (response.data.error && response.data.error.message) {
                console.error(`Reason from Server: ${response.data.error.message}`);
            }
        } else if (response.status === 200) {
            console.log("[SUCCESS] Call went through perfectly.");
        }

        // Send everything back to your website so you can see it in the Browser Console
        res.status(response.status).json({
            debug_summary: {
                url_called: finalFullUrl,
                status_code: response.status,
                server_message: response.statusText,
                google_raw_error: response.data
            }
        });

    } catch (error) {
        console.error("[SYSTEM ERROR] The debug script itself crashed:");
        console.error(error.message);
        res.status(500).json({ error: error.message, stack: error.stack });
    }
});