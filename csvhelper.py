import csv
import io
from typing import TypeVar, Any
from sqlalchemy import inspect

T = TypeVar("T")


def convert_value(value: str | None, python_type: type, column_name: str, row_number: int) -> Any:
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    try:
        if python_type is bool:
            return value.lower() in {"1", "true", "yes", "y", "da"}

        return python_type(value)

    except Exception as exc:
        raise ValueError(
            f"Invalid value for column '{column_name}' at row {row_number}: {value!r}"
        ) from exc


def parse_csv_binary_to_entities(
    csv_binary: bytes,
    entity_type: type[T],
    delimiter: str = ",",
    encoding: str = "utf-8",
    skip_columns: set[str] | None = None,
) -> list[T]:
    skip_columns = skip_columns or set()

    mapper = inspect(entity_type)

    columns = [
        column
        for column in mapper.columns
        if column.key not in skip_columns
    ]

    required_columns = {
        column.key
        for column in columns
        if not column.nullable
        and column.default is None
        and column.server_default is None
        and not column.autoincrement
    }

    text_stream = io.StringIO(csv_binary.decode(encoding))
    reader = csv.DictReader(text_stream, delimiter=delimiter)

    if reader.fieldnames is None:
        raise ValueError("CSV is empty or missing header row.")

    csv_columns = set(reader.fieldnames)

    missing_columns = required_columns - csv_columns
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    entities: list[T] = []

    for row_number, row in enumerate(reader, start=2):
        values = {}

        for column in columns:
            column_name = column.key

            if column_name not in csv_columns:
                continue

            try:
                python_type = column.type.python_type
            except NotImplementedError:
                python_type = str

            values[column_name] = convert_value(
                row[column_name],
                python_type,
                column_name,
                row_number,
            )

        entities.append(entity_type(**values))

    return entities
