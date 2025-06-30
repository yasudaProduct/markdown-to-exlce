import click
import os
from pathlib import Path
from typing import Optional
from .parser import MarkdownTableParser
from .converter import ExcelConverter


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='出力ファイルまたはディレクトリのパス'
)
@click.option(
    '--format', 'apply_formatting',
    is_flag=True,
    help='Excelファイルにフォーマット（太字ヘッダー、アライメント）を適用'
)
@click.option(
    '--auto-width',
    is_flag=True,
    help='列幅の自動調整を有効にする'
)
@click.option(
    '--batch',
    is_flag=True,
    help='ディレクトリ内のすべてのMarkdownファイルを一括変換'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='詳細な実行ログを出力'
)
def cli(input_path: str, output: Optional[str], apply_formatting: bool, 
        auto_width: bool, batch: bool, verbose: bool):
    """
    Convert Markdown files to Excel format.
    
    INPUT_PATH: Path to input Markdown file or directory
    """
    input_path_obj = Path(input_path)
    
    try:
        if batch or input_path_obj.is_dir():
            # ディレクトリ一括変換
            if not input_path_obj.is_dir():
                click.echo("Error: --batch option requires a directory input", err=True)
                raise click.Abort()
            
            output_dir = Path(output) if output else input_path_obj
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
            
            convert_directory(
                str(input_path_obj),
                str(output_dir),
                apply_formatting,
                auto_width,
                verbose
            )
        else:
            # 単一ファイル変換
            if output:
                output_file = Path(output)
            else:
                # デフォルト出力ファイル名: input.md -> input.xlsx
                output_file = input_path_obj.with_suffix('.xlsx')
            
            convert_file(
                str(input_path_obj),
                str(output_file),
                apply_formatting,
                auto_width,
                verbose
            )
        
        if verbose:
            click.echo("✅ 変換が完了しました")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


def convert_file(input_file: str, output_file: str, apply_formatting: bool,
                auto_adjust_width: bool, verbose: bool) -> None:
    """
    単一のMarkdownファイルをExcelに変換する
    
    Args:
        input_file: 入力Markdownファイルパス
        output_file: 出力Excelファイルパス
        apply_formatting: フォーマット適用フラグ
        auto_adjust_width: 列幅自動調整フラグ
        verbose: 詳細出力フラグ
    """
    if verbose:
        click.echo(f"Processing: {input_file}")
    
    # 入力ファイルの存在確認
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file does not exist: {input_file}")
    
    # 出力ディレクトリの作成
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ファイル読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Markdownテーブル解析
    parser = MarkdownTableParser()
    tables_data = parser.parse(markdown_content)
    
    if verbose:
        table_count = len(tables_data)
        if table_count == 0:
            click.echo("  ⚠️  テーブルが見つかりませんでした")
        else:
            click.echo(f"  📊 {table_count}個のテーブルを検出")
    
    # Excel変換
    converter = ExcelConverter()
    converter.convert_to_excel(
        tables_data,
        output_file,
        apply_formatting=apply_formatting,
        auto_adjust_width=auto_adjust_width
    )
    
    if verbose:
        click.echo(f"  💾 出力: {output_file}")


def convert_directory(input_dir: str, output_dir: str, apply_formatting: bool,
                     auto_adjust_width: bool, verbose: bool) -> None:
    """
    ディレクトリ内のMarkdownファイルを一括変換する
    
    Args:
        input_dir: 入力ディレクトリパス
        output_dir: 出力ディレクトリパス
        apply_formatting: フォーマット適用フラグ
        auto_adjust_width: 列幅自動調整フラグ
        verbose: 詳細出力フラグ
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 出力ディレクトリ作成
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Markdownファイルを検索
    markdown_files = list(input_path.glob('*.md'))
    
    if verbose:
        click.echo(f"📁 ディレクトリ処理: {input_dir}")
        click.echo(f"   {len(markdown_files)}個のMarkdownファイルを発見")
    
    if not markdown_files:
        if verbose:
            click.echo("  ⚠️  Markdownファイルが見つかりませんでした")
        return
    
    # 各ファイルを変換
    for md_file in markdown_files:
        output_file = output_path / f"{md_file.stem}.xlsx"
        
        try:
            convert_file(
                str(md_file),
                str(output_file),
                apply_formatting,
                auto_adjust_width,
                verbose
            )
        except Exception as e:
            if verbose:
                click.echo(f"  ❌ {md_file.name}: {str(e)}")
            continue
    
    if verbose:
        click.echo(f"📁 ディレクトリ処理完了: {len(markdown_files)}ファイル")


def main():
    """エントリーポイント"""
    cli()


if __name__ == '__main__':
    main()