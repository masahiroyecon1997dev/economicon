import json
from .input_validator import (InputValidationError, InputValidator)
from .input_validation_config import (INPUT_VALIDATOR_CONFIG)
from typing import Optional, Dict, Any
from ....apis.data.tables_info import all_tables_info
from ..create_response import create_error_response


def validate_add_column_request(request) -> Optional[Dict[str, Any]]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)
        request_data = json.loads(request.body)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        new_column_name = request_data['newColumnName']
        table_info = all_tables_info[table_name]
        validator.validate_new_column_name(new_column_name, table_info)

        insert_position_column = request_data['insertPositionColumn']
        validator.validate_existed_column_name(insert_position_column,
                                               table_info)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )
