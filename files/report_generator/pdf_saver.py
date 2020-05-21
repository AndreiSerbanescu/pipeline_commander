import os
from common.utils import *
import subprocess as sb


class Markdown2Pdf:

    def __init__(self):
        self.report_name = "report.pdf"

    def generate_pdf(self, report_dir, remove_files=True):
        pandoc_cmd = f"cd {report_dir} && pandoc -s -o {self.report_name} report.md --variable urlcolor=cyan"

        sb.check_output([pandoc_cmd], shell=True)
        pdf_filename = os.path.join(report_dir, self.report_name)

        if remove_files:
            self.__remove_other_files(report_dir)

        return pdf_filename

    def __remove_other_files(self, report_dir):
        files = os.listdir(report_dir)
        for file in files:
            if file != self.report_name:
                os.remove(os.path.join(report_dir, file))