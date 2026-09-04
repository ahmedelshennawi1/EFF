# Render the pitch deck to PDF, Arabic and English.
#
# Headless Edge is the only HTML->PDF path on this machine (no LibreOffice, no
# poppler). Two notes learned the hard way:
#   * Start-Process -Wait is required; calling the exe with & returns before the
#     PDF is flushed and you get no file and no error.
#   * The deck's print CSS keeps the dark ground on purpose, so the PDF needs
#     print-color-adjust:exact — light text on a white page would be invisible.
#
# Usage:  powershell -File tools\deck2pdf.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$deck = Join-Path $root 'demo\EFF-Deck.html'
$outDir = Join-Path $root 'out'
New-Item -ItemType Directory -Force $outDir | Out-Null

$edge = @(
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw "No Chromium browser found for PDF rendering." }

# The English PDF needs the deck opened already switched; the toggle is runtime.
$tmp = Join-Path $env:TEMP 'EFF-Deck-EN.html'
$html = [System.IO.File]::ReadAllText($deck, [Text.Encoding]::UTF8)
$en = $html.Replace('<div id="deck" dir="rtl" data-lang="ar">',
                    '<div id="deck" dir="ltr" data-lang="en">')
if ($en -eq $html) { throw "Could not find the deck root tag to switch language." }
[System.IO.File]::WriteAllText($tmp, $en, [Text.Encoding]::UTF8)

$jobs = @(
  @{ src = $deck; out = Join-Path $outDir 'EFF-Deck-AR.pdf' },
  @{ src = $tmp;  out = Join-Path $outDir 'EFF-Deck-EN.pdf' }
)
foreach ($j in $jobs) {
  $uri = ([System.Uri]$j.src).AbsoluteUri
  $p = Start-Process -FilePath $edge -Wait -PassThru -NoNewWindow -ArgumentList @(
    '--headless=new', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer',
    '--run-all-compositor-stages-before-draw', '--virtual-time-budget=10000',
    "--print-to-pdf=$($j.out)", $uri)
  if ($p.ExitCode -ne 0 -or -not (Test-Path $j.out)) {
    throw "Failed to render $($j.out) (exit $($p.ExitCode))"
  }
  $kb = [math]::Round((Get-Item $j.out).Length / 1KB, 1)
  Write-Output "$([System.IO.Path]::GetFileName($j.out))  ${kb} KB"
}
Remove-Item $tmp -ErrorAction SilentlyContinue
