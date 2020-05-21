from file_cleaner import FileCleaner
import os

if __name__ == "__main__":

    fc_dir = "/app/test_filecleaner"
    os.makedirs(fc_dir, exist_ok=True)

    fc = FileCleaner(fc_dir, [".nii.gz", ".json"], expiry_time_secs=20, probe_interval=5)
    fc.start_watching()