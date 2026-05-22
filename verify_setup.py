#!/usr/bin/env python3
"""
セットアップ検証スクリプト
全ての依存関係とファイルが正しく設定されているか確認します
"""
import subprocess
import sys
import os
from pathlib import Path

def check_python():
    """Python バージョン確認"""
    try:
        version = subprocess.check_output([sys.executable, '--version']).decode().strip()
        print(f"✅ Python {version}")
        return True
    except Exception as e:
        print(f"❌ Python: {e}")
        return False

def check_package(package_name, import_name=None):
    """パッケージインストール確認"""
    if import_name is None:
        import_name = package_name.split('==')[0]

    try:
        __import__(import_name)
        print(f"✅ {package_name.split('==')[0]}")
        return True
    except ImportError:
        print(f"❌ {package_name.split('==')[0]} (未インストール)")
        return False

def check_file_exists(file_path, description):
    """ファイル存在確認"""
    if Path(file_path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} (見つかりません)")
        return False

def check_ngrok():
    """ngrok インストール確認"""
    try:
        subprocess.run(['ngrok', '--version'], capture_output=True, check=True)
        print("✅ ngrok (外部公開用)")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ngrok (未インストール - ローカルのみの場合は不要)")
        return False

def check_notion_config():
    """Notion 設定確認"""
    try:
        # notion_client.py をインポートして NOTION_API_KEY が設定されているか確認
        with open('notion_client.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'NOTION_API_KEY' in content or 'NOTION_DB' in content:
                print("✅ Notion 設定ファイル存在")
                return True
            else:
                print("⚠️  Notion 設定確認が必要")
                return True  # ファイルは存在している
    except Exception as e:
        print(f"❌ Notion 設定: {e}")
        return False

def main():
    print("\n" + "="*50)
    print("  セットアップ検証")
    print("="*50 + "\n")

    base_path = Path(__file__).parent

    # 1. Python
    print("📦 Python:")
    py_ok = check_python()

    # 2. 依存パッケージ
    print("\n📦 依存パッケージ:")
    packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('anthropic', 'anthropic'),
        ('requests', 'requests'),
        ('python-dotenv', 'dotenv'),
        ('python-multipart', 'multipart'),
    ]

    packages_ok = True
    for package, import_name in packages:
        if not check_package(package, import_name):
            packages_ok = False

    # 3. 必須ファイル
    print("\n📁 必須ファイル:")
    files_ok = True
    files = [
        ('main.py', 'メイン実行ファイル'),
        ('requirements.txt', '依存パッケージリスト'),
        ('templates/index.html', 'ダッシュボード HTML'),
        ('templates/register.html', '申込フォーム HTML'),
        ('notion_client.py', 'Notion クライアント'),
        ('matching_engine.py', 'マッチングエンジン'),
    ]

    for file_path, description in files:
        if not check_file_exists(base_path / file_path, description):
            files_ok = False

    # 4. デプロイスクリプト
    print("\n🚀 デプロイスクリプト:")
    deploy_files = [
        ('deploy.py', 'Python デプロイスクリプト'),
        ('deploy.bat', 'Windows デプロイスクリプト'),
        ('quick_share.cmd', 'クイック共有ショートカット'),
    ]

    deploy_ok = True
    for file_path, description in deploy_files:
        if not check_file_exists(base_path / file_path, description):
            deploy_ok = False

    # 5. ドキュメント
    print("\n📚 ドキュメント:")
    docs_files = [
        ('README.md', 'スタートガイド'),
        ('DEPLOY_GUIDE.md', '詳細ガイド'),
        ('SHARING_CHECKLIST.md', '共有チェックリスト'),
    ]

    for file_path, description in docs_files:
        check_file_exists(base_path / file_path, description)

    # 6. 外部ツール
    print("\n🌐 外部ツール:")
    ngrok_ok = check_ngrok()

    # サマリー
    print("\n" + "="*50)
    print("  検証結果")
    print("="*50 + "\n")

    if py_ok and packages_ok and files_ok and deploy_ok:
        print("✅ セットアップ完了！\n")
        print("次のステップ:")
        print("  1. Windows ユーザー → quick_share.cmd をダブルクリック")
        print("  2. その他 → python deploy.py を実行")
        print("\n詳細は README.md を参照してください")
        return 0
    else:
        print("❌ セットアップに問題があります\n")
        print("対応方法:")
        if not py_ok:
            print("  • Python をインストール: https://www.python.org/")
        if not packages_ok:
            print("  • 依存パッケージをインストール:")
            print("    pip install -r requirements.txt")
        if not files_ok:
            print("  • 必須ファイルを確認（プロジェクトフォルダ内か確認）")
        if not deploy_ok:
            print("  • デプロイスクリプトを確認")
        if not ngrok_ok:
            print("  • ngrok をインストール（外部公開する場合）:")
            print("    https://ngrok.com/download")
        return 1

if __name__ == '__main__':
    sys.exit(main())
