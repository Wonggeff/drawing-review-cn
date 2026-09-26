# Parallel batch dump of project DWG text via AutoCAD Core Console
$acc  = if ($env:DRAWING_REVIEW_ACCORECONSOLE) { $env:DRAWING_REVIEW_ACCORECONSOLE } else { "D:\Program Files\Autodesk\AutoCAD 2025\accoreconsole.exe" }
$base = if ($env:DRAWING_REVIEW_TMP) { $env:DRAWING_REVIEW_TMP } else { Join-Path $PSScriptRoot "..\_tmp" }
$dst  = if ($env:DRAWING_REVIEW_DWGTEXT) { $env:DRAWING_REVIEW_DWGTEXT } else { Join-Path $PSScriptRoot "..\_dwgtext" }
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$root = if ($env:DRAWING_REVIEW_ROOT) { $env:DRAWING_REVIEW_ROOT } else { Join-Path $PSScriptRoot "..\drawings" }

$files = Get-ChildItem -Path $root -Recurse -File -Filter *.dwg | Sort-Object FullName
Write-Output "total dwg: $($files.Count)"

$items = @()
$i = 0
foreach ($f in $files) { $i++; $items += [pscustomobject]@{ key = ("dwg{0:d3}" -f $i); path = $f.FullName; rel = $f.FullName.Substring($root.Length).TrimStart('\'); mb = [math]::Round($f.Length/1MB,2) } }

$results = $items | ForEach-Object -ThrottleLimit 5 -Parallel {
    $it = $_
    $acc = $using:acc; $base = $using:base; $dst = $using:dst
    $slot = Join-Path $base ("slot_" + $it.key)
    New-Item -ItemType Directory -Force -Path $slot | Out-Null
    Copy-Item (Join-Path $base "dump.lsp") (Join-Path $slot "dump.lsp") -Force
    $lsp = ((Join-Path $slot "dump.lsp") -replace '\\','/')
    $cur = ((Join-Path $slot "cur.txt") -replace '\\','/')
    $scr = Join-Path $slot "dump.scr"
    $lines = @("SECURELOAD", "0", "(load `"$lsp`")", "(dumptext `"$cur`")")
    Set-Content -Path $scr -Value $lines -Encoding ASCII
    try { & $acc /i $it.path /s $scr 2>&1 | Out-Null } catch { }
    $sz = -1
    $c = Join-Path $slot "cur.txt"
    if (Test-Path $c) { Copy-Item $c (Join-Path $dst ($it.key + ".txt")) -Force; $sz = (Get-Item (Join-Path $dst ($it.key + ".txt"))).Length }
    Remove-Item $slot -Recurse -Force -ErrorAction SilentlyContinue
    [pscustomobject]@{ key = $it.key; rel = $it.rel; size = $sz; mb = $it.mb }
}

$results | Sort-Object key | Export-Csv -Path "$dst\_manifest.csv" -NoTypeInformation -Encoding UTF8
Write-Output ("DONE " + $results.Count + " ok=" + (($results | Where-Object { $_.size -gt 0 }).Count))
