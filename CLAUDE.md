# CLAUDE.md

このファイルはクロードコード(claude.ai/code)がこのリポジトリにあるコードで作業する際のガイダンスを提供します。

## プロジェクト概要

これはマークダウンからエクセルへの変換ツールのプロジェクトです。現在リポジトリは空で、初期設定が必要です。

## プロジェクトの目的

MarkdownファイルをExcel形式に変換する：
- MarkdownテーブルからExcelスプレッドシートへ
- 構造化されたMarkdownコンテンツからExcelワークブックへ

## Development Philosophy

### Test-Driven Development (TDD)

- 原則としてテスト駆動開発（TDD）で進める
- 期待される入出力に基づき、まずテストを作成する
- 実装コードは書かず、テストのみを用意する
- テストを実行し、失敗を確認する
- テストが正しいことを確認できた段階でコミットする
- その後、テストをパスさせる実装を進める
- 実装中はテストを変更せず、コードを修正し続ける
- すべてのテストが通過するまで繰り返す

## 開発環境セットアップ

```bash
# 依存関係インストール
pip install -r requirements.txt

# 開発用依存関係インストール
pip install -e ".[dev]"

# テスト実行
pytest

# カバレッジ付きテスト実行
pytest --cov=src --cov-report=html

# コード整形
black src/ tests/

# 型チェック
mypy src/

# リント
flake8 src/ tests/
```

## プロジェクト構造

```
src/
├── __init__.py
├── cli.py              # CLIエントリーポイント
├── parser.py           # Markdown解析
├── converter.py        # Excel変換
└── utils.py           # ユーティリティ

tests/
├── __init__.py
├── test_parser.py      # パーサーテスト
├── test_converter.py   # コンバーターテスト
└── fixtures/          # テスト用データ
    └── sample_table.md
```