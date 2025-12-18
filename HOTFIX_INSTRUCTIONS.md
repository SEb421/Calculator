# HOTFIX for 500 Error

## The Problem
The AI is returning incomplete mappings missing these fields:
- `dims_text`
- `totalCartons` 
- `netWeight`

When the code tries to access `mapping.dims_text.col`, it crashes because `mapping.dims_text` is `undefined`.

## The Solution
The current code in this repo has the fix (`normalizeMapping` function), but it needs to be deployed via GitHub Actions.

## Immediate Steps:

1. **Commit and push the current changes:**
```bash
git add .
git commit -m "Fix: Add normalizeMapping to handle missing AI fields"
git push origin main
```

2. **Wait for GitHub Actions to deploy** (check the Actions tab in GitHub)

3. **Test after deployment**

## What the Fix Does:
- Adds `normalizeMapping()` function that ensures all required fields exist
- Missing fields get default values: `{ col: null, name: null, unit: null }`
- Prevents crashes when AI doesn't return complete mappings

## Current Error in Logs:
```
TypeError: Cannot read properties of undefined (reading 'col')
at extractProducts (/workspace/index.js:233:56)
```

This will be fixed once the updated code is deployed.