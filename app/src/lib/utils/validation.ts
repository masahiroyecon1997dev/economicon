type ValidationResult = string | undefined;

export const validateTableName = (tableName: string): ValidationResult => {
  if (!tableName.trim()) {
    return "ValidationMessages.DataNameRequired";
  }
  return undefined;
};

export const validateNumRows = (numRows: number): ValidationResult => {
  if (numRows < 1) {
    return "ValidationMessages.NumRowsMoreThan0";
  }
  return undefined;
};

export const validateColumnName = (columnName: string): ValidationResult => {
  if (!columnName.trim()) {
    return "ValidationMessages.ColumnNameRequired";
  }
  return undefined;
};
