# drawing-review-cn 一键发布到 GitHub
#
# 前置：
#   1) 已在 GitHub 网页创建**空仓库**（New repository → 不要勾选 Add README / .gitignore / License）
#   2) 本机已安装 Git for Windows 与 Git Credential Manager（Git for Windows 自带）
#
# 用法（git 不在 PATH 时脚本会自动搜索常见安装位置）：
#   pwsh -File publish.ps1 `
#     -RepoUrl https://github.com/<用户名>/drawing-review-cn.git `
#     -AuthorName "张三" -AuthorEmail "zhangsan@example.com"
#
# 推送时会由 Git Credential Manager 弹出浏览器窗口，用 GitHub 账号授权即可。
param(
    [Parameter(Mandatory = $true)][string]$RepoUrl,
    [string]$Branch = "main",
    [string]$AuthorName = "",
    [string]$AuthorEmail = "",
    [string]$Message = "feat: drawing-review-cn v1.1.0 图纸会审（施工图自审）智能体技能",
    [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"

# ---------- 1. 定位 git ----------
function Find-Git {
    $onPath = Get-Command git -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    $cands = @(
        "D:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    ) + (Get-ChildItem "$env:LOCALAPPDATA" -Directory -Filter "github-copilot-git-*" -ErrorAction SilentlyContinue |
         ForEach-Object { Join-Path $_.FullName "cmd\git.exe" }) +
        (Get-ChildItem "$env:LOCALAPPDATA\GitHubDesktop" -Directory -Filter "app-*" -ErrorAction SilentlyContinue |
         ForEach-Object { Join-Path $_.FullName "resources\app\git\cmd\git.exe" })
    foreach ($c in $cands) { if ($c -and (Test-Path $c)) { return $c } }
    return $null
}

$git = Find-Git
if (-not $git) {
    Write-Host "× 未找到 git，请先安装 Git for Windows：https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}
Write-Host "√ git: $git" -ForegroundColor Green
& $git --version

$repo = $PSScriptRoot
Push-Location $repo
try {
    # ---------- 2. 清理与初始化 ----------
    Write-Host "`n== 1/6 清理缓存目录 ==" -ForegroundColor Cyan
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Host "  已删 $($_.FullName)" }

    Write-Host "`n== 2/6 初始化仓库 ==" -ForegroundColor Cyan
    if (-not (Test-Path ".git")) { & $git init -b $Branch } else { Write-Host "  · 已存在 .git" }

    if ($AuthorName)  { & $git config user.name  $AuthorName;  Write-Host "  · user.name  = $AuthorName" }
    if ($AuthorEmail) { & $git config user.email $AuthorEmail; Write-Host "  · user.email = $AuthorEmail" }
    if (-not (& $git config user.name)) {
        Write-Host "× 未设置提交身份，请传 -AuthorName 与 -AuthorEmail" -ForegroundColor Red
        exit 1
    }

    # ---------- 3. 暂存 ----------
    Write-Host "`n== 3/6 暂存文件 ==" -ForegroundColor Cyan
    & $git add -A
    $staged = & $git diff --cached --name-only
    if (-not $staged) { Write-Host "  · 无新变更" }
    $staged | ForEach-Object { "  + $_" }

    # ---------- 4. 安全闸 ----------
    if (-not $SkipChecks) {
        Write-Host "`n== 4/6 安全闸：确认未把本地配置/图纸/产物入库 ==" -ForegroundColor Cyan
        $bad = $staged | Where-Object {
            $_ -match '(^|/)(config\.json|_render/|_render_ext/|_dwgtext/|_extract/|_findings/|_ledger/|_tmp/|drawings/)|\.(pdf|dwg|dxf)$|__pycache__'
        }
        if ($bad) {
            Write-Host "× 以下文件不应提交，请检查 .gitignore：" -ForegroundColor Red
            $bad | ForEach-Object { "  ! $_" }
            exit 1
        }
        Write-Host "  √ 干净"
    }

    # ---------- 5. 提交 ----------
    Write-Host "`n== 5/6 提交 ==" -ForegroundColor Cyan
    & $git commit -m $Message 2>&1 | ForEach-Object { "  $_" }
    if ($LASTEXITCODE -ne 0) { Write-Host "  · 无新变更可提交" }

    # ---------- 6. 推送 ----------
    Write-Host "`n== 6/6 推送（若弹出浏览器窗口，请用 GitHub 账号授权）==" -ForegroundColor Cyan
    if ((& $git remote) -contains "origin") { & $git remote set-url origin $RepoUrl }
    else { & $git remote add origin $RepoUrl }
    & $git push -u origin $Branch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n× 推送失败。常见原因：" -ForegroundColor Red
        Write-Host "  1) 仓库不存在或地址写错 → 先在 GitHub 网页创建空仓库"
        Write-Host "  2) 远程已有提交（创建时勾选了 README/.gitignore/License）→ 执行："
        Write-Host "     git pull --rebase origin $Branch  然后再 push"
        Write-Host "  3) 认证被取消 → 重跑本脚本"
        exit 1
    }

    Write-Host "`n√ 发布完成：$RepoUrl" -ForegroundColor Green
    Write-Host "  建议在 GitHub 仓库页面补充 About 简介与 Topics：" -ForegroundColor Green
    Write-Host "  construction, drawing-review, aec, cad, claude-skill, agent-skill, china"
}
finally {
    Pop-Location
}
