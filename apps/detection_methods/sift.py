import math
import json
import random
import numpy as np
from scipy.spatial import KDTree
import cv2
import Pycluster
from . core import BaseDetectionMethod


class Analyzator(BaseDetectionMethod):
    code = "SIFT"
    threshold = 0.4
    pre_conditions = {
        "min_cluster_items": 3
    }

    def __init__(self, *args, **kwargs):
        super(Analyzator, self).__init__(*args, **kwargs)
        self.sift = cv2.SIFT()
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

    def get_cluster(self, points, point):
        for index, x in enumerate(points):
            if (x[0], x[1]) == point:
                return index

    def _generate_color_for_clusters(self, num_of_clusters):
        colors = []
        r = random.randint
        for i in range(num_of_clusters):
            colors.append((r(0, 255), r(0, 255), r(0, 255)))

        return colors

    def find_nearest_neighbors(self, kd_tree, descriptors, k):
        return kd_tree.query(np.array(descriptors), k)

    def num_of_clusters(self, count):
        #http://en.wikipedia.org/wiki/Determining_the_number_of_clusters_in_a_data_set
        return int(math.sqrt(count / 2 )) + 1

    def nn_test(self, nearest_neighboors):
        n = nearest_neighboors

        if n[1] / n[2] < self.threshold or n[2] / n[3] < self.threshold:
            return True

        return False

    def analyze(self):
        img = cv2.imread(self.filepath)
        # convert to gray
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # compute keypoints and descriptors
        keypoints, descriptors = self.sift.compute(
            gray,
            self.sift.detect(gray, None)
        )

        # kd-tree for nearest neighbors
        kd_tree = KDTree(descriptors)

        tr = []

        for descriptor in descriptors:
            # find nearest neighbors
            neighboors, positions = self.find_nearest_neighbors(
                kd_tree,
                descriptor,
                4
            )
            # array([0, 257.53640519, 262.92584506, 281.47824072]),
            # array([477, 207, 460,  11])

            if self.nn_test(neighboors):
                a, b = keypoints[positions[0]], keypoints[positions[1]]
                if any(p.pt not in tr for p in [a, b]):
                    tr.append(a.pt)
                    tr.append(b.pt)

        tr = np.asarray(tr)
        num_of_clusters = self.num_of_clusters(len(tr))
        clusters, e, n = Pycluster.kcluster(tr, num_of_clusters)
        colors = self._generate_color_for_clusters(num_of_clusters)
        # to array
        clusters = clusters.tolist()

        self.stat_data["keypoints"] = len(tr)
        self.stat_data["all_clusters"] = len({c for c in clusters})

        final_data = []

        not_suitable_clusters = []
        connections_count = {}

        for index in range(0, len(tr), 2):

            cluster1 = clusters[index]
            cluster2 = clusters[index+1]

            if any(c in not_suitable_clusters for c in [cluster1, cluster2]):
                continue

            # cluster pre conditions
            if clusters.count(cluster1) < self.pre_conditions["min_cluster_items"]:
                not_suitable_clusters.append(cluster1)
                continue

            if clusters.count(cluster2) < self.pre_conditions["min_cluster_items"]:
                not_suitable_clusters.append(cluster2)
                continue

            # point pre condition  
            if cluster1 == cluster2:
                continue
                #not_suitable_clusters.append(cluster1)
                #not_suitable_clusters.append(cluster2)
    
            if cluster1 not in connections_count:
                connections_count[cluster1] = 0

            if cluster2 not in connections_count:
                connections_count[cluster2] = 0

            # at least 3 connections
            connections_count[cluster1] += 1
            connections_count[cluster2] += 1

            final_data.append((index, index+1))

        self.stat_data["filtered_clusters"] = connections_count

        for point in final_data:
            a, b = tr[point[0]]
            a1, b1 = tr[point[1]]

            cluster = clusters[point[0]]
            cluster1 = clusters[point[1]]

            # min 3 connection within clusters are required
            if connections_count[cluster] < 3 or connections_count[cluster1] < 3:
                continue

            cv2.circle(img, (int(a), int(b)), 3, colors[cluster-1], -1)
            cv2.circle(img, (int(a1), int(b1)), 3, colors[cluster1-1], -1)

            cv2.line(
                img,
                (int(a), int(b)),
                (int(a1), int(b1)),
                (0, 255, 255)
            )

            self.is_forgery = True


            if cluster not in self.stat_data["final_clusters"]:
                self.stat_data["final_clusters"][cluster] = 0

            if cluster1 not in self.stat_data["final_clusters"]:
                self.stat_data["final_clusters"][cluster1] = 0

            self.stat_data["final_clusters"][cluster] += 1
            self.stat_data["final_clusters"][cluster1] += 1
            self.stat_data["final_keypoints"] += 2


        if self.stat_data["final_keypoints"]:
            self.is_forgery = True
            # write result document
            cv2.imwrite(self.output(), img)

        self.save_result()
