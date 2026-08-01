"""Stores SERP results in the appropriate output format."""
import pprint
import sys

from scrapcore.database import SERP, Link
from scrapcore.tools import CsvStreamWriter, JsonStreamWriter


class ResultWriter:
    """Handles writing SERP results to the configured output format (stdout, JSON, or CSV)."""

    def __init__(self):
        self.output_format = 'stdout'
        self.outfile = sys.stdout

    def init_outfile(self, config, force_reload=False):
        """Initialize the output file/stream based on config."""
        if not self.outfile or force_reload:
            output_file = config.get('output_filename', '')
            if not output_file or output_file == 'stdout':
                self.output_format = 'stdout'
                self.outfile = sys.stdout
            elif output_file.endswith('.json'):
                self.output_format = 'json'
                self.outfile = JsonStreamWriter(output_file)
            elif output_file.endswith('.csv'):
                self.output_format = 'csv'
                csv_fieldnames = sorted(
                    set(Link.__table__.columns._data.keys() | SERP.__table__.columns._data.keys()) - {'id', 'serp_id'}
                )
                self.outfile = CsvStreamWriter(output_file, csv_fieldnames)
            else:
                self.output_format = None
                self.outfile = None

    def store_serp_result(self, serp, config):
        """Store the parsed SERP page in the configured output format."""
        if self.outfile:
            data = self.row2dict(serp)
            data['results'] = [self.row2dict(link) for link in serp.links]
            if self.output_format == 'json':
                self.outfile.write(data)
            elif self.output_format == 'csv':
                serp_dict = self.row2dict(serp)
                self.outfile.write(data, serp_dict)
            elif self.output_format == 'stdout':
                if config.get('print_results') == 'summarize':
                    print(serp)
                elif config.get('print_results') == 'all':
                    pprint.pprint(data)

    def row2dict(self, obj) -> dict:
        """Convert a SQLAlchemy object to a dictionary."""
        return {column.name: str(getattr(obj, column.name)) for column in obj.__table__.columns}

    def close_outfile(self):
        """Closes the output file/stream if needed."""
        if self.output_format in ('json', 'csv') and self.outfile:
            self.outfile.end()
