from typing import List


def create_table_name_by_file_name(file_name: str,
                                   table_name_list: List[str]) -> str:
    table_name: str = file_name.split('.')[0]
    if _check_duplicated_table_name(table_name, table_name_list):
        table_name = f'{table_name}_1'
    return table_name


def _check_duplicated_table_name(table_name_cadidate: str,
                                 table_name_list: List[str]) -> bool:
    return table_name_cadidate in table_name_list
