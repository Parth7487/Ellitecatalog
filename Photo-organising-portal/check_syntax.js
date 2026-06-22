const fs = require('fs');
const vm = require('vm');
const path = require('path');

const htmlPath = path.join(__dirname, 'visual_audit_sheet.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// Extract script content
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!scriptMatch) {
    console.error("No script tag found!");
    process.exit(1);
}

const jsCode = scriptMatch[1];

try {
    // Attempt to parse the JS code in VM context
    new vm.Script(jsCode);
    console.log("✅ JavaScript syntax is valid!");
} catch (e) {
    console.error("❌ JavaScript Syntax Error found:");
    console.error(e.message);
    console.error(e.stack);
    process.exit(1);
}
