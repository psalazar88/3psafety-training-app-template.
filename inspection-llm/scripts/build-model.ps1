# Builds (or rebuilds) the 3p-inspector model from the Modelfile and the rulebook.
# Run again any time you edit rulebook/system-prompt.md.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\build-model.ps1

$root = Split-Path -Parent $PSScriptRoot
$rulebook = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'rulebook\system-prompt.md')
$modelfile = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Modelfile')

# Ollama's SYSTEM block is wrapped in triple quotes, so the rulebook must not contain them.
if ($rulebook.Contains('"""')) { throw 'rulebook/system-prompt.md must not contain triple quotes (""").' }

$built = $modelfile.Replace('{{RULEBOOK}}', $rulebook)
$out = Join-Path $env:TEMP 'Modelfile.3p-inspector'
[IO.File]::WriteAllText($out, $built, (New-Object Text.UTF8Encoding $false))

ollama create 3p-inspector -f $out
if ($LASTEXITCODE -ne 0) { throw 'ollama create failed - is the base model in the Modelfile pulled? (ollama pull <tag>)' }
Write-Host 'Built model: 3p-inspector'
