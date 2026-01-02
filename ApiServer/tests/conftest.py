"""pytest設定ファイル"""
import sys
from pathlib import Path

# ApiServerディレクトリをPythonパスに追加
api_server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_server_dir))
