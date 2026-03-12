Write-Host "[PS] pushing to GitHub..." -ForegroundColor Yellow
git push origin main
Write-Host "[PS] pushing to Hugging Face..." -ForegroundColor Yellow
git push alt main

Write-Host "[PS] docker build and push..." -ForegroundColor Yellow
docker build -t tuanphung69/travel-ai-backend:latest .
docker push tuanphung69/travel-ai-backend:latest

Write-Host "[PS] done!!!!!!!!!!!!!" -ForegroundColor Green