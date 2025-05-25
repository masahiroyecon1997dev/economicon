from typing import Dict, Any


def create_table_name_by_file_name(file_name: str,
                                   tables: Dict[str, Any]) -> str:
    file_name: str = file_name
    table_name: str = file_name.split('.')[0]
    if _check_duplicated_table_name(table_name, tables):
        table_name = f'{table_name}_1'
    return table_name


def _check_duplicated_table_name(table_name_cadidate: str,
                                 tables: Dict[str, Any]) -> bool:
    return table_name_cadidate in tables
