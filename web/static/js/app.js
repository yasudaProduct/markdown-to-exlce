// メインJavaScriptファイル
document.addEventListener('DOMContentLoaded', function() {
    
    // グローバル設定
    const config = {
        maxFileSize: 16 * 1024 * 1024, // 16MB
        allowedExtensions: ['.md', '.markdown'],
        apiEndpoint: '/api/convert'
    };

    // ユーティリティ関数
    const utils = {
        // ファイルサイズフォーマット
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        // ファイル拡張子チェック
        isAllowedFile: function(filename) {
            const ext = '.' + filename.split('.').pop().toLowerCase();
            return config.allowedExtensions.includes(ext);
        },

        // ファイルサイズチェック
        isValidFileSize: function(size) {
            return size <= config.maxFileSize;
        },

        // セキュアファイル名生成
        generateSecureFilename: function(originalName) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const safeName = originalName.replace(/[^a-zA-Z0-9.-]/g, '_');
            return `${timestamp}_${safeName}`;
        },

        // 通知表示
        showNotification: function(message, type = 'info') {
            const alertClass = {
                'success': 'alert-success',
                'error': 'alert-danger',
                'warning': 'alert-warning',
                'info': 'alert-info'
            }[type] || 'alert-info';

            const icon = {
                'success': 'fa-check-circle',
                'error': 'fa-exclamation-triangle',
                'warning': 'fa-exclamation-circle',
                'info': 'fa-info-circle'
            }[type] || 'fa-info-circle';

            const alertHTML = `
                <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    <i class="fas ${icon} me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;

            // 既存のアラートの下に追加
            const container = document.querySelector('.container');
            const existingAlerts = container.querySelector('.alert');
            if (existingAlerts) {
                existingAlerts.insertAdjacentHTML('afterend', alertHTML);
            } else {
                container.insertAdjacentHTML('afterbegin', alertHTML);
            }

            // 5秒後に自動削除
            setTimeout(() => {
                const alert = container.querySelector(`.${alertClass}:last-of-type`);
                if (alert) {
                    alert.remove();
                }
            }, 5000);
        },

        // APIリクエスト送信
        sendApiRequest: async function(data) {
            try {
                const response = await fetch(config.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                return await response.json();
            } catch (error) {
                throw new Error('API通信に失敗しました: ' + error.message);
            }
        }
    };

    // ファイルアップロード処理
    const fileUpload = {
        // ドラッグ&ドロップ初期化
        initDragAndDrop: function(dropZone, fileInput, callback) {
            if (!dropZone) return;

            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, function() {
                    dropZone.classList.add('dragover');
                });
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, function() {
                    dropZone.classList.remove('dragover');
                });
            });

            dropZone.addEventListener('drop', function(e) {
                const files = Array.from(e.dataTransfer.files);
                const validFiles = files.filter(file => 
                    utils.isAllowedFile(file.name) && utils.isValidFileSize(file.size)
                );

                if (validFiles.length === 0) {
                    utils.showNotification('有効なMarkdownファイルがありません', 'error');
                    return;
                }

                if (validFiles.length !== files.length) {
                    utils.showNotification('一部のファイルが除外されました（形式またはサイズエラー）', 'warning');
                }

                // ファイル入力を更新
                const dt = new DataTransfer();
                validFiles.forEach(file => dt.items.add(file));
                fileInput.files = dt.files;

                if (callback) callback(validFiles);
            });
        },

        // ファイル検証
        validateFile: function(file) {
            const errors = [];

            if (!utils.isAllowedFile(file.name)) {
                errors.push('許可されていないファイル形式です');
            }

            if (!utils.isValidFileSize(file.size)) {
                errors.push(`ファイルサイズが大きすぎます（最大: ${utils.formatFileSize(config.maxFileSize)}）`);
            }

            if (file.size === 0) {
                errors.push('ファイルが空です');
            }

            return {
                isValid: errors.length === 0,
                errors: errors
            };
        },

        // ファイルプレビュー生成
        generatePreview: function(file, callback) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const content = e.target.result;
                const preview = content.length > 1000 ? 
                    content.substring(0, 1000) + '\n...(続きあり)' : content;
                callback(preview);
            };
            reader.onerror = function() {
                callback('ファイルの読み込みに失敗しました');
            };
            reader.readAsText(file);
        }
    };

    // プログレスバー制御
    const progress = {
        create: function(container) {
            const progressHTML = `
                <div class="mt-3" id="progressContainer">
                    <div class="d-flex justify-content-between mb-1">
                        <span>処理進行状況</span>
                        <span id="progressText">0%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%" id="progressBar"></div>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', progressHTML);
        },

        update: function(percentage) {
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            
            if (progressBar && progressText) {
                progressBar.style.width = percentage + '%';
                progressText.textContent = Math.round(percentage) + '%';
            }
        },

        complete: function() {
            this.update(100);
            setTimeout(() => {
                const container = document.getElementById('progressContainer');
                if (container) {
                    container.remove();
                }
            }, 1000);
        },

        remove: function() {
            const container = document.getElementById('progressContainer');
            if (container) {
                container.remove();
            }
        }
    };

    // フォーム送信処理
    const formHandler = {
        // 送信ボタン状態制御
        setSubmitButtonState: function(button, loading = false) {
            if (loading) {
                button.disabled = true;
                button.dataset.originalText = button.innerHTML;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>処理中...';
            } else {
                button.disabled = false;
                button.innerHTML = button.dataset.originalText || button.innerHTML;
            }
        },

        // フォームリセット
        resetForm: function(form) {
            form.reset();
            const previewCards = form.querySelectorAll('[id*="preview"], [id*="fileList"]');
            previewCards.forEach(card => card.style.display = 'none');
        }
    };

    // エラーハンドリング
    const errorHandler = {
        // 一般的なエラー処理
        handleError: function(error, context = '') {
            console.error('Error in ' + context + ':', error);
            
            let message = 'エラーが発生しました';
            if (error.message) {
                message += ': ' + error.message;
            }
            
            utils.showNotification(message, 'error');
        },

        // ネットワークエラー処理
        handleNetworkError: function(error) {
            utils.showNotification('ネットワークエラーが発生しました。接続を確認してください。', 'error');
        },

        // ファイルエラー処理
        handleFileError: function(filename, error) {
            utils.showNotification(`ファイル "${filename}" の処理でエラー: ${error}`, 'error');
        }
    };

    // 初期化処理
    const init = function() {
        // ツールチップ初期化
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // 共通ドラッグ&ドロップ処理
        const dropZones = document.querySelectorAll('#dropZone');
        dropZones.forEach(dropZone => {
            const fileInput = dropZone.closest('form')?.querySelector('input[type="file"]');
            if (fileInput) {
                fileUpload.initDragAndDrop(dropZone, fileInput);
            }
        });

        // フォーム送信時の確認ダイアログ
        const forms = document.querySelectorAll('form[method="POST"]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const fileInput = form.querySelector('input[type="file"]');
                if (fileInput && fileInput.files.length === 0) {
                    e.preventDefault();
                    utils.showNotification('ファイルを選択してください', 'warning');
                }
            });
        });

        // 自動フォーカス
        const autoFocusElement = document.querySelector('[autofocus]');
        if (autoFocusElement) {
            autoFocusElement.focus();
        }

        console.log('Markdown to Excel Converter Web UI initialized');
    };

    // グローバルオブジェクトとして公開
    window.MarkdownToExcel = {
        utils: utils,
        fileUpload: fileUpload,
        progress: progress,
        formHandler: formHandler,
        errorHandler: errorHandler,
        config: config
    };

    // 初期化実行
    init();
});

// サービスワーカー登録（PWA対応の基礎）
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // 将来的にサービスワーカーを実装する場合
        // navigator.serviceWorker.register('/sw.js');
    });
}