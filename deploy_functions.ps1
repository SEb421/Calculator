# Deploy Firebase Functions
Write-Host "Deploying Firebase Functions..." -ForegroundColor Green

# Check if firebase CLI is available
try {
    firebase --version
    Write-Host "Firebase CLI found" -ForegroundColor Green
} catch {
    Write-Host "Firebase CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "npm install -g firebase-tools" -ForegroundColor Yellow
    exit 1
}

# Deploy functions
Write-Host "Deploying functions..." -ForegroundColor Yellow
firebase deploy --only functions

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Functions deployed successfully!" -ForegroundColor Green
    Write-Host "Test the health endpoint:" -ForegroundColor Cyan
    Write-Host "https://analyzequotesheetv2-f3lqrbycya-uc.a.run.app/health" -ForegroundColor Blue
} else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}