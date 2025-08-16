# PowerShell script to get token and test Spotify API

# Get the access token
$tokenResponse = Invoke-RestMethod -Uri 'http://127.0.0.1:5001/get_access_token' -Method Get
$token = $tokenResponse.access_token

Write-Host "Token obtained: $($token.Substring(0,20))..." -ForegroundColor Green
Write-Host "Token type: $($tokenResponse.type)" -ForegroundColor Green

# Test the Spotify API with the token
Write-Host "`nTesting Spotify API..." -ForegroundColor Yellow

try {
    $spotifyResponse = Invoke-RestMethod -Uri 'https://api.spotify.com/v1/tracks/2TpxZ7JUBn3uw46aR7qd6V' -Headers @{"Authorization" = "Bearer $token"} -Method Get
    
    Write-Host "✅ SUCCESS! Track found:" -ForegroundColor Green
    Write-Host "  Track: $($spotifyResponse.name)" -ForegroundColor Cyan
    Write-Host "  Artist: $($spotifyResponse.artists[0].name)" -ForegroundColor Cyan
    Write-Host "  Album: $($spotifyResponse.album.name)" -ForegroundColor Cyan
    Write-Host "  Duration: $([math]::Round($spotifyResponse.duration_ms / 1000, 0)) seconds" -ForegroundColor Cyan
} catch {
    Write-Host "❌ FAILED to access Spotify API" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎵 Your PowerShell command template:" -ForegroundColor Magenta
Write-Host "Invoke-RestMethod -Uri 'https://api.spotify.com/v1/tracks/TRACK_ID' -Headers @{`"Authorization`" = `"Bearer $token`"} -Method Get" -ForegroundColor White
