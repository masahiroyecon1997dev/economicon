import mimetypes
from typing import List, Optional, Tuple

import magic
from analysisapp.i18n.translation import gettext_lazy as _
from fastapi import HTTPException, UploadFile


class FileValidationError(Exception):
    """
    ファイルバリデーション専用の例外
    """
    def __init__(self,
                 message: str,
                 status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class FileValidator:
    """
    ファイルバリデーションを行うクラス
    """
    def __init__(self,
                 max_size: int = 10 * 1024 * 1024,  # 10MB
                 allowed_extensions: Optional[Tuple[str]] = None,
                 allowed_mime_types: Optional[List[str]] = None):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions or ()
        self.allowed_mime_types = allowed_mime_types or []

    async def validate_file(self,
                            uploaded_file: UploadFile) -> Optional[Exception]:
        """
        ファイルバリデーションを実行

        Args:
            uploaded_file: FastAPIのUploadFileオブジェクト

        Returns:
            None: バリデーション成功
            HTTPException: バリデーション失敗時
        """
        try:
            if uploaded_file is None:
                message = _("No file uploaded.")
                return HTTPException(status_code=400, detail=message)
            self._validate_file_size(uploaded_file)
            self._validate_file_extension(uploaded_file)
            await self._validate_file_mime_type(uploaded_file)
            return None

        except FileValidationError as e:
            return HTTPException(
                status_code=e.status_code,
                detail=e.message
            )

    def _validate_file_size(self, uploaded_file: UploadFile):
        """
        ファイルサイズのチェック
        """
        if uploaded_file.size and uploaded_file.size > self.max_size:
            size_mb = self.max_size / (1024 * 1024)
            message = _(
                f"File size exceeds maximum limit of {size_mb}MB."
                )
            raise FileValidationError(
                message,
                413,
            )

    def _validate_file_extension(self, uploaded_file: UploadFile):
        """
        ファイル拡張子のチェック
        """
        if not uploaded_file.filename.lower().endswith(self.allowed_extensions):
            extensions = ', '.join(self.allowed_extensions)
            message = _(
                f"Uploaded file is not a {extensions} file.")
            raise FileValidationError(
                message,
                400
            )

    async def _validate_file_mime_type(self, uploaded_file: UploadFile):
        """
        MIMEタイプのチェック
        """
        # ファイル内容からMIMEタイプを判定
        await uploaded_file.seek(0)
        file_content = await uploaded_file.read(1024)  # 最初の1KBを読み取り
        await uploaded_file.seek(0)  # ファイルポインタをリセット

        try:
            detected_mime = magic.from_buffer(file_content, mime=True)
        except Exception:
            # python-magicが利用できない場合はファイル名から推測
            detected_mime, _encoding = mimetypes.guess_type(uploaded_file.filename)

        if detected_mime not in self.allowed_mime_types:
            mime_types = ', '.join(self.allowed_mime_types)
            raise FileValidationError(
                _(f"Invalid file content type. Allowed types: {mime_types}")
            )
            )
