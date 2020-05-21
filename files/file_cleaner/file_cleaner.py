from time import sleep
import os
import time

class FileCleaner:

    def __init__(self, dir_to_watch, extensions_to_watch, expiry_time_secs=60 * 60 * 6,
                 probe_interval=60):

        self.dir_to_watch = dir_to_watch
        self.expiry_time = expiry_time_secs
        self.extensions_to_watch = extensions_to_watch
        self.probe_interval = probe_interval

    def start_watching(self):

        while True:

            files = os.listdir(self.dir_to_watch)

            files_to_delete = self.__get_files_to_delete(files)
            self.__delete_files(files_to_delete)

            sleep(self.probe_interval)

    def __get_files_to_delete(self, files):

        files_fullpaths = map(lambda f: os.path.join(self.dir_to_watch, f), files)

        files_to_delete = []

        for file in files_fullpaths:
            for extension in self.extensions_to_watch:
                if file.endswith(extension) and self.__file_expired(file):
                    files_to_delete.append(file)

        return files_to_delete

    def __file_expired(self, file):

        file_stats = os.stat(file)
        age = (time.time() - file_stats.st_mtime)

        return age > self.expiry_time

    def __delete_files(self, file_fullpaths):

        for file in file_fullpaths:
            print(f"Deleting expired file {file}")
            os.remove(file)
