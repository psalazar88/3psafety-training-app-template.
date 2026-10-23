# Sends one test case (photos + field notes + customer memory) to the local model
# and saves the draft report next to it.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\draft-report.ps1 -Case test-cases\_example
#   powershell -ExecutionPolicy Bypass -File .\scripts\draft-report.ps1 -Case test-cases\_example -Model qwen3-vl
#
# A test case folder holds:
#   notes.md         field notes, unit IDs, inspection type   (required)
#   customer.txt     name of a folder under memory\           (optional)
#   *.jpg / *.png    photos                                   (optional)
#   actual-report.*  the report you really wrote, for comparing (ignored here)

param(
    [Parameter(Mandatory = $true)][string]$Case,
    [string]$Model = '3p-inspector',
    [string]$OllamaUrl = 'http://localhost:11434'
)

$root = Split-Path -Parent $PSScriptRoot
$caseDir = Resolve-Path $Case
$notesPath = Join-Path $caseDir 'notes.md'
if (-not (Test-Path $notesPath)) { throw "Missing $notesPath" }

$prompt = "Write a draft inspection report from these field notes and photos.`n`n## Field notes`n" +
    (Get-Content -Raw -Encoding UTF8 $notesPath)

# Customer memory: equipment history and preferences for this customer.
$customerFile = Join-Path $caseDir 'customer.txt'
if (Test-Path $customerFile) {
    $customer = (Get-Content -Raw $customerFile).Trim()
    $memDir = Join-Path $root "memory\$customer"
    if (-not (Test-Path $memDir)) { throw "No memory folder for customer '$customer' at $memDir" }
    $prompt += "`n`n## Customer memory ($customer)`n"
    foreach ($f in Get-ChildItem $memDir -Filter *.md | Sort-Object Name) {
        $prompt += "`n### $($f.BaseName)`n" + (Get-Content -Raw -Encoding UTF8 $f.FullName)
    }
}

$photos = Get-ChildItem $caseDir -File | Where-Object { $_.Extension -match '^\.(jpe?g|png)$' } | Sort-Object Name
if ($photos) {
    $prompt += "`n`n## Photos (in this order)`n" + (($photos | ForEach-Object { "- $($_.Name)" }) -join "`n")
}
$images = @($photos | ForEach-Object { [Convert]::ToBase64String([IO.File]::ReadAllBytes($_.FullName)) })

$body = @{
    model    = $Model
    stream   = $false
    messages = @(@{ role = 'user'; content = $prompt; images = $images })
} | ConvertTo-Json -Depth 6

Write-Host "Sending $($photos.Count) photo(s) to $Model ... (can take a few minutes on a laptop)"
$started = Get-Date
$resp = Invoke-RestMethod -Uri "$OllamaUrl/api/chat" -Method Post -ContentType 'application/json; charset=utf-8' `
    -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 1800
$seconds = [int]((Get-Date) - $started).TotalSeconds

$safeModel = $Model -replace '[^A-Za-z0-9._-]', '_'
$outPath = Join-Path $caseDir "draft-$safeModel.md"
[IO.File]::WriteAllText($outPath, $resp.message.content, (New-Object Text.UTF8Encoding $false))
Write-Host "Saved $outPath ($seconds s)"
