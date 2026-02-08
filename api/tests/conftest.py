"""pytest設定ファイル"""

import os
import sys
from pathlib import Path

# apiディレクトリをPythonパスに追加
api_server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_server_dir))

# 環境変数でデフォルトロケールを日本語に設定
os.environ["ANALYSISAPP_LOCALE"] = "ja"
