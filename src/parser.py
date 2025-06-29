import re
from typing import List, Dict, Any


class MarkdownTableParser:
    """Markdownテーブルを解析するクラス"""
    
    def __init__(self):
        # テーブル行を識別する正規表現パターン
        self.table_row_pattern = re.compile(r'^\s*\|.*\|\s*$')
        self.separator_pattern = re.compile(r'^\s*\|[\s\-\:\|]*\|\s*$')
    
    def parse(self, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Markdownコンテンツからテーブルを抽出して解析する
        
        Args:
            markdown_content: 解析対象のMarkdownテキスト
            
        Returns:
            テーブル情報のリスト。各テーブルは以下の構造:
            {
                'headers': List[str],  # カラムヘッダー
                'rows': List[List[str]],  # データ行
                'alignment': List[str]  # アライメント情報
            }
        """
        if not markdown_content.strip():
            return []
        
        lines = markdown_content.split('\n')
        tables = []
        i = 0
        
        while i < len(lines):
            table_data = self._extract_table_at_position(lines, i)
            if table_data:
                tables.append(table_data['table'])
                i = table_data['next_index']
            else:
                i += 1
        
        return tables
    
    def _extract_table_at_position(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """
        指定位置からテーブルを抽出する
        
        Args:
            lines: 全行のリスト
            start_index: 開始位置
            
        Returns:
            テーブルデータと次のインデックス、またはNone
        """
        if start_index >= len(lines):
            return None
        
        # 現在行がテーブル行かチェック
        current_line = lines[start_index]
        if not self._is_table_row(current_line):
            return None
        
        # ヘッダー行を解析
        headers = self._parse_table_row(current_line)
        
        # セパレーター行を探す
        separator_index = start_index + 1
        if separator_index >= len(lines):
            return None
        
        separator_line = lines[separator_index]
        if not self._is_separator_row(separator_line):
            return None
        
        # アライメント情報を抽出
        alignment = self._parse_alignment(separator_line)
        
        # データ行を収集
        rows = []
        current_index = separator_index + 1
        
        while current_index < len(lines):
            line = lines[current_index]
            if self._is_table_row(line):
                row_data = self._parse_table_row(line)
                # ヘッダー数に合わせて行データを調整
                row_data = self._normalize_row_data(row_data, len(headers))
                rows.append(row_data)
                current_index += 1
            else:
                break
        
        return {
            'table': {
                'headers': headers,
                'rows': rows,
                'alignment': alignment
            },
            'next_index': current_index
        }
    
    def _is_table_row(self, line: str) -> bool:
        """行がテーブル行かどうかを判定"""
        return bool(self.table_row_pattern.match(line))
    
    def _is_separator_row(self, line: str) -> bool:
        """行がセパレーター行かどうかを判定"""
        return bool(self.separator_pattern.match(line))
    
    def _parse_table_row(self, line: str) -> List[str]:
        """テーブル行からセルデータを抽出"""
        # 前後の空白とパイプを除去
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # セルを分割して前後の空白を除去
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def _parse_alignment(self, separator_line: str) -> List[str]:
        """セパレーター行からアライメント情報を抽出"""
        # セパレーター行からセルを抽出
        cells = self._parse_table_row(separator_line)
        alignment = []
        
        for cell in cells:
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignment.append('center')
            elif cell.endswith(':'):
                alignment.append('right')
            else:
                alignment.append('left')
        
        return alignment
    
    def _normalize_row_data(self, row_data: List[str], expected_columns: int) -> List[str]:
        """行データをヘッダー数に合わせて正規化"""
        if len(row_data) == expected_columns:
            return row_data
        elif len(row_data) < expected_columns:
            # 不足分を空文字で埋める
            return row_data + [''] * (expected_columns - len(row_data))
        else:
            # 余分な列は切り捨て
            return row_data[:expected_columns]