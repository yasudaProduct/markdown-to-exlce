import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from src.cli import cli, convert_file, convert_directory


class TestCLI:
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.runner = CliRunner()
    
    def test_cli_single_file_conversion(self):
        """単一ファイル変換のCLIテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # テスト用Markdownファイル作成
            input_file = Path(temp_dir) / "test.md"
            output_file = Path(temp_dir) / "output.xlsx"
            
            input_file.write_text("""# Test Table

| Name | Age | City |
|------|-----|------|
| Alice | 25 | Tokyo |
| Bob | 30 | Osaka |
""")
            
            # CLI実行
            result = self.runner.invoke(cli, [
                str(input_file),
                '--output', str(output_file)
            ])
            
            # 実行結果の確認
            assert result.exit_code == 0
            assert output_file.exists()
    
    def test_cli_directory_conversion(self):
        """ディレクトリ一括変換のCLIテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            # 複数のMarkdownファイル作成
            (input_dir / "file1.md").write_text("""
| Product | Price |
|---------|-------|
| Apple | 100 |
""")
            
            (input_dir / "file2.md").write_text("""
| Country | Capital |
|---------|---------|
| Japan | Tokyo |
""")
            
            # CLI実行
            result = self.runner.invoke(cli, [
                str(input_dir),
                '--output', str(output_dir),
                '--batch'
            ])
            
            # 実行結果の確認
            assert result.exit_code == 0
            assert (output_dir / "file1.xlsx").exists()
            assert (output_dir / "file2.xlsx").exists()
    
    def test_cli_with_formatting_options(self):
        """フォーマットオプション付きCLIテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "test.md"
            output_file = Path(temp_dir) / "formatted.xlsx"
            
            input_file.write_text("""
| Name | Score |
|------|-------|
| Alice | 95.5 |
""")
            
            # フォーマットオプション付きで実行
            result = self.runner.invoke(cli, [
                str(input_file),
                '--output', str(output_file),
                '--format',
                '--auto-width'
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
    
    def test_cli_help_command(self):
        """ヘルプコマンドのテスト"""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Convert Markdown files to Excel format' in result.output
        assert '--output' in result.output
        assert '--format' in result.output
        assert '--batch' in result.output
    
    def test_cli_invalid_input_file(self):
        """存在しない入力ファイルのエラーハンドリングテスト"""
        result = self.runner.invoke(cli, [
            '/nonexistent/path/file.md',
            '--output', 'output.xlsx'
        ])
        
        assert result.exit_code != 0
        assert 'does not exist' in result.output or 'not found' in result.output
    
    def test_cli_invalid_output_directory(self):
        """存在しない出力ディレクトリのエラーハンドリングテスト"""
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp_file:
            tmp_file.write(b"| Name | Age |\n|------|-----|\n| Alice | 25 |")
            tmp_file.flush()
            
            try:
                result = self.runner.invoke(cli, [
                    tmp_file.name,
                    '--output', '/nonexistent/directory/output.xlsx'
                ])
                
                assert result.exit_code != 0
            finally:
                os.unlink(tmp_file.name)
    
    def test_cli_with_verbose_output(self):
        """詳細出力オプションのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "test.md"
            output_file = Path(temp_dir) / "output.xlsx"
            
            input_file.write_text("""
| Name | Age |
|------|-----|
| Alice | 25 |
""")
            
            result = self.runner.invoke(cli, [
                str(input_file),
                '--output', str(output_file),
                '--verbose'
            ])
            
            assert result.exit_code == 0
            assert 'Processing' in result.output or 'Converting' in result.output
    
    def test_cli_default_output_filename(self):
        """デフォルト出力ファイル名のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "sample.md"
            input_file.write_text("""
| Name | Age |
|------|-----|
| Alice | 25 |
""")
            
            # 出力ファイル名を指定せずに実行
            with patch('os.getcwd', return_value=temp_dir):
                result = self.runner.invoke(cli, [str(input_file)])
            
            assert result.exit_code == 0
            # sample.md -> sample.xlsx に変換されることを確認
            expected_output = Path(temp_dir) / "sample.xlsx"
            assert expected_output.exists()


class TestCLIUtilityFunctions:
    
    def test_convert_file_function(self):
        """convert_file関数の単体テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "test.md"
            output_file = Path(temp_dir) / "output.xlsx"
            
            input_file.write_text("""
| Product | Price |
|---------|-------|
| Apple | 100 |
| Orange | 150 |
""")
            
            # convert_file関数を直接呼び出し
            convert_file(
                str(input_file), 
                str(output_file),
                apply_formatting=True,
                auto_adjust_width=True,
                verbose=True
            )
            
            assert output_file.exists()
    
    def test_convert_directory_function(self):
        """convert_directory関数の単体テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            # テストファイル作成
            (input_dir / "test1.md").write_text("| A | B |\n|---|---|\n| 1 | 2 |")
            (input_dir / "test2.md").write_text("| X | Y |\n|---|---|\n| 3 | 4 |")
            (input_dir / "readme.txt").write_text("Not a markdown file")
            
            # convert_directory関数を直接呼び出し
            convert_directory(
                str(input_dir),
                str(output_dir),
                apply_formatting=False,
                auto_adjust_width=False,
                verbose=True
            )
            
            # Markdownファイルのみが変換されることを確認
            assert (output_dir / "test1.xlsx").exists()
            assert (output_dir / "test2.xlsx").exists()
            assert not (output_dir / "readme.xlsx").exists()
    
    def test_empty_markdown_file_handling(self):
        """空のMarkdownファイルの処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "empty.md"
            output_file = Path(temp_dir) / "empty.xlsx"
            
            input_file.write_text("")  # 空ファイル
            
            convert_file(
                str(input_file),
                str(output_file),
                apply_formatting=False,
                auto_adjust_width=False,
                verbose=False
            )
            
            # 空のExcelファイルが作成されることを確認
            assert output_file.exists()
    
    def test_markdown_file_without_tables(self):
        """テーブルがないMarkdownファイルの処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "no_tables.md"
            output_file = Path(temp_dir) / "no_tables.xlsx"
            
            input_file.write_text("""
# Just a heading

This is just regular text without any tables.

- List item 1
- List item 2
""")
            
            convert_file(
                str(input_file),
                str(output_file),
                apply_formatting=False,
                auto_adjust_width=False,
                verbose=False
            )
            
            # 空のExcelファイルが作成されることを確認
            assert output_file.exists()