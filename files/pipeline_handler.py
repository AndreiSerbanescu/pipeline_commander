import os
import shutil
from common import utils
from exceptions.workers import WorkerNotReadyException, WorkerFailedException
import segmenter
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import json
from common_display.main_displayer import MainDisplayer

def ct_fat_report(source_file, filepath_only=False):
    print("ct fat report called with", source_file)

    if segmenter.is_nifti(source_file):
        return segmenter.ct_fat_measure_nifti(source_file, filepath_only=filepath_only)
    else:
        return segmenter.ct_fat_measure_dcm(source_file, filepath_only=filepath_only)


def ct_muscle_segment(source_file, filepath_only=False):
    print("ct muscle segment called with", source_file)

    if segmenter.is_nifti(source_file):
        muscle_segmentation, original = segmenter.ct_muscle_segment_nifti(source_file, filepath_only=filepath_only)
    else:
        muscle_segmentation, original = segmenter.ct_muscle_segment_dcm(source_file, filepath_only=filepath_only)

    return muscle_segmentation


def lesion_detect(source_file, filepath_only=False):
    print("lesion detect called with", source_file)

    if segmenter.is_nifti(source_file):
        attention_volume, detection_volume = segmenter.covid_detector_nifti(source_file, filepath_only=filepath_only)
    else:
        attention_volume, detection_volume = segmenter.covid_detector_dcm(source_file, filepath_only=filepath_only)


    return attention_volume, detection_volume


def lesion_detect_seg(source_file, filepath_only=False):
    print("lesion detect seg called with", source_file)

    if segmenter.is_nifti(source_file):
        mask_volume, detection_volume = segmenter.covid_detector_seg_nifti(source_file, filepath_only=filepath_only)
    else:
        mask_volume, detection_volume = segmenter.covid_detector_seg_dcm(source_file, filepath_only=filepath_only)

    return mask_volume, detection_volume


def lungmask_segment(source_dir, filepath_only=False):
    segmentation, input = segmenter.lungmask_segment(source_dir, model_name='R231CovidWeb', filepath_only=filepath_only)
    return segmentation, input


class MultithreadedPipelineHandler:

    def start_pipeline(self, config_filepath):

        sn_thrd_pipeline_handler = PipelineHandler()

        pipeline_thread = Thread(target=lambda: sn_thrd_pipeline_handler.start_pipeline(config_filepath))
        pipeline_thread.start()

class PipelineHandler:

    def __init__(self):
        self.LUNGMASK_SEGMENT = "Lungmask Segmentation"
        self.CT_FAT_REPORT = "CT Fat Report"
        self.CT_MUSCLE_SEGMENTATION = "CT Muscle Segmentation"
        self.LESION_DETECTION = "Lesion Detection"
        self.LESION_DETECTION_SEG = "Lesion Detection Segmentation"


    def start_pipeline(self, config_filepath):
        data = self.__extract_data_from_and_delete_config(config_filepath)
        workers_selected = data["workers_selected"]
        source_filepath = data["source_filepath"]

        value_map, workers_not_ready, workers_failed = self.__call_workers(workers_selected, source_filepath)
        paths = self.__move_files_to_fileserver_dir_and_get_paths(value_map)

        self.__generate_pdf_report(paths, workers_not_ready, workers_failed)


    def __extract_data_from_and_delete_config(self, config_filepath):

        with open(config_filepath, "r") as config_file:
            contents = json.load(config_file)

        # os.remove(config_filepath) TODO remove
        os.rename(config_filepath, f"{config_filepath}.old")

        print("type of json", type(contents))

        contents = json.loads(contents)

        print("type of contents", type(contents))

        assert "source_filepath" in contents
        assert "project_name" in contents
        assert "workers_selected" in contents

        return contents

    def __get_worker_information(self):

        worker_names = [self.LUNGMASK_SEGMENT, self.CT_FAT_REPORT, self.CT_MUSCLE_SEGMENTATION,
                        self.LESION_DETECTION, self.LESION_DETECTION_SEG]

        worker_methods = {
            self.LUNGMASK_SEGMENT: lungmask_segment,
            self.CT_FAT_REPORT: ct_fat_report,
            self.CT_MUSCLE_SEGMENTATION: ct_muscle_segment,
            self.LESION_DETECTION: lesion_detect,
            self.LESION_DETECTION_SEG: lesion_detect_seg
        }

        return worker_methods, worker_names

    def __call_workers(self, workers_selected, source_dir):

        worker_methods = self.__get_worker_information()[0]
        future_map = {}
        with ThreadPoolExecutor() as executor:

            for worker in workers_selected:
                method = worker_methods[worker]

                future = executor.submit(method, source_dir, filepath_only=True)
                future_map[worker] = future

        value_map = {}
        workers_failed = []
        workers_not_ready = []
        for key in future_map:
            future = future_map[key]

            try:
                value = future.result()
                value_map[key] = value
            except WorkerNotReadyException:
                # __display_worker_not_ready(key, streamlit_wrapper=streamlit_wrapper)
                workers_not_ready.append(key)
            except WorkerFailedException:
                # __display_worker_failed(key, streamlit_wrapper=streamlit_wrapper)
                workers_failed.append(key)

        return value_map, workers_not_ready, workers_failed


    def __generate_pdf_report(self, paths, workers_not_ready, workers_failed):
        # all of these paths may be None
        # the displayer expects None values

        lungmask_path = paths.get("lungmask")
        input_path = paths.get("input")
        fat_report_path = paths.get("fat_report")
        muscle_seg_path = paths.get("muscle_seg")
        lesion_detection_path = paths.get("lesion_detection")
        lesion_attention_path = paths.get("lesion_attention")
        lesion_seg_mask_path = paths.get("lesion_seg_mask")
        lesion_seg_detection_path = paths.get("lesion_seg_detection")

        print("generate pdf report paths", paths)
        print("generate pdf report workers not ready", workers_not_ready)
        print("generate pdf report workers failed", workers_failed)

        # TODO generate report and send email here
        # TODO make result config file for streamlit

        # displayer = MainDisplayer(streamlit_wrapper=)
        #
        # class MainDisplayer:
        #
        #     def __init__(self, streamlit_wrapper=None, save_to_pdf=True, email_receiver=None,
        #                  subject_name=None, pdf_saver_class=None):
        #
        #     def display_volume_and_slice_information(self, input_nifti_path, lung_seg_path, muscle_seg=None,
        #                                              lesion_detection=None, lesion_attention=None,
        #                                              lesion_detection_seg=None,
        #                                              lesion_mask_seg=None, fat_report=None, fat_interval=None):

    def __move_files_to_fileserver_dir_and_get_paths(self, value_map):

        unique_id = utils.get_unique_id()

        paths = {}

        if self.LUNGMASK_SEGMENT in value_map:
            lungmask_path, input_path = value_map[self.LUNGMASK_SEGMENT]
            lungmask_path = self.__move_file_to_fileserver_base_dir(lungmask_path,
                                                                    download_name=f"lungmask-{unique_id}.nii.gz")
            input_path = self.__move_file_to_fileserver_base_dir(input_path, download_name=f"input-{unique_id}.nii.gz")

            paths["input"] = input_path
            paths["lungmask"] = lungmask_path

        if self.CT_FAT_REPORT in value_map:
            fat_report_path = value_map[self.CT_FAT_REPORT]
            fat_report_path = self.__move_file_to_fileserver_base_dir(fat_report_path,
                                                                      download_name=f"fat_report-{unique_id}.txt")

            paths["fat_report"] = fat_report_path

        if self.CT_MUSCLE_SEGMENTATION in value_map:
            muscle_seg_path = value_map[self.CT_MUSCLE_SEGMENTATION]
            muscle_seg_path = self.__move_file_to_fileserver_base_dir(muscle_seg_path,
                                                                      download_name=f"muscle_segmentation-"
                                                                                    f"{unique_id}.nii.gz")

            paths["muscle_seg"] = muscle_seg_path

        if self.LESION_DETECTION in value_map:
            lesion_attention_path, lesion_detection_path = value_map[self.LESION_DETECTION]
            lesion_attention_path = self.__move_file_to_fileserver_base_dir(lesion_attention_path,
                                                                            download_name=f"lesion_attention-"
                                                                                          f"{unique_id}.nii.gz")
            lesion_detection_path = self.__move_file_to_fileserver_base_dir(lesion_detection_path,
                                                                            download_name=f"lesion_detection-"
                                                                                          f"{unique_id}.nii.gz")

            paths["lesion_attention"] = lesion_attention_path
            paths["lesion_detection"] = lesion_detection_path

        if self.LESION_DETECTION_SEG in value_map:
            lesion_seg_mask_path, lesion_seg_detection_path = value_map[self.LESION_DETECTION_SEG]
            lesion_seg_mask_path = self.__move_file_to_fileserver_base_dir(lesion_seg_mask_path,
                                                                           download_name=f"lesion_seg_mask-"
                                                                                         f"{unique_id}.nii.gz")
            lesion_seg_detection_path = self.__move_file_to_fileserver_base_dir(lesion_seg_detection_path,
                                                                                download_name=f"lesion_seg_detection-"
                                                                                              f"{unique_id}.nii.gz")

            paths["lesion_seg_mask"]      = lesion_seg_mask_path
            paths["lesion_seg_detection"] = lesion_seg_detection_path

        return paths

    def __move_file_to_fileserver_base_dir(self, filepath, download_name=None, copy_only=False):

        name = os.path.split(filepath)[1] if download_name is None else download_name

        fileserver_base_dir = os.environ["FILESERVER_BASE_DIR"]

        fs_out_filename = os.path.join(fileserver_base_dir, name)

        if copy_only:
            shutil.copyfile(filepath, fs_out_filename)
        else:
            shutil.move(filepath, fs_out_filename)
        return fs_out_filename
