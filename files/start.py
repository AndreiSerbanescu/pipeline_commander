import subprocess as sb
from threading import Thread
from file_server.file_server import start_file_server
import os
from time import sleep
from pipeline_handler import MultithreadedPipelineHandler
import shutil

def start_streamlit_watcher():

    streamlit_share_path = os.environ["COMMANDER_AND_STREAMLIT_SHARE_PATH"]
    config_path = os.path.join(streamlit_share_path, "config")

    pipeline_handler = MultithreadedPipelineHandler()

    while True:

        config_files = os.listdir(path=config_path)

        for config_file in config_files:

            config_file_path = os.path.join(config_path, config_file)
            tmp_config_file_path = os.path.join("/tmp", config_file)
            shutil.move(config_file_path, tmp_config_file_path)

            pipeline_handler.start_pipeline(tmp_config_file_path)

        sleep(0.5)


if __name__ == "__main__":

    streamlit_share_path = os.environ["COMMANDER_AND_STREAMLIT_SHARE_PATH"]
    config_dir = os.path.join(streamlit_share_path, "config")
    result_dir = os.path.join(streamlit_share_path, "result")

    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    streamlit_thread = Thread(target=start_streamlit_watcher)
    fserver_thread = Thread(target=start_file_server)

    streamlit_thread.start()
    fserver_thread.start()
