import numpy as np
import re
import os
import sys
# import cv2


def orientation_diff(array1, array2):
    concat = np.concatenate((np.expand_dims(array1, axis=1),
                             np.expand_dims(array2, axis=1)), axis=1)
    diffs = np.concatenate((np.expand_dims(concat[:,0] - concat[:,1], axis=1),
                            np.expand_dims(concat[:,0] - concat[:,1] - 180, axis=1),
                            np.expand_dims(concat[:,0] - concat[:,1] + 180, axis=1)), axis=1)
    diffs_argmin = np.argmin(np.abs(diffs), axis=1)
    return [idiff[argmin] for idiff, argmin in zip(diffs, diffs_argmin)]


def cluster_points(xs, ys, stepsize):
    xss = list(xs)
    sort_args = np.array(xss).argsort()
    xss.sort()
    ys_sorted = np.array(ys)[sort_args]

    x_accumulator = []
    y_mu = []
    y_25 = []
    y_75 = []
    x_perbin = []
    y_perbin = []
    icut = -90 + stepsize

    for ix, iy in zip(xss, ys_sorted):
        if ix < icut:
            x_perbin.append(ix)
            y_perbin.append(iy)
        else:
            if len(y_perbin) > 0:
                x_accumulator.append(icut - stepsize / 2)
                y_mu.append(np.median(y_perbin))
                y_25.append(np.percentile(y_perbin, 25))
                y_75.append(np.percentile(y_perbin, 75))
            icut += stepsize
            x_perbin = []
            y_perbin = []
    return x_accumulator, y_mu, y_25, y_75


def collapse_points(cs_diff, out_gt_diff):
    cs_diff_collapsed =[]
    out_gt_diff_collapsed = []
    for ix, iy in zip(cs_diff, out_gt_diff):
        if ix < -10:
            cs_diff_collapsed.append(-ix)
            out_gt_diff_collapsed.append(-iy)
        else:
            cs_diff_collapsed.append(ix)
            out_gt_diff_collapsed.append(iy)
    return cs_diff_collapsed, out_gt_diff_collapsed


def screen(r1, lambda1, theta, r1min=None, r1max=None, lambda1min=None, lambda1max=None, thetamin=None, thetamax=None):
    if np.array(r1).size > 1:
        cond = np.ones_like(r1).astype(np.bool)
    else:
        cond = True
    if r1min is not None:
        cond = cond * (r1 > r1min)
    if r1max is not None:
        cond = cond * (r1 < r1max)
    if lambda1min is not None:
        cond = cond * (lambda1 > lambda1min)
    if lambda1max is not None:
       cond = cond * (lambda1 < lambda1max)
    if thetamin is not None:
        cond = cond * ((theta > thetamin) | (theta > thetamin+180))
    if thetamax is not None:
        cond = cond * (theta < thetamax)
    return cond


# im_sub_path, im_fn, iimg,
# r1, theta1, lambda1, shift1,
# r2, theta2, lambda2, shift2, dual_center):


def main():
    import matplotlib.pyplot as plt

    ### ASSUME OUTPUT FILE AND META ARE CO-ALIGNED
    center_gt = []
    plaid_gt = []
    surround_gt = []
    predictions = []

    file_path = '/Users/drewlinsley/Documents/test_gratings'
    file_name =  sys.argv[1]
    if len(sys.argv) > 2:
        h = int(sys.argv[2])
        w = int(sys.argv[3])
        save = sys.argv[4] == 'True'
    else:
        h, w = 0, 0
        save = False
    out_data = np.load(os.path.join(file_path, file_name), allow_pickle=True, encoding="latin1")

    out_data_arr = out_data['test_dict'].copy()
    meta_arr = np.reshape(np.load('tb_stim_outputs/1.npy', allow_pickle=True), [-1, 12])

    thetas = meta_arr[:, 4].astype(np.float32)
    rs = meta_arr[:, 3].astype(np.float32)
    plaids = meta_arr[:, -1].astype(np.float32)
    unique_thetas = np.unique(thetas)
    unique_rs = np.unique(rs)
    unique_plaids = np.unique(plaids)


    image_paths = np.asarray([x['image_paths'][0].split(os.path.sep)[-1] for x in out_data_arr])
    target_image_paths = meta_arr[:, 1]
    assert np.all(image_paths == target_image_paths)

    responses = []
    H, W = 224, 224
    for d in out_data_arr:
        responses.append(d['ephys'][0, H // 2, W // 2])
    responses = np.asarray(responses)
    import ipdb;ipdb.set_trace()


    # for t in unique_thetas:
    #     plaid_mask = plaids == 0
    #     theta_mask = thetas == t
    #     overlap_mask = np.logical_and(plaid_mask, theta_mask)
    # plaid_selections = np.arange(55, 66)
    plaid_selections = [0]
    overlap_mask = np.in1d(plaids, plaid_selections)
    sel_data = out_data_arr[overlap_mask]
    sel_data = np.asarray([x['ephys'] for x in sel_data])  # .squeeze(1)
    import ipdb;ipdb.set_trace()

    for t in unique_thetas:
        plaid_mask = plaids == 0
        theta_mask = thetas == t
        overlap_mask = np.logical_and(plaid_mask, theta_mask)
        sel_data = out_data_arr[overlap_mask]
        a = 2



    f = plt.figure(figsize=(4,4))
    axarr = f.subplots(4,4) #(4, 4)
    theta_list = np.linspace(22.5, 67.5, 5)
    r1_list = np.linspace(100, 120, 5).astype(float) / 2
    for ir, rmin in enumerate(r1_list):
        import ipdb;ipdb.set_trace()
        for ith, thetamin in enumerate(theta_list):
            it_center_gt = []
            it_plaid_gt = []
            it_surround_gt = []
            it_predictions = []

            cond = screen(meta_arr[:,3].astype(np.float), meta_arr[:,5].astype(np.float), meta_arr[:,4].astype(np.float),
                          r1min=rmin, r1max=rmin+2.5, lambda1min=None, lambda1max=None, thetamin=thetamin, thetamax=thetamin+5)
            for i in range(out_data_arr.size):

                out_deg = ((np.arctan2(out_data_arr[i]['logits'][0, 0], out_data_arr[i]['logits'][0, 1])) * 180 / np.pi) % 180
                label_deg = ((np.arctan2(out_data_arr[i]['labels'][0, 0], out_data_arr[i]['labels'][0, 1])) * 180 / np.pi) % 180

                # r1, r2 ~ [40, 120], r2 = 2*r1
                # lambda1, lambda2~ [30 90]
                #
                # [im_sub_path, im_fn, iimg, r1, theta1, lambda1, shift1, r2, theta2, lambda2, shift2]
                if cond[i]:
                    it_center_gt.append(meta_arr[i, 4].astype(np.float))
                    it_plaid_gt.append(meta_arr[i, -1].astype(np.float))
                    it_surround_gt.append(meta_arr[i, 8].astype(np.float))
                    it_predictions.append(out_deg)

    import ipdb;ipdb.set_trace()
    a = 2

if __name__ == '__main__':
    main()


