"""
ポート 8000 と 8001 の両方でサーバーを起動
http://localhost:8000/ と http://localhost:8001/register にアクセス可能
"""
import subprocess
import time
import signal
import sys

def run_servers():
    """2つのサーバーを同時に起動"""
    print("\n" + "="*60)
    print("🚀 Blendy Inc. マッチングシステムを起動中...")
    print("="*60)

    # プロセス管理用リスト
    processes = []

    try:
        # サーバー1: ポート 8000
        print("\n[1/2] ポート 8000 でサーバーを起動中...")
        p1 = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            env={**dict(os.environ), "PYTHONUNBUFFERED": "1"}
        )
        processes.append(("Port 8000", p1))
        print("      ✅ http://localhost:8000/ で起動しました")

        # 少し待ってからサーバー2を起動
        time.sleep(2)

        # サーバー2: ポート 8001
        print("\n[2/2] ポート 8001 でサーバーを起動中...")
        p2 = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
            env={**dict(os.environ), "PYTHONUNBUFFERED": "1"}
        )
        processes.append(("Port 8001", p2))
        print("      ✅ http://localhost:8001/register で起動しました")

        print("\n" + "="*60)
        print("✨ 両方のサーバーが起動しました！")
        print("="*60)
        print("\n📱 アクセスしてください：")
        print("   • ダッシュボード: http://localhost:8000/")
        print("   • 申込フォーム:   http://localhost:8001/register")
        print("\n💡 ポート 8000 と 8001 は同じアプリです（どちらも利用可能）")
        print("\nサーバーを停止するには Ctrl+C を押してください...\n")

        # 全プロセスが完了するまで待機
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  {name} が停止しました")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 サーバーを停止中...")
        for name, proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"   ✅ {name} を停止しました")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"   ⚠️  {name} を強制終了しました")
        print("✅ すべてのサーバーが停止しました\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        for name, proc in processes:
            try:
                proc.kill()
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    import os
    run_servers()
