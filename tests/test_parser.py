import pytest
from src.parser import MarkdownTableParser


class TestMarkdownTableParser:
    
    def test_parse_simple_table(self):
        """シンプルなMarkdownテーブルの解析テスト"""
        markdown_content = """# Test Table

| Name | Age | City |
|------|-----|------|
| Alice | 25 | Tokyo |
| Bob | 30 | Osaka |
"""
        parser = MarkdownTableParser()
        result = parser.parse(markdown_content)
        
        # テーブルが1つ抽出されることを確認
        assert len(result) == 1
        
        # テーブル構造の確認
        table = result[0]
        assert table['headers'] == ['Name', 'Age', 'City']
        assert len(table['rows']) == 2
        assert table['rows'][0] == ['Alice', '25', 'Tokyo']
        assert table['rows'][1] == ['Bob', '30', 'Osaka']
    
    def test_parse_multiple_tables(self):
        """複数のMarkdownテーブルの解析テスト"""
        markdown_content = """# First Table

| Product | Price |
|---------|-------|
| Apple | 100 |
| Orange | 150 |

# Second Table

| Country | Capital |
|---------|---------|
| Japan | Tokyo |
| USA | Washington |
"""
        parser = MarkdownTableParser()
        result = parser.parse(markdown_content)
        
        # 2つのテーブルが抽出されることを確認
        assert len(result) == 2
        
        # 1つ目のテーブル
        table1 = result[0]
        assert table1['headers'] == ['Product', 'Price']
        assert table1['rows'] == [['Apple', '100'], ['Orange', '150']]
        
        # 2つ目のテーブル
        table2 = result[1]
        assert table2['headers'] == ['Country', 'Capital']
        assert table2['rows'] == [['Japan', 'Tokyo'], ['USA', 'Washington']]
    
    def test_parse_empty_content(self):
        """空のコンテンツの処理テスト"""
        parser = MarkdownTableParser()
        result = parser.parse("")
        
        assert result == []
    
    def test_parse_no_tables(self):
        """テーブルが含まれていないMarkdownの処理テスト"""
        markdown_content = """# Just a heading

This is just text with no tables.

- List item 1
- List item 2
"""
        parser = MarkdownTableParser()
        result = parser.parse(markdown_content)
        
        assert result == []
    
    def test_parse_malformed_table(self):
        """不正な形式のテーブルの処理テスト"""
        markdown_content = """# Malformed Table

| Name | Age |
|------|-----|
| Alice | 25 | Extra column |
| Bob |
"""
        parser = MarkdownTableParser()
        result = parser.parse(markdown_content)
        
        # 不正な形式でも可能な限り解析する
        assert len(result) == 1
        table = result[0]
        assert table['headers'] == ['Name', 'Age']
        # 不正な行は適切に処理される
        assert len(table['rows']) == 2
    
    def test_parse_table_with_alignment(self):
        """アライメント指定があるテーブルの処理テスト"""
        markdown_content = """# Aligned Table

| Name     | Age | Score    |
|:---------|:---:|---------:|
| Alice    | 25  | 95.5     |
| Bob      | 30  | 87.2     |
"""
        parser = MarkdownTableParser()
        result = parser.parse(markdown_content)
        
        assert len(result) == 1
        table = result[0]
        assert table['headers'] == ['Name', 'Age', 'Score']
        assert table['rows'] == [
            ['Alice', '25', '95.5'],
            ['Bob', '30', '87.2']
        ]
        # アライメント情報も保存される
        assert 'alignment' in table
        assert table['alignment'] == ['left', 'center', 'right']
    
    def test_parse_table_with_empty_cells(self):
        """空セルを含むテーブルの処理テスト"""
        markdown_content = """# Table with Empty Cells

| Name | Age | City |
|------|-----|------|
| Alice |     | Tokyo |
|       | 30  |       |
"""
        parser = MarkdownTableParser()
        result = parser.parse(markdown_content)
        
        assert len(result) == 1
        table = result[0]
        assert table['headers'] == ['Name', 'Age', 'City']
        assert table['rows'] == [
            ['Alice', '', 'Tokyo'],
            ['', '30', '']
        ]