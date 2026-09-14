import numpy as np
from datetime import datetime

def predict_subject(scores):
    if not scores:
        return None
    if len(scores) == 1:
        return round(scores[0], 1)
    
    x = np.arange(len(scores))
    weights = np.linspace(1, 2, len(scores))
    
    weighted_avg = np.average(scores, weights=weights)
    
    slope, intercept = np.polyfit(x, scores, 1)
    trend_prediction = slope * len(scores) + intercept
    
    predicted = 0.6 * weighted_avg + 0.4 * trend_prediction
    
    return round(max(0, min(100, predicted)), 1)