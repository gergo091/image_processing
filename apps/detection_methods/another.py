import math
import json
import random
import numpy as np
from scipy.spatial import KDTree
import cv2
import Pycluster
from . core import BaseDetectionMethod

class Analyzator(BaseDetectionMethod):
    code = "ANOTHER"
    threshold = 0.4
    pre_conditions = {
        "min_cluster_items": 3
    }

def __init__(self, *args, **kwargs):
        super(Analyzator, self).__init__(*args, **kwargs)
        self.another = cv2.ANOTHER()
        self.is_forgery = False
        self.stat_data = {
            "final_keypoints": 0,
            "final_clusters": {},
            "keypoints": 0,
            "all_clusters": 0
        }

def save_result(self):
        if self.is_forgery:
            self.result_data["result_status"] = "forgery"
            self.result_data["filepath"] = self.output()
        else:
            self.result_data["result_status"] = "not_altered"

        self.result_data["result_note"] = json.dumps(self.stat_data)

   # if self.stat_data["final_keypoints"]:
    #        self.is_forgery = True
            # write result document
     #       cv2.imwrite(self.output(), img)

        self.save_result()

