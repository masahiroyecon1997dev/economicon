use super::FileError;
use dunce::canonicalize;
use std::fs;
use std::io::ErrorKind;
use std::path::{Path, PathBuf};

fn validate_regular_file(file_path: &str) -> Result<PathBuf, FileError> {
    if file_path.trim().is_empty() {
        return Err(FileError::PathRequired);
    }

    let path = PathBuf::from(file_path);

    if !path.exists() {
        return Err(FileError::PathNotFound(format!(
            "File does not exist: {}",
            file_path
        )));
    }

    let metadata = match fs::symlink_metadata(&path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == ErrorKind::PermissionDenied => {
            return Err(FileError::PermissionDenied(format!(
                "Cannot access file: {}",
                file_path
            )));
        }
        Err(error) => {
            return Err(FileError::UnexpectedError(error.to_string()));
        }
    };

    if !metadata.file_type().is_file() {
        return Err(FileError::NotAFile(format!(
            "Path is not a regular file: {}",
            file_path
        )));
    }

    canonicalize(&path).map_err(|error| {
        FileError::CanonicalizationError(format!(
            "Failed to canonicalize file '{}': {}",
            file_path, error
        ))
    })
}

fn map_delete_error(path: &Path, error: std::io::Error) -> FileError {
    match error.kind() {
        ErrorKind::NotFound => {
            FileError::PathNotFound(format!("File does not exist: {}", path.to_string_lossy()))
        }
        ErrorKind::PermissionDenied => {
            #[cfg(target_os = "windows")]
            if matches!(error.raw_os_error(), Some(32 | 33)) {
                return FileError::FileInUse(format!(
                    "File is in use by another process: {}",
                    path.to_string_lossy()
                ));
            }

            FileError::PermissionDenied(format!(
                "Permission denied while deleting file: {}",
                path.to_string_lossy()
            ))
        }
        _ => FileError::UnexpectedError(error.to_string()),
    }
}

pub fn can_delete_file_internal(file_path: &str) -> Result<(), FileError> {
    validate_regular_file(file_path)?;
    Ok(())
}

pub fn delete_file_internal(file_path: &str) -> Result<(), FileError> {
    let canonical_path = validate_regular_file(file_path)?;

    fs::remove_file(&canonical_path).map_err(|error| map_delete_error(&canonical_path, error))
}

#[cfg(test)]
mod tests {
    use super::{can_delete_file_internal, delete_file_internal};
    use crate::files::FileError;
    use std::fs;
    use std::path::PathBuf;
    use uuid::Uuid;

    fn create_temp_dir() -> PathBuf {
        let dir = std::env::temp_dir().join(format!("economicon-delete-test-{}", Uuid::new_v4()));
        fs::create_dir_all(&dir).expect("failed to create temp dir");
        dir
    }

    #[test]
    fn test_can_delete_file_internal_returns_ok_for_regular_file() {
        let temp_dir = create_temp_dir();
        let file_path = temp_dir.join("sample.csv");
        fs::write(&file_path, "a,b\n1,2\n").expect("failed to write temp file");

        let result = can_delete_file_internal(file_path.to_string_lossy().as_ref());

        assert!(result.is_ok());
        fs::remove_dir_all(temp_dir).expect("failed to remove temp dir");
    }

    #[test]
    fn test_delete_file_internal_removes_existing_file() {
        let temp_dir = create_temp_dir();
        let file_path = temp_dir.join("sample.csv");
        fs::write(&file_path, "a,b\n1,2\n").expect("failed to write temp file");

        delete_file_internal(file_path.to_string_lossy().as_ref())
            .expect("delete_file_internal should succeed");

        assert!(!file_path.exists());
        fs::remove_dir_all(temp_dir).expect("failed to remove temp dir");
    }

    #[test]
    fn test_can_delete_file_internal_rejects_directory_path() {
        let temp_dir = create_temp_dir();

        let result = can_delete_file_internal(temp_dir.to_string_lossy().as_ref());

        assert!(matches!(result, Err(FileError::NotAFile(_))));
        fs::remove_dir_all(temp_dir).expect("failed to remove temp dir");
    }
}
