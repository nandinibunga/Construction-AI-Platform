import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Dummy construction data (replace with real data)
X = np.array([[25, 30], [30, 45], [20, 35]])  # [planned_days, actual_days]
y = np.array([5, 15, 2])                      # delay_days

model = RandomForestRegressor()
model.fit(X, y)
joblib.dump(model, 'model.pkl')  