#!/usr/bin/env python3.6

import rospy
import numpy as np

from grasp_generator.tools_superquadric.single_superquadric_generation import EMS_recovery
from sklearn.cluster import DBSCAN
from scipy.spatial.transform import Rotation as R

def hierarchical_ems(
    point,
    OutlierRatio=rospy.get_param('hierachical_ems/OutlierRatio'),               # prior outlier probability [0, 1) (default: 0.1)
    MaxIterationEM=rospy.get_param('hierachical_ems/MaxIterationEM'),           # maximum number of EM iterations (default: 20)
    ToleranceEM=rospy.get_param('hierachical_ems/ToleranceEM'),                 # absolute tolerance of EM (default: 1e-3)
    RelativeToleranceEM=rospy.get_param('hierachical_ems/RelativeToleranceEM'), # relative tolerance of EM (default: 1e-1)
    MaxOptiIterations=rospy.get_param('hierachical_ems/MaxOptiIterations'),     # maximum number of optimization iterations per M (default: 2)
    Sigma=rospy.get_param('hierachical_ems/Sigma'),                             # 0.3 initial sigma^2 (default: 0 - auto generate)
    MaxiSwitch=rospy.get_param('hierachical_ems/MaxiSwitch'),                   # maximum number of switches allowed (default: 2)
    AdaptiveUpperBound=rospy.get_param('hierachical_ems/AdaptiveUpperBound'),   # Introduce adaptive upper bound to restrict the volume of SQ (default: false)
    Rescale=rospy.get_param('hierachical_ems/Rescale'),                         # normalize the input point cloud (default: true)
    MaxLayer=rospy.get_param('hierachical_ems/MaxLayer'),                       # maximum depth
    Eps=rospy.get_param('hierachical_ems/Eps'),                                 # 0.03 IMPORTANT: varies based on the size of the input pointcoud (DBScan parameter)
    MinPoints=rospy.get_param('hierachical_ems/MinPoints'),                     # DBScan parameter required minimum points
):

    point_seg = {key: [] for key in list(range(0, MaxLayer+1))}
    point_outlier = {key: [] for key in list(range(0, MaxLayer+1))}
    point_seg[0] = [point]
    list_quadrics = []
    quadric_count = 1

    for h in range(MaxLayer):
        for c in range(len(point_seg[h])):
            #print(f"Counting number of generated quadrics: {quadric_count}")
            quadric_count += 1
            x_raw, p_raw = EMS_recovery(
                point_seg[h][c],
                OutlierRatio,
                MaxIterationEM,
                ToleranceEM,
                RelativeToleranceEM,
                MaxOptiIterations,
                Sigma,
                MaxiSwitch,
                AdaptiveUpperBound,
                Rescale,
            )
            point_previous = point_seg[h][c]
            list_quadrics.append(x_raw)
            outlier = point_seg[h][c][p_raw < 0.1, :]
            point_seg[h][c] = point_seg[h][c][p_raw > 0.1, :]
            if np.sum(p_raw) < (0.8 * len(point_previous)):
                clustering = DBSCAN(eps=Eps, min_samples=MinPoints).fit(outlier)
                labels = list(set(clustering.labels_))
                labels = [item for item in labels if item >= 0]
                if len(labels) >= 1:
                    for i in range(len(labels)):
                        point_seg[h + 1].append(outlier[clustering.labels_ == i])
                point_outlier[h].append(outlier[clustering.labels_ == -1])
            else:
                point_outlier[h].append(outlier)
    return list_quadrics
