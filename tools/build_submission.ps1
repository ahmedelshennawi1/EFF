# Build the single submission PDF handed to a client.
#
#   Arabic brief -> Arabic deck -> English brief -> English deck
#
# Arabic first because that is the language it will be read in; the English half
# follows so one file serves a mixed board without a second attachment.
#
# Usage:  powershell -File tools\build_submission.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root 'out'
New-Item -ItemType Directory -Force $outDir | Out-Null

$edge = @(
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw "No Chromium browser found for PDF rendering." }

# Each source page carries its language in the root tag; the on-page toggle is
# runtime-only, so the English variants are rendered from patched temp copies.
$parts = @(
  @{ src = 'offer\EFF-Proposal-Dakahlia.html'; lang = 'ar'; pdf = 'part1-proposal-ar.pdf' },
  @{ src = 'demo\EFF-Deck.html';            lang = 'ar'; pdf = 'part2-deck-ar.pdf'  },
  @{ src = 'offer\EFF-Proposal-Dakahlia.html'; lang = 'en'; pdf = 'part3-proposal-en.pdf' },
  @{ src = 'demo\EFF-Deck.html';            lang = 'en'; pdf = 'part4-deck-en.pdf'  }
)

$made = @()
foreach ($p in $parts) {
  $srcPath = Join-Path $root $p.src
  $render = $srcPath

  if ($p.lang -eq 'en') {
    $html = [System.IO.File]::ReadAllText($srcPath, [Text.Encoding]::UTF8)
    # Match the ROOT OPENING TAG and rewrite attributes only inside it.
    # These same attribute strings appear in the stylesheet's selectors
    # (#deck[data-lang="ar"], .page[dir="rtl"]); rewriting those inverts the
    # language rules and blanks the whole document. Note also that
    # [regex]::Replace has no static count overload — a trailing 1 is silently
    # read as RegexOptions and the replace goes global.
    $swapped = [regex]::Replace($html, '<div\b[^>]*\bid="(?:doc|deck)"[^>]*>', {
      param($m)
      $tag = $m.Value
      $tag = $tag -replace 'dir="rtl"', 'dir="ltr"'
      $tag = $tag -replace 'data-lang="ar"', 'data-lang="en"'
      $tag = $tag -replace 'data-doc-lang="ar"', 'data-doc-lang="en"'
      return $tag
    })
    if ($swapped -eq $html) { throw "Could not switch language in $($p.src)" }
    $render = Join-Path $env:TEMP ("eff-en-" + [System.IO.Path]::GetFileName($srcPath))
    [System.IO.File]::WriteAllText($render, $swapped, [Text.Encoding]::UTF8)
  }

  $out = Join-Path $outDir $p.pdf
  $uri = ([System.Uri]$render).AbsoluteUri
  # Start-Process -Wait is required: `&` returns before the PDF is flushed,
  # leaving no file and no error message.
  $proc = Start-Process -FilePath $edge -Wait -PassThru -NoNewWindow -ArgumentList @(
    '--headless=new', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer',
    '--run-all-compositor-stages-before-draw', '--virtual-time-budget=10000',
    "--print-to-pdf=$out", $uri)
  if ($proc.ExitCode -ne 0 -or -not (Test-Path $out)) {
    throw "Failed rendering $($p.src) [$($p.lang)] (exit $($proc.ExitCode))"
  }
  $made += $out
  Write-Output "  rendered $($p.pdf)"
}

$merge = Join-Path $PSScriptRoot 'merge_pdf.py'
& python $merge (Join-Path $outDir 'EFF-Submission-Dakahlia.pdf') @made
if ($LASTEXITCODE -ne 0) { throw "merge failed" }

$made | ForEach-Object { Remove-Item $_ -ErrorAction SilentlyContinue }
Get-ChildItem (Join-Path $outDir 'EFF-Submission-Dakahlia.pdf') |
  Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}}
