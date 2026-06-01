# Claude API キーを更新するワンコマンドスクリプト
# 使い方: .\update_api_key.ps1

Write-Host "`n" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Claude API キー更新ツール" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Step 1: 新しいAPIキーの入力
Write-Host "`n[STEP 1] 新しい Claude API キーを入力してください`n" -ForegroundColor Yellow
Write-Host "Anthropic ダッシュボード: https://console.anthropic.com/account/keys`n"

$newKey = Read-Host "新しい API キー (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)"

if (-not $newKey -or -not $newKey.StartsWith("sk-ant-api03-")) {
    Write-Host "`n[ERROR] 無効なキーです。sk-ant-api03- で始まる必要があります。" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ キーが有効な形式です" -ForegroundColor Green

# Step 2: .env ファイルの確認
$envPath = ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "`n[ERROR] .env ファイルが見つかりません" -ForegroundColor Red
    exit 1
}

Write-Host "`n[STEP 2] .env ファイルをバックアップ中..." -ForegroundColor Yellow
Copy-Item ".env" ".env.backup" -Force
Write-Host "✓ バックアップ作成: .env.backup" -ForegroundColor Green

# Step 3: API キーを更新
Write-Host "`n[STEP 3] API キーを更新中..." -ForegroundColor Yellow

$envContent = Get-Content ".env" -Raw
$pattern = 'CLAUDE_API_KEY=sk-ant-api03-[a-zA-Z0-9]*'
$replacement = "CLAUDE_API_KEY=$newKey"
$newContent = $envContent -replace $pattern, $replacement

Set-Content ".env" $newContent -NoNewline
Write-Host "✓ API キーを更新しました" -ForegroundColor Green

# Step 4: 動作確認
Write-Host "`n[STEP 4] マッチング機能をテスト中..." -ForegroundColor Yellow
Write-Host "（初回は15秒程度かかります）`n"

& python test_matching.py > test_output.txt 2>&1
$lastExitCode = $LASTEXITCODE

$output = Get-Content test_output.txt -Raw
Remove-Item test_output.txt

# テスト結果の判定
if ($output -match "紹介文: \(紹介文の生成に失敗しました\)") {
    Write-Host "`n[WARN] API キーがまだ有効になっていません" -ForegroundColor Yellow
    Write-Host "数秒待ってからもう一度実行してください`n" -ForegroundColor Yellow
    Write-Host "もう一度テスト: python test_matching.py`n"
} elseif ($output -match "DONE\]") {
    Write-Host "`n===============================================" -ForegroundColor Green
    Write-Host "✅ API キー更新が完了しました！" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green

    # マッチング結果を表示
    $matches = $output -split "--- マッチング"
    $count = $matches.Count - 1
    Write-Host "`n📊 テスト結果: $count件のマッチングを生成` -ForegroundColor Cyan

    Write-Host "`n[STEP 5] 本番環境に反映する場合:`n" -ForegroundColor Yellow
    Write-Host "  git add .env`n  git commit -m 'Update Claude API key'`n  git push origin main`n"
} else {
    Write-Host "`n[ERROR] テストに失敗しました。以下を確認してください:`n" -ForegroundColor Red
    Write-Host "  1. API キーが正しく入力されたか`n  2. インターネット接続`n  3. 環境変数の設定`n"
    Write-Host "復元コマンド: copy .env.backup .env`n"
    exit 1
}

Write-Host "詳細は STATUS.md を参照してください`n"
Write-Host "===============================================`n" -ForegroundColor Cyan
