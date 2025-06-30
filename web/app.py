import os
import uuid
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import tempfile
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from src.integration import MarkdownToExcelProcessor


def create_app(testing=False):
    """Flaskアプリケーションファクトリ"""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # 設定
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB制限
    
    if testing:
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    else:
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # アップロードフォルダ作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # MarkdownToExcelProcessorの初期化
    app.processor = MarkdownToExcelProcessor()
    
    # ルート登録
    register_routes(app)
    
    return app


def register_routes(app):
    """ルートを登録"""
    
    @app.route('/')
    def index():
        """メインページ"""
        return render_template('index.html')

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        """単一ファイルアップロード処理"""
        if request.method == 'POST':
            # ファイルチェック
            if 'file' not in request.files:
                flash('ファイルが選択されていません', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('ファイルが選択されていません', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # ファイル保存
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                try:
                    # オプション取得
                    apply_formatting = 'apply_formatting' in request.form
                    auto_adjust_width = 'auto_adjust_width' in request.form
                    
                    # Excel変換
                    output_filename = f"{Path(filename).stem}.xlsx"
                    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{output_filename}")
                    
                    result = app.processor.process_file(
                        filepath,
                        output_path,
                        apply_formatting=apply_formatting,
                        auto_adjust_width=auto_adjust_width
                    )
                    
                    # 入力ファイル削除
                    os.remove(filepath)
                    
                    if result.success:
                        flash(f'変換成功！{result.tables_found}個のテーブルを処理しました', 'success')
                        if result.warnings:
                            for warning in result.warnings:
                                flash(f'警告: {warning}', 'warning')
                        
                        return redirect(url_for('download_file', filename=os.path.basename(output_path)))
                    else:
                        for error in result.errors:
                            flash(f'エラー: {error}', 'error')
                        return redirect(request.url)
                        
                except Exception as e:
                    flash(f'処理中にエラーが発生しました: {str(e)}', 'error')
                    # クリーンアップ
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return redirect(request.url)
            else:
                flash('Markdownファイル（.md, .markdown）のみアップロード可能です', 'error')
                return redirect(request.url)
        
        return render_template('upload.html')

    @app.route('/batch', methods=['GET', 'POST'])
    def batch_upload():
        """複数ファイル一括アップロード処理"""
        if request.method == 'POST':
            files = request.files.getlist('files')
            
            if not files or all(f.filename == '' for f in files):
                flash('ファイルが選択されていません', 'error')
                return redirect(request.url)
            
            # 有効なファイルのフィルタ
            valid_files = [f for f in files if f.filename != '' and allowed_file(f.filename)]
            
            if not valid_files:
                flash('有効なMarkdownファイルがありません', 'error')
                return redirect(request.url)
            
            try:
                # オプション取得
                apply_formatting = 'apply_formatting' in request.form
                auto_adjust_width = 'auto_adjust_width' in request.form
                
                # 一時ディレクトリ作成
                batch_id = str(uuid.uuid4())
                batch_input_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"batch_input_{batch_id}")
                batch_output_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"batch_output_{batch_id}")
                os.makedirs(batch_input_dir, exist_ok=True)
                os.makedirs(batch_output_dir, exist_ok=True)
                
                # ファイル保存
                for file in valid_files:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(batch_input_dir, filename)
                    file.save(filepath)
                
                # バッチ処理実行
                results = app.processor.process_directory(
                    batch_input_dir,
                    batch_output_dir,
                    apply_formatting=apply_formatting,
                    auto_adjust_width=auto_adjust_width
                )
                
                # 統計情報取得
                stats = app.processor.get_statistics(results)
                
                # ZIP作成
                zip_filename = f"converted_files_{batch_id}.zip"
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for result in results:
                        if result.success and os.path.exists(result.output_file):
                            zipf.write(result.output_file, os.path.basename(result.output_file))
                
                # クリーンアップ
                import shutil
                shutil.rmtree(batch_input_dir)
                shutil.rmtree(batch_output_dir)
                
                # 結果表示
                flash(f'バッチ処理完了！{stats["successful_files"]}個のファイルを変換しました', 'success')
                if stats["failed_files"] > 0:
                    flash(f'{stats["failed_files"]}個のファイルで処理に失敗しました', 'warning')
                
                return redirect(url_for('download_file', filename=zip_filename))
                
            except Exception as e:
                flash(f'バッチ処理中にエラーが発生しました: {str(e)}', 'error')
                return redirect(request.url)
        
        return render_template('batch.html')

    @app.route('/download/<filename>')
    def download_file(filename):
        """ファイルダウンロード"""
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(file_path):
                flash('ファイルが見つかりません', 'error')
                return redirect(url_for('index'))
            
            return send_file(file_path, as_attachment=True, download_name=filename)
            
        except Exception as e:
            flash(f'ダウンロードエラー: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/api/convert', methods=['POST'])
    def api_convert():
        """API エンドポイント - JSON形式での変換"""
        try:
            data = request.get_json()
            
            if not data or 'markdown_content' not in data:
                return jsonify({'error': 'markdown_content is required'}), 400
            
            markdown_content = data['markdown_content']
            apply_formatting = data.get('apply_formatting', False)
            auto_adjust_width = data.get('auto_adjust_width', False)
            
            # 一時ファイル作成
            temp_id = str(uuid.uuid4())
            temp_input = os.path.join(app.config['UPLOAD_FOLDER'], f"api_input_{temp_id}.md")
            temp_output = os.path.join(app.config['UPLOAD_FOLDER'], f"api_output_{temp_id}.xlsx")
            
            # Markdownコンテンツ保存
            with open(temp_input, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 変換実行
            result = app.processor.process_file(
                temp_input,
                temp_output,
                apply_formatting=apply_formatting,
                auto_adjust_width=auto_adjust_width
            )
            
            # 入力ファイル削除
            os.remove(temp_input)
            
            if result.success:
                # Base64エンコードしてファイル内容を返す
                import base64
                with open(temp_output, 'rb') as f:
                    excel_data = base64.b64encode(f.read()).decode('utf-8')
                
                os.remove(temp_output)
                
                return jsonify({
                    'success': True,
                    'tables_found': result.tables_found,
                    'warnings': result.warnings,
                    'excel_data': excel_data,
                    'processing_time': result.processing_time_seconds
                })
            else:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                return jsonify({
                    'success': False,
                    'errors': result.errors
                }), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/status')
    def status():
        """ヘルスチェックエンドポイント"""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'features': ['single_file', 'batch_processing', 'api']
        })

    @app.errorhandler(413)
    def too_large(e):
        """ファイルサイズ超過エラー"""
        flash('ファイルサイズが大きすぎます（16MB以下にしてください）', 'error')
        return redirect(url_for('upload_file'))

    @app.errorhandler(404)
    def not_found(e):
        """404エラー"""
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        """500エラー"""
        return render_template('500.html'), 500


def allowed_file(filename):
    """許可されたファイル拡張子かチェック"""
    ALLOWED_EXTENSIONS = {'md', 'markdown'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# アプリケーションインスタンス作成（モジュール実行時のみ）
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8080)