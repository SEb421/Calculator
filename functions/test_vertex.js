const { VertexAI } = require('@google-cloud/vertexai');

async function test() {
    console.log('Initializing Vertex AI (Project: landed-calculator, Location: us-central1)...');
    const vertexAI = new VertexAI({
        project: 'landed-calculator',
        location: 'us-central1'
    });

    const model = vertexAI.getGenerativeModel({
        model: 'gemini-1.5-flash'
    });

    const question = 'Tell me a short joke about spreadsheets.';
    console.log(`\nAsking Gemini: "${question}"\n`);

    try {
        const result = await model.generateContent(question);
        const response = await result.response;
        const text = response.candidates[0].content.parts[0].text;
        console.log('---------------------------------------------------');
        console.log('AI RESPONSE:');
        console.log(text);
        console.log('---------------------------------------------------');
    } catch (e) {
        console.error('ERROR Calling Vertex AI:', e.message);
        console.error('\nNOTE: This error likely means you need to authenticate locally.');
        console.error('Try running: gcloud auth application-default login');
    }
}

test();
