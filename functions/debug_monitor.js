/**
 * SUPER EXPLICIT DEBUG MONITOR
 * This script logs every character of the URL construction to find the 404.
 */
const { onRequest } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");

// Initialize admin if not already done
if (!admin.apps.length) {
  admin.initializeApp();
}

exports.monitorAICall = onRequest({ cors: true }, async (req, res) => {
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
        const token = await admin.credential.applicationDefault().getAccessToken();
        const accessToken = token.access_token;
        console.log("[3] Token Acquired.");

        // --- STEP 4: THE CALL ---
        console.log("[4] Sending Request to Google...");
        const response = await fetch(finalUrl, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(req.body)
        });

        // --- STEP 5: FINAL ANALYSIS ---
        console.log(`[5] GOOGLE RESPONSE STATUS: ${response.status} ${response.statusText}`);
        
        const responseData = await response.json().catch(() => ({}));
        
        if (response.status === 404) {
            console.error("--- 404 DATA DUMP ---");
            console.error("This URL does not exist on Google's servers.");
            console.error("Full Error Body:", JSON.stringify(responseData, null, 2));
        }

        res.status(response.status).json({
            debug: {
                url_attempted: finalUrl,
                google_status: response.status,
                google_message: responseData
            }
        });

    } catch (err) {
        console.error("[CRASH] Debugger failed:", err.message);
        res.status(500).send(err.message);
    }
});