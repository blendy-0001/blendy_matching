@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ========================================
echo   協業マッチング - 簡単デプロイ
echo ========================================
echo.

REM Check if python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonがインストールされていません
    echo https://www.python.org/ からダウンロードしてください
    pause
    exit /b 1
)

REM Check if ngrok is installed
ngrok --version >nul 2>&1
if errorlevel 1 (
    echo ℹ️  ngrokをインストール中...
    echo.
    echo ngrokをダウンロードしてください: https://ngrok.com/download
    echo その後、以下のコマンドで認証してください:
    echo   ngrok config add-authtoken YOUR_AUTH_TOKEN
    echo.
    pause
    exit /b 1
)

echo ✓ 依存関係の確認完了
echo.

REM Kill any existing processes on port 8001
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo 📋 ファイアウォール許可について:
echo ========================================
echo サーバーを外部公開する場合、Windowsファイアウォールが
echo ポート8001へのアクセスをブロックする場合があります。
echo.
echo 以下いずれかを実行してください:
echo   1. Windowsファイアウォール設定で許可する
echo   2. 以下のコマンドを管理者権限で実行:
echo      netsh advfirewall firewall add rule name="Blendy-8001" dir=in action=allow protocol=tcp localport=8001
echo.
echo ========================================
echo.

REM Start Python server
echo 🚀 FastAPIサーバーを起動中...
start "FastAPI Server" python main.py

REM Wait for server to start
timeout /t 3 /nobreak

REM Start ngrok
echo 🌐 ngrokで外部公開中...
start "ngrok Tunnel" ngrok http 8001

REM Wait for ngrok to start
timeout /t 2 /nobreak

echo.
echo ========================================
echo   ✅ 準備完了！
echo ========================================
echo.
echo 📱 外部ユーザーに共有するURL:
echo.
echo   ngrokコンソール を開いて
echo   表示されている "Forwarding" URLをコピーしてください
echo   例: https://abc123.ngrok.io
echo.
echo 📝 申込フォーム:
echo   https://abc123.ngrok.io/register
echo.
echo 📊 ダッシュボード:
echo   https://abc123.ngrok.io/
echo.
echo ========================================
echo.
echo 💡 ヒント:
echo   - ブラウザで localhost:8001 でローカル確認可能
echo   - ngrokコンソール (localhost:4040) で トラフィック確認可能
echo   - 24時間で接続が切れるので、必要に応じて再度実行してください
echo.
echo [Ctrl+C] で終了します
echo.

pause
