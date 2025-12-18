const API_KEY = 'AQ.Ab8RN6IHk10yFU-Bm8usZPgGOiA72507iMcIQ-2QSUjYo0u8yQ';

async function test() {
    console.log(`Testing with provided key: ${API_KEY.substring(0, 6)}...`);
    const question = "Tell me a fun fact about space.";
    console.log(`Asking: "${question}"`);

    // 1. Try Google Generative Language API (API Key style)
    try {
        console.log('\n--- Attempt 1: Google AI Studio (API Key) ---');
        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{ parts: [{ text: question }] }]
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('SUCCESS!');
            console.log(data.candidates[0].content.parts[0].text);
            return;
        } else {
            console.log(`Failed: ${response.status} - ${await response.text()}`);
        }
    } catch (e) {
        console.log('Error:', e.message);
    }

    // 2. Try Vertex AI (Bearer Token style) - Note: standard Vertex requires Project ID in URL
    // We'll guess project 'landed-calculator' since that's what we are working on
    try {
        console.log('\n--- Attempt 2: Vertex AI (Bearer Token) ---');
        const project = 'landed-calculator';
        const location = 'us-central1';
        const model = 'gemini-1.5-flash';
        const url = `https://${location}-aiplatform.googleapis.com/v1/projects/${project}/locations/${location}/publishers/google/models/${model}:generateContent`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify({
                contents: [{ role: 'user', parts: [{ text: question }] }]
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('SUCCESS!');
            console.log(data.candidates[0].content.parts[0].text);
            return;
        } else {
            console.log(`Failed: ${response.status} - ${await response.text()}`);
        }
    } catch (e) {
        console.log('Error:', e.message);
    }
}

test();
