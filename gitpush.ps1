Write-Host "[PS] pushing to GitHub..." -ForegroundColor Yellow
git push origin main
Write-Host "[PS] pushing to Hugging Face..." -ForegroundColor Yellow
git push alt main

Write-Host "[PS] done!!!!!!!!!!!!!" -ForegroundColor Green