from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import os
from .parser import MarkdownTableParser
from .converter import ExcelConverter


@dataclass
class ProcessingResult:
    """処理結果を表すデータクラス"""
    success: bool
    input_file: str
    output_file: str
    tables_found: int
    errors: List[str]
    warnings: List[str]
    processing_time_seconds: Optional[float] = None


class MarkdownToExcelProcessor:
    """
    MarkdownからExcelへの変換を統合的に処理するクラス
    Parser + Converter + エラーハンドリングを組み合わせた高レベルAPI
    """
    
    def __init__(self):
        self.parser = MarkdownTableParser()
        self.converter = ExcelConverter()
    
    def process_file(
        self,
        input_file: str,
        output_file: str,
        apply_formatting: bool = False,
        auto_adjust_width: bool = False
    ) -> ProcessingResult:
        """
        単一ファイルのエンドツーエンド変換処理
        
        Args:
            input_file: 入力Markdownファイルパス
            output_file: 出力Excelファイルパス
            apply_formatting: フォーマット適用フラグ
            auto_adjust_width: 列幅自動調整フラグ
            
        Returns:
            ProcessingResult: 処理結果
        """
        errors = []
        warnings = []
        tables_found = 0
        
        import time
        start_time = time.time()
        
        try:
            # 入力ファイルの存在確認
            if not os.path.exists(input_file):
                errors.append(f"Input file does not exist: {input_file}")
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    tables_found=0,
                    errors=errors,
                    warnings=warnings,
                    processing_time_seconds=time.time() - start_time
                )
            
            # 出力ディレクトリの作成
            output_path = Path(output_file)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Failed to create output directory: {str(e)}")
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    tables_found=0,
                    errors=errors,
                    warnings=warnings,
                    processing_time_seconds=time.time() - start_time
                )
            
            # ファイル読み込み
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
            except Exception as e:
                errors.append(f"Failed to read input file: {str(e)}")
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    tables_found=0,
                    errors=errors,
                    warnings=warnings,
                    processing_time_seconds=time.time() - start_time
                )
            
            # 空ファイルの処理
            if not markdown_content.strip():
                warnings.append("Input file is empty")
            
            # Markdownテーブル解析
            try:
                tables_data = self.parser.parse(markdown_content)
                tables_found = len(tables_data)
                
                if tables_found == 0:
                    warnings.append("No tables found in the input file")
                    
            except Exception as e:
                errors.append(f"Failed to parse markdown tables: {str(e)}")
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    tables_found=0,
                    errors=errors,
                    warnings=warnings,
                    processing_time_seconds=time.time() - start_time
                )
            
            # Excel変換
            try:
                self.converter.convert_to_excel(
                    tables_data,
                    output_file,
                    apply_formatting=apply_formatting,
                    auto_adjust_width=auto_adjust_width
                )
            except Exception as e:
                errors.append(f"Failed to convert to Excel: {str(e)}")
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    tables_found=tables_found,
                    errors=errors,
                    warnings=warnings,
                    processing_time_seconds=time.time() - start_time
                )
            
            # 出力ファイルの確認
            if not os.path.exists(output_file):
                errors.append("Excel file was not created successfully")
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    tables_found=tables_found,
                    errors=errors,
                    warnings=warnings,
                    processing_time_seconds=time.time() - start_time
                )
            
            # 成功
            return ProcessingResult(
                success=True,
                input_file=input_file,
                output_file=output_file,
                tables_found=tables_found,
                errors=errors,
                warnings=warnings,
                processing_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return ProcessingResult(
                success=False,
                input_file=input_file,
                output_file=output_file,
                tables_found=0,
                errors=errors,
                warnings=warnings,
                processing_time_seconds=time.time() - start_time
            )
    
    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        apply_formatting: bool = False,
        auto_adjust_width: bool = False
    ) -> List[ProcessingResult]:
        """
        ディレクトリ内のMarkdownファイルを一括変換
        
        Args:
            input_dir: 入力ディレクトリパス
            output_dir: 出力ディレクトリパス
            apply_formatting: フォーマット適用フラグ
            auto_adjust_width: 列幅自動調整フラグ
            
        Returns:
            List[ProcessingResult]: 各ファイルの処理結果リスト
        """
        results = []
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # 出力ディレクトリ作成
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # ディレクトリ作成失敗の場合は単一の失敗結果を返す
            return [ProcessingResult(
                success=False,
                input_file=input_dir,
                output_file=output_dir,
                tables_found=0,
                errors=[f"Failed to create output directory: {str(e)}"],
                warnings=[]
            )]
        
        # Markdownファイルを検索
        try:
            markdown_files = list(input_path.glob('*.md'))
        except Exception as e:
            return [ProcessingResult(
                success=False,
                input_file=input_dir,
                output_file=output_dir,
                tables_found=0,
                errors=[f"Failed to scan input directory: {str(e)}"],
                warnings=[]
            )]
        
        if not markdown_files:
            return [ProcessingResult(
                success=True,
                input_file=input_dir,
                output_file=output_dir,
                tables_found=0,
                errors=[],
                warnings=["No Markdown files found in input directory"]
            )]
        
        # 各ファイルを変換
        for md_file in markdown_files:
            output_file = output_path / f"{md_file.stem}.xlsx"
            
            result = self.process_file(
                str(md_file),
                str(output_file),
                apply_formatting,
                auto_adjust_width
            )
            
            results.append(result)
        
        return results
    
    def validate_input(self, file_path: str) -> List[str]:
        """
        入力ファイルの事前検証
        
        Args:
            file_path: 検証対象ファイルパス
            
        Returns:
            List[str]: 検証エラーのリスト（空の場合は問題なし）
        """
        errors = []
        
        # ファイル存在確認
        if not os.path.exists(file_path):
            errors.append(f"File does not exist: {file_path}")
            return errors
        
        # ファイルサイズ確認
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                errors.append("File is empty")
            elif file_size > 100 * 1024 * 1024:  # 100MB制限
                errors.append("File is too large (> 100MB)")
        except Exception as e:
            errors.append(f"Failed to check file size: {str(e)}")
        
        # ファイル読み取り可能性確認
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 先頭1KBだけ読んで確認
                f.read(1024)
        except UnicodeDecodeError:
            errors.append("File is not valid UTF-8 text")
        except Exception as e:
            errors.append(f"Failed to read file: {str(e)}")
        
        return errors
    
    def get_statistics(self, results: List[ProcessingResult]) -> dict:
        """
        処理結果の統計情報を取得
        
        Args:
            results: 処理結果のリスト
            
        Returns:
            dict: 統計情報
        """
        if not results:
            return {
                'total_files': 0,
                'successful_files': 0,
                'failed_files': 0,
                'total_tables': 0,
                'total_processing_time': 0.0,
                'average_processing_time': 0.0
            }
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        total_tables = sum(r.tables_found for r in successful_results)
        
        processing_times = [
            r.processing_time_seconds for r in results 
            if r.processing_time_seconds is not None
        ]
        total_processing_time = sum(processing_times)
        average_processing_time = (
            total_processing_time / len(processing_times) 
            if processing_times else 0.0
        )
        
        return {
            'total_files': len(results),
            'successful_files': len(successful_results),
            'failed_files': len(failed_results),
            'total_tables': total_tables,
            'total_processing_time': total_processing_time,
            'average_processing_time': average_processing_time
        }