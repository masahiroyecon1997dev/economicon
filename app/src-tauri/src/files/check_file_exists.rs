/// 指定したフルパスにファイルが存在するかどうかを返す。
///
/// - 存在し、かつ通常ファイル（ディレクトリ・シンボリックリンクでない）の場合に `true`
/// - パスが空・存在しない・ディレクトリの場合は `false`
pub fn check_file_exists_internal(file_path: &str) -> bool {
    if file_path.trim().is_empty() {
        return false;
    }
    std::path::Path::new(file_path).is_file()
}
