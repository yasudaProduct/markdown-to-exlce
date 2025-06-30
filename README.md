# Markdown to Excel Converter

Markdownファイル内のテーブルをExcel形式に変換するPythonツールです。

## 📋 概要

このツールは、Markdownファイル内のテーブルを解析し、Excelファイル（.xlsx）として出力します。複数のテーブルが含まれている場合、それぞれを別々のシートに配置します。

## ✨ 主な機能

- Markdownテーブルの自動検出と解析
- 複数テーブルの処理（各テーブルを別シートに配置）
- テーブルアライメント情報の保持
- 空セルの適切な処理
- コマンドラインインターフェース（CLI）対応

## 🚀 インストール

### 前提条件
- Python 3.8以上

### インストール方法

1. リポジトリをクローン
```bash
git clone <repository-url>
cd markdown-to-excel
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

または、開発用の依存関係も含めてインストール：
```bash
pip install -e ".[dev]"
```

## 📖 使い方

### コマンドラインでの使用

```bash
# 基本的な使用方法
python -m src.cli input.md output.xlsx

# ヘルプの表示
python -m src.cli --help
```

### プログラムでの使用例

```python
from src.parser import MarkdownTableParser
import pandas as pd

# Markdownファイルを読み込み
with open('input.md', 'r', encoding='utf-8') as f:
    markdown_content = f.read()

# テーブルを解析
parser = MarkdownTableParser()
tables = parser.parse(markdown_content)

# Excelファイルに出力
with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    for i, table in enumerate(tables):
        df = pd.DataFrame(table['rows'], columns=table['headers'])
        sheet_name = f'Table_{i+1}'
        df.to_excel(writer, sheet_name=sheet_name, index=False)
```

## 📝 対応Markdownテーブル例

### 基本的なテーブル
```markdown
| Name | Age | City |
|------|-----|------|
| Alice | 25 | Tokyo |
| Bob | 30 | Osaka |
```

### アライメント指定付きテーブル
```markdown
| Name     | Age | Score    |
|:---------|:---:|---------:|
| Alice    | 25  | 95.5     |
| Bob      | 30  | 87.2     |
```
- `:---` : 左揃え
- `:---:` : 中央揃え
- `---:` : 右揃え

## 🧪 テスト

テストを実行するには：

```bash
pytest
```

カバレッジ付きでテスト実行：
```bash
pytest --cov=src --cov-report=html
```

## 📦 依存パッケージ

- `pandas>=2.1.0` - データ処理とExcel出力
- `openpyxl>=3.1.2` - Excelファイルの読み書き
- `markdown>=3.5.1` - Markdown解析
- `click>=8.1.7` - コマンドラインインターフェース

### 開発用
- `pytest` / `pytest-cov` / `black` / `flake8` / `mypy`

## 🏗️ ディレクトリ構成

```
markdown-to-excel/
├── src/
│   ├── __init__.py
│   ├── parser.py          # Markdownテーブル解析クラス
│   └── cli.py             # コマンドラインインターフェース
├── tests/
│   ├── __init__.py
│   ├── test_parser.py     # パーサーのテスト
│   └── fixtures/          # テスト用ファイル
├── pyproject.toml         # プロジェクト設定
├── requirements.txt       # 依存関係
└── README.md              # このファイル
```

## 🤝 貢献方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/your-feature`)
3. 変更をコミット (`git commit -m 'Add your feature'`)
4. ブランチにプッシュ (`git push origin feature/your-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🐛 問題の報告

バグや機能要望はGitHubのIssuesページでご報告ください。 