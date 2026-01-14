"""
Variable Data Import
Imports CSV data for batch personalization of nameplates.
"""

import csv
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class DataField:
    """Represents a field/column from imported data."""
    name: str
    values: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.values)


@dataclass
class VariableDataSet:
    """Contains imported variable data."""
    fields: Dict[str, DataField] = field(default_factory=dict)
    row_count: int = 0
    source_file: str = ""

    def get_field_names(self) -> List[str]:
        """Get list of field names."""
        return list(self.fields.keys())

    def get_row(self, index: int) -> Dict[str, str]:
        """Get all field values for a specific row."""
        if index < 0 or index >= self.row_count:
            return {}
        return {name: field.values[index] for name, field in self.fields.items()}

    def get_field_value(self, field_name: str, index: int) -> str:
        """Get a specific field value at a row index."""
        if field_name in self.fields and 0 <= index < self.fields[field_name].count:
            return self.fields[field_name].values[index]
        return ""


class VariableDataImporter:
    """
    Imports variable data from CSV files for batch personalization.
    """

    def __init__(self):
        self._dataset: Optional[VariableDataSet] = None

    def import_csv(self, filepath: str, has_header: bool = True,
                   delimiter: str = ',', encoding: str = 'utf-8') -> Optional[VariableDataSet]:
        """
        Import data from a CSV file.

        Args:
            filepath: Path to the CSV file
            has_header: Whether first row contains column headers
            delimiter: Field delimiter character
            encoding: File encoding

        Returns:
            VariableDataSet with imported data, or None if failed
        """
        try:
            dataset = VariableDataSet(source_file=filepath)

            with open(filepath, 'r', encoding=encoding, newline='') as f:
                reader = csv.reader(f, delimiter=delimiter)

                # Get headers
                if has_header:
                    headers = next(reader, None)
                    if not headers:
                        return None
                else:
                    # Peek first row to determine column count
                    first_row = next(reader, None)
                    if not first_row:
                        return None
                    headers = [f"Column_{i+1}" for i in range(len(first_row))]
                    # Add first row back as data
                    for i, value in enumerate(first_row):
                        if headers[i] not in dataset.fields:
                            dataset.fields[headers[i]] = DataField(name=headers[i])
                        dataset.fields[headers[i]].values.append(value)
                    dataset.row_count = 1

                # Initialize fields
                for header in headers:
                    clean_header = header.strip()
                    if clean_header and clean_header not in dataset.fields:
                        dataset.fields[clean_header] = DataField(name=clean_header)

                # Read data rows
                for row in reader:
                    for i, value in enumerate(row):
                        if i < len(headers):
                            header = headers[i].strip()
                            if header in dataset.fields:
                                dataset.fields[header].values.append(value.strip())
                    dataset.row_count += 1

            self._dataset = dataset
            return dataset

        except Exception as e:
            print(f"Error importing CSV: {e}")
            return None

    def get_dataset(self) -> Optional[VariableDataSet]:
        """Get the currently loaded dataset."""
        return self._dataset

    def apply_to_config(self, config: Dict[str, Any],
                        row_index: int,
                        field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Apply variable data to a configuration.

        Args:
            config: Base configuration dictionary
            row_index: Row index in the dataset
            field_mapping: Maps config paths to field names
                          e.g., {"text.lines[0].segments[0].content": "Name"}

        Returns:
            Modified configuration with substituted values
        """
        if not self._dataset:
            return config

        import copy
        result = copy.deepcopy(config)

        for config_path, field_name in field_mapping.items():
            value = self._dataset.get_field_value(field_name, row_index)
            if value:
                self._set_nested_value(result, config_path, value)

        return result

    def _set_nested_value(self, config: Dict, path: str, value: str):
        """Set a value at a nested path in the config."""
        # Parse path like "text.lines[0].segments[0].content"
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]  # Remove empty strings

        current = config
        for i, part in enumerate(parts[:-1]):
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return

        # Set the final value
        final_part = parts[-1]
        if final_part.isdigit():
            idx = int(final_part)
            if isinstance(current, list) and idx < len(current):
                current[idx] = value
        elif isinstance(current, dict):
            current[final_part] = value


class TemplateParser:
    """
    Parses template strings with variable placeholders.
    """

    PLACEHOLDER_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    @staticmethod
    def parse_template(template: str, data: Dict[str, str]) -> str:
        """
        Replace placeholders in template with data values.

        Args:
            template: String with {{field_name}} placeholders
            data: Dictionary of field values

        Returns:
            String with placeholders replaced
        """
        def replacer(match):
            field_name = match.group(1)
            return data.get(field_name, match.group(0))

        return TemplateParser.PLACEHOLDER_PATTERN.sub(replacer, template)

    @staticmethod
    def find_placeholders(template: str) -> List[str]:
        """
        Find all placeholder field names in a template.

        Args:
            template: String to search

        Returns:
            List of field names found
        """
        return TemplateParser.PLACEHOLDER_PATTERN.findall(template)

    @staticmethod
    def has_placeholders(template: str) -> bool:
        """Check if a string contains any placeholders."""
        return bool(TemplateParser.PLACEHOLDER_PATTERN.search(template))


def generate_sample_csv(filepath: str, num_rows: int = 10):
    """
    Generate a sample CSV file for testing.

    Args:
        filepath: Output file path
        num_rows: Number of sample rows to generate
    """
    sample_names = [
        ("John", "Smith", "Engineering"),
        ("Jane", "Doe", "Marketing"),
        ("Bob", "Johnson", "Sales"),
        ("Alice", "Williams", "HR"),
        ("Charlie", "Brown", "IT"),
        ("Diana", "Davis", "Finance"),
        ("Edward", "Miller", "Operations"),
        ("Fiona", "Wilson", "Legal"),
        ("George", "Moore", "R&D"),
        ("Helen", "Taylor", "Support"),
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["FirstName", "LastName", "Department", "ID"])

        for i in range(min(num_rows, len(sample_names))):
            first, last, dept = sample_names[i]
            writer.writerow([first, last, dept, f"{1000 + i}"])


def preview_data(dataset: VariableDataSet, max_rows: int = 5) -> str:
    """
    Generate a text preview of the dataset.

    Args:
        dataset: Dataset to preview
        max_rows: Maximum rows to show

    Returns:
        Formatted string preview
    """
    if not dataset or not dataset.fields:
        return "No data loaded"

    lines = []
    headers = dataset.get_field_names()

    # Header row
    lines.append(" | ".join(headers))
    lines.append("-" * len(lines[0]))

    # Data rows
    for i in range(min(max_rows, dataset.row_count)):
        row = dataset.get_row(i)
        values = [row.get(h, "") for h in headers]
        lines.append(" | ".join(values))

    if dataset.row_count > max_rows:
        lines.append(f"... and {dataset.row_count - max_rows} more rows")

    return "\n".join(lines)
