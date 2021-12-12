#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 14:44:17 2021

@author: atimans
"""

import numpy as np
import torch
from sklearn.metrics import roc_curve, roc_auc_score, RocCurveDisplay, accuracy_score

from utils import load_model, load_data, get_path


def main():

    BATCH_SIZE = 10
    model, model_name, device = load_model("DetectorNet", "checkpoints/checkpoint.pt")

    test_path = get_path("Alex", "test")
    test_data = load_data(test_path, BATCH_SIZE)

    evaluate(model, model_name, test_data, device)


def evaluate(model, model_name, dataloader, device):
    """Obtain predictions for given dataset/loader and compute relevant metrics."""

    model.eval()
    y_true, y_pred = np.array([]), np.array([])
    print("\nCollecting predictions...")

    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            out = model(X)
            y_pred = np.append(y_pred, out.numpy()) #proba class 1
            y_true = np.append(y_true, y.numpy())

    assert y_true.shape == y_pred.shape, "y_true, y_pred of unequal length."
    print(f"Performance metrics for {model_name}:")
    roc_auc(y_true, y_pred, model_name)
    accuracy(y_true, y_pred, binary_thresh=0.5)

    return y_true, y_pred


def roc_auc(y_true, y_pred, model_name, plot=True):
    """ROC AUC and optional ROC curve plot."""

    auc = roc_auc_score(y_true, y_pred, labels=[0,1])
    print(f"AUC: {auc:.6f}")
    if plot:
        fpr, tpr, thr = roc_curve(y_true, y_pred)
        roc_plot = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=auc,
                                   estimator_name=model_name,
                                   pos_label=1)
        roc_plot.plot()


def accuracy(y_true, y_pred, binary_thresh=0.5):
    """Accuracy for a given decision threshold."""

    print(f"Assign class 1 for probabilities >={binary_thresh}")
    y_pred[y_pred >= binary_thresh] = 1
    y_pred[y_pred < binary_thresh] = 0
    acc = accuracy_score(y_true, y_pred)
    print(f"Accuracy: {acc:.4f}")


if __name__ == "__main__":
    main()