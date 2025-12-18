/**
 * SUPER EXPLICIT DEBUG MONITOR
 * This script logs every character of the URL construction to find the 404.
 */
const functions = require("firebase-functions");
const axios = require("axios"); // Ensure 'axios' is in your package.json
const { GoogleAuth } = require("google-auth-library");

exports.monitorAICall = functions.https.onRequest(async (req, res) => {
    console.log("=== [DEBUG START] ===");
    
    // --- STEP 1: CAPTURE VARIABLES ---
    // Note: We use string keys here because hyphens in variable names 
    // like 'landed-calculator' cause JavaScript to do SUBTRACTION.
    const config = {
        location: "us-central1",
        projectId: "landed-calculator", 
        modelId: "gemini-3-flash-preview"
    };

    console.log("[1] Configuration Values:");
    console.log(`    Location: "${config.location}"`);
    console.log(`    Project:  "${config.projectId}"`);
    console.log(`    Model:    "${config.modelId}"`);

    // --- STEP 2: MANUAL URL CONSTRUCTION LOGGING ---
    // This mimics your specific string to see if it's breaking
    const baseUrl = `https://${config.location}-aiplatform.googleapis.com`;
    const apiPath = `/v1beta1/projects/${config.projectId}/locations/${config.location}/publishers/google/models/${config.modelId}:generateContent`;
    const finalUrl = baseUrl + apiPath;

    console.log("[2] URL Segments:");
    console.log(`    Base: ${baseUrl}`);
    console.log(`    Path: ${apiPath}`);
    console.log(`    FINAL CONSTRUCTED URL: ${finalUrl}`);

    // AUTOMATIC DETECTION:
    if (finalUrl.includes("NaN") || finalUrl.includes("undefined")) {
        console.error("!!! ERROR DETECTED: Your URL contains 'NaN' or 'undefined'.");
        console.error("Cause: You are likely using a hyphenated variable name (like landed-calculator) without quotes.");
    }

    try {
        // --- STEP 3: AUTHENTICATION ---
        console.log("[3] Fetching Google Auth Token...");
        const auth = new GoogleAuth({
            scopes: 'https://www.googleapis.com/auth/cloud-platform'
        });
        const client = await auth.getClient();
        const headers = await client.getRequestHeaders();
        console.log("[3] Token Header Acquired.");

        // --- STEP 4: THE CALL ---
        console.log("[4] Sending Request to Google...");
        const response = await axios.post(finalUrl, req.body, {
            headers: { ...headers, "Content-Type": "application/json" },
            validateStatus: (status) => true // Don't crash on 404, we want to see it
        });

        // --- STEP 5: FINAL ANALYSIS ---
        console.log(`[5] GOOGLE RESPONSE STATUS: ${response.status} ${response.statusText}`);
        
        if (response.status === 404) {
            console.error("--- 404 DATA DUMP ---");
            console.error("This URL does not exist on Google's servers.");
            console.error("Full Error Body:", JSON.stringify(response.data, null, 2));
        }

        res.status(response.status).json({
            debug: {
                url_attempted: finalUrl,
                google_status: response.status,
                google_message: response.data
            }
        });

    } catch (err) {
        console.error("[CRASH] Debugger failed:", err.message);
        res.status(500).send(err.message);
    }
});