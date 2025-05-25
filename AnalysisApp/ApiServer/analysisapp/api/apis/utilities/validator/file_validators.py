from rest_framework import status
from django.utils.translation import gettext as _
from ..create_response import create_error_response
from typing import Optional, Dict, Any, Tuple, List
import magic
import mimetypes


class FileValidationError(Exception):
    """
    ファイルバリデーション専用の例外
    """
    def __init__(self,
                 message: str,
                 status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class FileValidator:
    """
    ファイルバリデーションを行うクラス
    """
    def __init__(self,
                 max_size: int = 10 * 1024 * 1024,  # 10MB
                 allowed_extensions: Tuple[str] = None,
                 allowed_mime_types: List[str] = None):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions or ()
        self.allowed_mime_types = allowed_mime_types or []

    def validate_request(self, request) -> Optional[Dict[str, Any]]:
        """
        リクエストのファイルバリデーションを実行

        Args:
            request: DRFのリクエストオブジェクト

        Returns:
            None: バリデーション成功
            Dict: エラーレスポンス（バリデーション失敗時）
        """
        try:
            self._validate_file_presence(request)
            uploaded_file = request.FILES['file']
            self._validate_file_size(uploaded_file)
            self._validate_file_extension(uploaded_file)
            self._validate_file_mime_type(uploaded_file)
            return None

        except FileValidationError as e:
            return create_error_response(
                e.status_code,
                e.message,
                request
            )

    def _validate_file_presence(self, request):
        """
        ファイルの存在チェック
        """
        if 'file' not in request.data:
            message = _("No file uploaded.")
            raise FileValidationError(
                message,
                status.HTTP_400_BAD_REQUEST
            )

    def _validate_file_size(self, uploaded_file):
        """
        ファイルサイズのチェック
        """
        if uploaded_file.size > self.max_size:
            size_mb = self.max_size / (1024 * 1024)
            message = _(
                f"File size exceeds maximum limit of {size_mb}MB."
                )
            raise FileValidationError(
                message,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

    def _validate_file_extension(self, uploaded_file):
        """
        ファイル拡張子のチェック
        """
        if not uploaded_file.name.lower().endswith(self.allowed_extensions):
            extensions = ', '.join(self.allowed_extensions)
            message = _(
                f"Uploaded file is not a {extensions} file.")
            raise FileValidationError(
                message,
                status.HTTP_400_BAD_REQUEST
            )

    def _validate_file_mime_type(self, uploaded_file):
        """
        MIMEタイプのチェック
        """
        # ファイル内容からMIMEタイプを判定
        uploaded_file.seek(0)
        file_content = uploaded_file.read(1024)  # 最初の1KBを読み取り
        uploaded_file.seek(0)  # ファイルポインタをリセット

        try:
            detected_mime = magic.from_buffer(file_content, mime=True)
        except Exception:
            # python-magicが利用できない場合はファイル名から推測
            detected_mime, _encoding = mimetypes.guess_type(uploaded_file.name)

        if detected_mime not in self.allowed_mime_types:
            mime_types = ', '.join(self.allowed_mime_types)
            raise FileValidationError(
                _(f"Invalid file content type. Allowed types: {mime_types}")
            )
