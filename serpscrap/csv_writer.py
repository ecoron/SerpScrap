# -*- coding: utf-8 -*-
import csv
import traceback


class CsvWriter():

    def write(self, file_name, my_dict):
        try:
            with open(file_name, 'w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, my_dict[0].keys(), dialect='excel', delimiter='\t', quotechar='"')
                w.writeheader()
                for row in my_dict[0:]:
                    w.writerow(row)
        except Exception:
            print(traceback.print_exc())
            raise Exception
