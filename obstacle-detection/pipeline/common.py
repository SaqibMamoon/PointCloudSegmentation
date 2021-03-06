"""
Our implementation of obstacle detection pipeline steps
@authors:
"""
import numpy as np
import pandas as pd
from datetime import datetime
from numpy.linalg import eigh
from sklearn.preprocessing import normalize


def roi_filter_rounded(pcloud, verbose=True, **params):
    a = (- params['max_x'] - params['max_x']) / 2
    b = (params['min_y'] - params['max_y']) / 2

    if verbose:
        print('Input pcloud size: {}'.format(len(pcloud)))
    pcloud['equation'] = (pcloud['x'] ** 2) / (a ** 2) + (pcloud['y'] ** 2) / (b ** 2)

    pcloud['camera'] = ((pcloud['z'] >  params['min_z']) & (pcloud['z'] <  params['max_z']) &
                        (pcloud['x'] > params['min_x']) &
                        (pcloud['equation'] <= 1.0))

    pcloud = pcloud[pcloud['camera'] == True]

    if verbose:
        print('Output ROI pcloud size: {}'.format(len(pcloud)))
    return pcloud

def roi_filter(pcloud, verbose=True, **params):
    """

    Region Of Interest function, which filter required area
    that relative to LIDAR scanner (point (0, 0, 0) is a center)

    """
    if verbose:
        print('Input pcloud size: {}'.format(len(pcloud)))
    pcloud['camera'] = ((pcloud['x'] > params['min_x']) & (pcloud['x'] < params['max_x']) &
                        (pcloud['y'] >  params['min_y']) & (pcloud['y'] < params['max_y']) &
                        (pcloud['z'] >  params['min_z']) & (pcloud['z'] <  params['max_z']))
    pcloud = pcloud[pcloud['camera'] == True]
    if verbose:
        print('Output ROI pcloud size: {}'.format(len(pcloud)))
    return pcloud


def obstacle_filter(pcloud, obstacle_lst, proc_labels=True, verbose=True):
    """

    Obstacle filtering function
    pcloud: pandas.DataFrame,
    Point cloud DataFrame that have columns=['x', 'y', 'z', 'seg_id']

    obstacle_lst: list,
    A list of segments id you want to be remain after filtering
    """
    # sanity check
    assert isinstance(pcloud, pd.DataFrame)

    origin_point_size = len(pcloud)

    if proc_labels:
        pcloud.seg_id = pcloud.seg_id.astype('uint32')
        pcloud.seg_id = pcloud.seg_id.apply(lambda x: x & 0xFFFF)
        pcloud = pcloud[pcloud['seg_id'].isin(list(obstacle_lst.keys()))]
    else:
        pcloud = pcloud[pcloud['seg_id'].isin(obstacle_lst)]
    if verbose:
        print('Filter required segments')
        print('Point size before: {} and after filtering: {}'.format(origin_point_size, len(pcloud)))

    return pcloud


def outlier_filter(tcluster, verbose=True):

    # tcluster['norm'] = np.sqrt(np.square(tcluster).sum(axis=1))
    start_time = datetime.now()
    try:
        _mean, _std = tcluster['norm'].mean(), tcluster['norm'].std()
        lower, higher = _mean - 3 * _std, _mean + 3 * _std
    except:
        tcluster['norm'] = np.sqrt(np.square(tcluster[['x', 'y', 'z']]).sum(axis=1))
        _mean, _std = tcluster['norm'].mean(), tcluster['norm'].std()
        lower, higher = _mean - 3 * _std, _mean + 3 * _std
    end_time = (datetime.now() - start_time).total_seconds()
    if verbose:
        print('Computing lower-higher bounds {}'.format(end_time))

    start_time = datetime.now()
    tcluster = tcluster[(tcluster['norm'] > lower) & (tcluster['norm'] < higher)]
    end_time = (datetime.now() - start_time).total_seconds()
    if verbose:
        print('Applying  bounds {}'.format(end_time))
    return tcluster



def get_bounding_boxes(clusters):
    box_coord_list = []
    for i in range(len(clusters)):
        x_min, x_max, y_min, y_max, z_min, z_max =  list(clusters.iloc[i])
        box = np.zeros([8, 3])
        box[0, :] = [x_min, y_min, z_min]
        box[1, :] = [x_max, y_min, z_min]
        box[2, :] = [x_max, y_max, z_min]
        box[3, :] = [x_min, y_max, z_min]
        box[4, :] = [x_min, y_min, z_max]
        box[5, :] = [x_max, y_min, z_max]
        box[6, :] = [x_max, y_max, z_max]
        box[7, :] = [x_min, y_max, z_max]
        box = np.transpose(box)
        box_coord_list.append(box)
    return box_coord_list


def get_optimal_bboxes(clusters, cluster_data):
    box_coord_list = []
    cov_matrix = np.cov(cluster_data[['x', 'y', 'z']].T, bias=True)
    eig = np.linalg.eig(cov_matrix)
    clusters = []
    for cl_id in cluster_data.cluster_id.unique():
        cluster = cluster_data[cluster_data.cluster_id == cl_id]
        cluster = np.dot(cluster[['x', 'y', 'z']], eig[1])
        cluster = pd.DataFrame(cluster, columns = ['x', 'y', 'z'])
        cluster = cluster.agg({ 'x':['min','max'],
                                'y':['min','max'],
                                'z':['min','max']
                                  })
        clusters.append(cluster.T)
    for i in range(len(clusters)):
        x_min, x_max =  list(clusters[i].values[0])
        y_min, y_max =  list(clusters[i].values[1])
        z_min, z_max =  list(clusters[i].values[2])
        box = np.zeros([8, 3])
        box[0, :] = [x_min, y_min, z_min]
        box[1, :] = [x_max, y_min, z_min]
        box[2, :] = [x_max, y_max, z_min]
        box[3, :] = [x_min, y_max, z_min]
        box[4, :] = [x_min, y_min, z_max]
        box[5, :] = [x_max, y_min, z_max]
        box[6, :] = [x_max, y_max, z_max]
        box[7, :] = [x_min, y_max, z_max]

        box = np.transpose(box)
        box_coord_list.append(box)
    return box_coord_list


def get_rotated_data(cluster):

    cluster_id = cluster['cluster_id'].values
    rotation = np.cov(cluster[['x', 'y', 'z']].values, y=None, rowvar=0, bias=1)

    _, eigen_vectors = eigh(rotation)
    eigen_vec_normalized = normalize(eigen_vectors, axis=0)
    rotated_cluster = eigen_vectors.dot(cluster[['x','y','z']].values.T).T

    obb_min = np.min(rotated_cluster, axis=0)
    obb_max = np.max(rotated_cluster, axis=0)


    rotated_cluster = pd.DataFrame(rotated_cluster, columns = ['x', 'y', 'z'])
    rotated_cluster['cluster_id'] = cluster_id
    return rotated_cluster,  [
                                    # rightmost, topmost, farthest
                                    transform((obb_max[0], obb_max[1], obb_min[2]), rotation),
                                    # leftmost, topmost, farthest
                                    transform((obb_min[0], obb_max[1], obb_min[2]), rotation),
                                    # leftmost, topmost, closest
                                    transform((obb_min[0], obb_max[1], obb_max[2]), rotation),
                                    # rightmost, topmost, closest
                                    transform(obb_max, rotation),

                                    # leftmost, bottommost, farthest
                                    transform(obb_min, rotation),
                                    # rightmost, bottommost, farthest
                                    transform((obb_max[0], obb_min[1], obb_min[2]), rotation),
                                    # rightmost, bottommost, closest
                                    transform((obb_max[0], obb_min[1], obb_max[2]), rotation),
                                    # leftmost, bottommost, closest
                                    transform((obb_min[0], obb_min[1], obb_max[2]), rotation),
                                ]


def transform(point, rotation):
    return np.dot(np.array(point), rotation).tolist()
