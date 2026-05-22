#!/usr/bin/env python3
"""
協業マッチングシステム - 簡単デプロイスクリプト
外部ユーザーにフォームを共有する際に、このスクリプトを実行してください
"""
import subprocess
import sys
import time
import os
import signal
import socket
from pathlib import Path

def check_port_available(port):
    """ポートが利用可能か確認"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def kill_process_on_port(port):
    """指定ポートで実行中のプロセスを終了"""
    if os.name == 'nt':  # Windows
        os.system(f'netstat -aon | find ":{port}" | find "LISTENING" && taskkill /F /PID <PID>')
    else:  # Linux/Mac
        os.system(f'lsof -ti:{port} | xargs kill -9 2>/dev/null')

def check_dependency(command, install_url=None):
    """依存関係の確認"""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        if install_url:
            print(f"\n❌ {command}がインストールされていません")
            print(f"   {install_url} からダウンロードしてください\n")
        return False

def main():
    print("\n" + "="*50)
    print("  協業マッチング - 簡単デプロイ")
    print("="*50 + "\n")

    # 依存関係の確認
    print("📦 依存関係を確認中...\n")

    if not check_dependency('python'):
        print("❌ Pythonがインストールされていません")
        sys.exit(1)

    if not check_dependency('ngrok', 'https://ngrok.com/download'):
        print("⚠️  ngrokなしで続行します (ローカルのみアクセス可能)")
        use_ngrok = False
    else:
        use_ngrok = True

    print("✓ 依存関係の確認完了\n")

    # プロセスのクリーンアップ
    print("🧹 既存プロセスをクリーンアップ中...")
    port = 8001

    if not check_port_available(port):
        print(f"   ⚠️  ポート {port} は既に使用中です")
        kill_process_on_port(port)
        time.sleep(1)

    # サーバー起動
    print(f"\n🚀 FastAPIサーバーを起動中 (ポート {port})...")
    server_process = subprocess.Popen(
        [sys.executable, 'main.py'],
        cwd=Path(__file__).parent,
        env={**os.environ, 'PORT': str(port)}
    )

    time.sleep(3)  # サーバー起動待機

    # ngrok起動
    ngrok_process = None
    if use_ngrok:
        print("🌐 ngrokで外部公開中...\n")
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            cwd=Path(__file__).parent
        )
        time.sleep(2)

        print("\n" + "="*50)
        print("  ✅ 準備完了！")
        print("="*50)
        print("\n📱 外部ユーザーに共有するURL:")
        print("   (ngrokコンソールを確認して 'Forwarding' URLをコピー)\n")
        print("   フォーム URL: https://xxx.ngrok.io/register")
        print("   ダッシュボード: https://xxx.ngrok.io/\n")
    else:
        print("\n" + "="*50)
        print("  ✅ サーバー起動完了")
        print("="*50)
        print("\n📱 ローカルアクセス:")
        print(f"   フォーム URL: http://localhost:{port}/register")
        print(f"   ダッシュボード: http://localhost:{port}/\n")
        print("⚠️  ngrokなしで実行中のため、外部からはアクセスできません")
        print("   外部共有する場合は、ngrokをインストール後に再度実行してください\n")

    print("💡 ヒント:")
    print("   - 24時間で接続が切れます")
    print("   - [Ctrl+C] で終了します\n")

    # 終了まで待機
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 シャットダウン中...\n")
        server_process.terminate()
        if ngrok_process:
            ngrok_process.terminate()
        time.sleep(1)
        server_process.kill()
        if ngrok_process:
            ngrok_process.kill()
        print("✓ 終了しました\n")

if __name__ == '__main__':
    main()
