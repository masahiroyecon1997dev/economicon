---
applyTo: "ApiServer/**"
---

# FastAPI Backend Implementation Rules

## 1. Environment & Tools

- **Manager**: `uv`
- **Linting**: `flake8`
  - **Max line length**: 79 characters (72 for docstrings/comments)
  - **Indentation**: 4 spaces

## 2. i18n & Global Context

- **Translation**: `analysisapp.i18n.translation.gettext_lazy as _`
- **Language Setup**: Use `ContextVar` based thread-safe settings.
- **Rules**: All user-facing strings must be wrapped in `_()`.

## 3. Services (AbstractApi) Requirements

Every API service class must inherit from `AbstractApi` and implement:

1. `__init__`: Define `self.param_names` (Map `camelCase` to `snake_case`).
2. `validate`: Return `None` on success, raise `ValidationError`.
3. `execute`: Core logic using `Polars`. Raise `ApiError` for expected failures.

## 4. Router & Response Patterns

- **Endpoint**: `@router.post("/kebab-case-path")`
- **Error Mapping**:
  - `ValidationError` -> `status.HTTP_400_BAD_REQUEST`
  - `ApiError` / `Exception` -> `status.HTTP_500_INTERNAL_SERVER_ERROR`
- **Helper**: Use `create_success_response` or `create_error_response`.

## 5. Naming Convention Reference

| Category       | Convention | Example             |
| :------------- | :--------- | :------------------ |
| **Files**      | snake_case | `create_table.py`   |
| **Classes**    | PascalCase | `CreateTable`       |
| **JSON Key**   | camelCase  | `tableName`         |
| **Python Var** | snake_case | `table_name`        |
| **URLs**       | kebab-case | `/api/create-table` |

## 6. Testing (pytest)

- **File Name**: `test_*.py`
- **Function Name**: `test_[feature]_[scenario]`
- **Required Fixtures**: `client`, `tables_store`
- **Standard Assertions**:
  - `response.status_code`
  - `response_data['code'] == 'OK'/'NG'`
