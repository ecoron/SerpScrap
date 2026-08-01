import csv
import traceback


class CsvWriter:
    """Handles writing a list of dictionaries to a CSV file."""

    def write(self, file_name: str, rows: list[dict]):
        """Write a list of dictionaries to a CSV file with tab delimiter."""
        if not rows:
            raise ValueError("No data provided for CSV export.")
        try:
            with open(file_name, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, rows[0].keys(), dialect='excel', delimiter='\t', quotechar='"')
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
        except Exception as e:
            print(traceback.format_exc())
            raise RuntimeError(f"Failed to write CSV: {e}") from e
