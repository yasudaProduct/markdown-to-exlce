#!/usr/bin/env python3
"""
Web UIの簡単なテスト
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from web.app import create_app

def test_app_creation():
    """アプリケーション作成テスト"""
    app = create_app(testing=True)
    assert app is not None
    print("✅ アプリケーション作成成功")

def test_routes():
    """ルート確認テスト"""
    app = create_app(testing=True)
    with app.test_client() as client:
        # インデックスページ
        response = client.get('/')
        print(f"Index page status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response data: {response.data.decode()}")
        
        # ステータスページ
        response = client.get('/status')
        print(f"Status page: {response.status_code}")
        if response.status_code == 200:
            print(f"Status response: {response.get_json()}")

if __name__ == '__main__':
    try:
        test_app_creation()
        test_routes()
        print("🎉 基本テスト完了")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()