import os
from workers.converter import Converter
import csv
import subprocess as sb

class CTFatMeasurer:

    def __init__(self, container_requester):
        self.container_requester = container_requester

        self.worker_hostname = os.environ["CT_FAT_MEASURE_HOSTNAME"]
        self.worker_port     = os.environ["CT_FAT_MEASURE_PORT"]
        self.nifti_measure_request_name = "ct_visceral_fat_nifti"
        self.dcm_measure_request_name   = "ct_visceral_fat_dcm"

        self.converter = Converter(self.container_requester)

    def measure_nifti(self, source_file, filepath_only=False):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"
        return self.__ct_fat_measure(source_file, request_name=self.nifti_measure_request_name,
                                     filepath_only=filepath_only)

    def measure_dcm(self, source_file, filepath_only=False):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

        nifti_filename = self.converter.convert_dcm_to_nifti(source_file)
        result = self.__ct_fat_measure(nifti_filename, request_name=self.nifti_measure_request_name,
                                        filepath_only=filepath_only)

        # delete temporary nifti conversion
        data_share = os.environ["DATA_SHARE_PATH"]
        os.remove(os.path.join(data_share, nifti_filename))

        return result

    def __ct_fat_measure(self, source_file, request_name, filepath_only):
        payload = {"source_file": source_file}

        response_dict = self.container_requester.send_request_to_worker(payload,
                                                                        self.worker_hostname,
                                                                        self.worker_port,
                                                                        request_name)

        relative_report_path = response_dict["fat_report"]
        data_share = os.environ["DATA_SHARE_PATH"]
        report_path = os.path.join(data_share, relative_report_path)

        print("Report path")

        if filepath_only:
            return report_path

        report_csv = self.__read_csv_file(report_path)
        self.__delete_file(report_path)

        return report_csv

    def __read_csv_file(self, filepath):

        with open(filepath) as csv_file:
            lines = csv_file.readlines()
            # remove all whitespaces
            lines = [line.replace(' ', '') for line in lines]

            csv_dict = csv.DictReader(lines)
            dict_rows = []
            for row in csv_dict:
                dict_rows.append(row)

            return dict_rows

    def __delete_file(self, filepath):

        rm_cmd = "rm -rf {}".format(filepath)
        print("Removing {}".format(filepath))
        sb.call([rm_cmd], shell=True)
