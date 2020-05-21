import subprocess as sb
from threading import Thread
from file_server.file_server import start_file_server
import os
from time import sleep
from pipeline_handler import MultithreadedPipelineHandler
import shutil
import re

def start_streamlit_watcher(input_config_dir, result_config_dir):

    pipeline_handler = MultithreadedPipelineHandler(result_config_dir)

    while True:

        config_files = os.listdir(path=input_config_dir)

        for config_file in config_files:

            config_file_path = os.path.join(input_config_dir, config_file)
            tmp_config_file_path = os.path.join("/tmp", config_file)
            shutil.move(config_file_path, tmp_config_file_path)

            config_id = __extract_config_id(os.path.split(tmp_config_file_path)[1])

            pipeline_handler.start_pipeline(tmp_config_file_path, config_id)

        sleep(0.5)

# PRE: config name of form config-idhere.json
def __extract_config_id(config_name):
    return re.search('config-(.+?).json', config_name).group(1)


if __name__ == "__main__":

    streamlit_share_path = os.environ["COMMANDER_AND_STREAMLIT_SHARE_PATH"]
    config_dir = os.path.join(streamlit_share_path, "config")
    result_dir = os.path.join(streamlit_share_path, "result")

    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    streamlit_thread = Thread(target=start_streamlit_watcher, args=(config_dir, result_dir))
    fserver_thread = Thread(target=start_file_server)

    streamlit_thread.start()
    fserver_thread.start()
