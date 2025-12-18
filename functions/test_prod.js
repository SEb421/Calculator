const fetch = require('node-fetch'); // You might need to install this if not available, or use native fetch in Node 18+

async function testProduction() {
    const url = 'https://analyzequotesheet-f3lqrbycya-uc.a.run.app';
    console.log(`Calling Production Endpoint: ${url}`);

    // Create a minimal dummy XLSX base64
    // This is a minimal valid XLSX with one cell "Product A"
    // equivalent to: echo "Product A" > test.csv | ... convert to xlsx
    // For simplicity, I'll send a known simple base64 of a tiny xlsx
    // Or better, I'll send the request expecting a "Missing xlsxBase64" error 
    // which CONFIRMS the function is running and reachable, 
    // OR I can try to hit the 'health' endpoint if I made one.

    // Let's try the health endpoint first as it's simpler
    const healthUrl = 'https://health-f3lqrbycya-uc.a.run.app';
    console.log(`Checking Health: ${healthUrl}`);
    try {
        const res = await fetch(healthUrl);
        console.log(`Health Status: ${res.status}`);
        const text = await res.text();
        console.log('Health Response:', text);
    } catch (e) {
        console.log('Health Check Failed:', e.message);
    }

    // Now try the AI endpoint with a dummy payload to check connectivity/auth
    // We expect a 400 "Missing xlsxBase64" if it reaches the code
    // If API is disabled, we might get 403 or 500
    console.log('\nChecking AI Endpoint Connectivity...');
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test: true })
        });
        console.log(`AI Status: ${res.status}`);
        const text = await res.text();
        console.log('AI Response:', text);

        if (res.status === 400 && text.includes('Missing xlsxBase64')) {
            console.log('SUCCESS: Function is running and reachable! (400 is expected for empty payload)');
        } else if (res.status === 500) {
            console.log('WARNING: Function crashed (could be API enablement issue)');
        }
    } catch (e) {
        console.log('AI Check Failed:', e.message);
    }
}

testProduction();
