import os

class BaseDetectionMethod(object):
    # used for detection method mapping
    code = None

    def __init__(self, filepath, upload_to):
        self.filepath = filepath
        self.upload_to = upload_to
        self.result_data = {}

    def analyze(self):
        raise NotImplementedError

    def get_result(self):
        return self.result_data

    def output(self):
        return os.path.join(
            self.upload_to,
            self.filepath.split("/")[-1:][0]
        )




