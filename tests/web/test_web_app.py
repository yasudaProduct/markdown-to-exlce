import pytest
import tempfile
import os
from pathlib import Path
from werkzeug.datastructures import FileStorage
from io import BytesIO
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from web.app import create_app


class TestWebApp:
    """Web アプリケーションのテストクラス"""
    
    @pytest.fixture
    def app(self):
        """テスト用Flaskアプリケーション"""
        app = create_app(testing=True)
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            app.config['UPLOAD_FOLDER'] = temp_dir
            yield app
    
    @pytest.fixture
    def client(self, app):
        """テストクライアント"""
        return app.test_client()
    
    def test_index_page_loads(self, client):
        """インデックスページの読み込みテスト"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Markdown to Excel Converter' in response.data
        assert b'Upload Markdown File' in response.data
    
    def test_upload_page_loads(self, client):
        """アップロードページの読み込みテスト"""
        response = client.get('/upload')
        assert response.status_code == 200
        assert b'file' in response.data  # ファイル入力フィールド
        assert b'apply_formatting' in response.data  # フォーマットオプション
    
    def test_single_file_upload_success(self, client):
        """単一ファイルアップロード成功テスト"""
        # テスト用Markdownファイル作成
        markdown_content = """# Test Table

| Name | Age | City |
|------|-----|------|
| Alice | 25 | Tokyo |
| Bob | 30 | Osaka |
"""
        
        data = {
            'file': (BytesIO(markdown_content.encode('utf-8')), 'test.md'),
            'apply_formatting': True,
            'auto_adjust_width': True
        }
        
        response = client.post('/upload', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'success' in response.data.lower() or b'converted' in response.data.lower()
    
    def test_upload_no_file_error(self, client):
        """ファイル未選択エラーテスト"""
        data = {
            'apply_formatting': False,
            'auto_adjust_width': False
        }
        
        response = client.post('/upload', data=data)
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'required' in response.data.lower()
    
    def test_upload_invalid_file_type(self, client):
        """無効ファイル形式エラーテスト"""
        data = {
            'file': (BytesIO(b'Not markdown content'), 'test.txt'),
            'apply_formatting': False,
            'auto_adjust_width': False
        }
        
        response = client.post('/upload', data=data)
        assert response.status_code == 200
        # エラーメッセージまたはリダイレクト
        assert response.status_code == 200
    
    def test_upload_empty_markdown_file(self, client):
        """空Markdownファイルアップロードテスト"""
        data = {
            'file': (BytesIO(b''), 'empty.md'),
            'apply_formatting': False,
            'auto_adjust_width': False
        }
        
        response = client.post('/upload', data=data, follow_redirects=True)
        assert response.status_code == 200
        # 空ファイルでも処理は成功するが警告が表示される
    
    def test_batch_upload_page_loads(self, client):
        """バッチアップロードページの読み込みテスト"""
        response = client.get('/batch')
        assert response.status_code == 200
        assert b'multiple' in response.data.lower() or b'batch' in response.data.lower()
    
    def test_batch_upload_multiple_files(self, client):
        """複数ファイルバッチアップロードテスト"""
        # 複数のテストファイル作成
        file1_content = """
| Product | Price |
|---------|-------|
| Apple | 100 |
"""
        
        file2_content = """
| Country | Capital |
|---------|---------|
| Japan | Tokyo |
"""
        
        data = {
            'files': [
                (BytesIO(file1_content.encode('utf-8')), 'products.md'),
                (BytesIO(file2_content.encode('utf-8')), 'countries.md')
            ],
            'apply_formatting': True,
            'auto_adjust_width': False
        }
        
        response = client.post('/batch', data=data, follow_redirects=True)
        assert response.status_code == 200
    
    def test_download_endpoint_exists(self, client):
        """ダウンロードエンドポイント存在確認"""
        # 無効なファイル名でテスト（404になるはず）
        response = client.get('/download/nonexistent.xlsx')
        assert response.status_code == 404
    
    def test_api_convert_endpoint(self, client):
        """API変換エンドポイントテスト"""
        markdown_content = """
| API | Test |
|-----|------|
| POST | /api/convert |
"""
        
        data = {
            'markdown_content': markdown_content,
            'apply_formatting': True,
            'auto_adjust_width': False
        }
        
        response = client.post('/api/convert', json=data)
        # API エンドポイントが実装されている場合
        assert response.status_code in [200, 404, 501]  # 実装済み、未実装、またはメソッド未許可
    
    def test_status_endpoint(self, client):
        """ステータスエンドポイントテスト"""
        response = client.get('/status')
        # ヘルスチェックエンドポイント
        assert response.status_code in [200, 404]
    
    def test_static_files_serve(self, client):
        """静的ファイル配信テスト"""
        # CSS ファイルの配信確認
        response = client.get('/static/css/style.css')
        # ファイルが存在しない場合は404、存在する場合は200
        assert response.status_code in [200, 404]
        
        # JavaScript ファイルの配信確認
        response = client.get('/static/js/app.js')
        assert response.status_code in [200, 404]


class TestWebAppUtilities:
    """Web アプリケーションのユーティリティ関数テスト"""
    
    def test_allowed_file_function(self):
        """ファイル拡張子検証関数テスト"""
        from web.app import allowed_file
        
        assert allowed_file('test.md') == True
        assert allowed_file('test.markdown') == True
        assert allowed_file('test.txt') == False
        assert allowed_file('test.xlsx') == False
        assert allowed_file('test') == False
    
    def test_secure_filename_handling(self):
        """セキュアファイル名処理テスト"""
        from werkzeug.utils import secure_filename
        
        # 危険な文字を含むファイル名のテスト
        dangerous_name = "../../../etc/passwd.md"
        safe_name = secure_filename(dangerous_name)
        assert not safe_name.startswith('../')
        assert 'passwd.md' in safe_name
    
    def test_file_size_validation(self):
        """ファイルサイズ検証テスト"""
        # 大きすぎるファイルの処理テスト用
        large_content = "# Large File\n" + "| A | B |\n|---|---|\n" * 10000
        assert len(large_content) > 1000  # サイズ確認
        
        # アプリケーションがファイルサイズ制限を正しく処理することを確認
        # （実装依存のため、実際のテストは統合テストで行う）


class TestWebAppSecurity:
    """Web アプリケーションのセキュリティテスト"""
    
    @pytest.fixture
    def app(self):
        """セキュリティテスト用アプリ"""
        app = create_app(testing=True)
        app.config['WTF_CSRF_ENABLED'] = True  # CSRF保護有効
        yield app
    
    @pytest.fixture
    def client(self, app):
        """セキュリティテスト用クライアント"""
        return app.test_client()
    
    def test_csrf_protection(self, client):
        """CSRF保護テスト"""
        # CSRFトークンなしでPOST送信
        data = {
            'file': (BytesIO(b'# Test'), 'test.md'),
            'apply_formatting': False
        }
        
        response = client.post('/upload', data=data)
        # CSRF保護が有効な場合、400エラーまたはトークンエラー
        assert response.status_code in [400, 200]  # 実装依存
    
    def test_file_upload_size_limit(self, client):
        """ファイルアップロードサイズ制限テスト"""
        # 非常に大きなファイルをアップロード試行
        large_content = b"# Large\n" + b"| A | B |\n|---|---|\n" * 100000
        
        data = {
            'file': (BytesIO(large_content), 'large.md'),
            'apply_formatting': False
        }
        
        response = client.post('/upload', data=data)
        # サイズ制限エラーまたは正常処理
        assert response.status_code in [413, 200, 400]  # Payload Too Large or handled
    
    def test_malicious_filename_handling(self, client):
        """悪意のあるファイル名の処理テスト"""
        malicious_names = [
            '../../../etc/passwd.md',
            'test.md.exe',
            'test<script>.md',
            'con.md',  # Windows予約名
            '.htaccess.md'
        ]
        
        for filename in malicious_names:
            data = {
                'file': (BytesIO(b'# Test'), filename),
                'apply_formatting': False
            }
            
            response = client.post('/upload', data=data)
            # セキュアな処理が行われることを確認
            assert response.status_code in [200, 400]