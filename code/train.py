import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import numpy as np
import joblib

# Memuat data dari file CSV
file_path = 'Project-ML/data-new.csv'
data = pd.read_csv(file_path)

# Menampilkan beberapa baris dari data untuk inspeksi awal
print(data.head())

# Memisahkan data menjadi fitur (X) dan label (y)
features = ['rain', 'sound', 'temperature', 'humidity']
X = data[features]
y = data['condition']

# Check the distribution of the condition
print(data['condition'].value_counts())

# Membagi data menjadi set pelatihan dan pengujian
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Melatih model Random Forest dengan hyperparameter terbaik
best_model = RandomForestClassifier(bootstrap=False, max_depth=None, min_samples_leaf=1, min_samples_split=2, n_estimators=100, random_state=42)
best_model.fit(X_train, y_train)

# Mengevaluasi performa model
y_pred = best_model.predict(X_test)
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Menampilkan pentingnya fitur
importances = best_model.feature_importances_
indices = np.argsort(importances)[::-1]
features_sorted = [features[i] for i in indices]

plt.figure(figsize=(10, 6))
plt.title("Feature Importances")
plt.bar(range(X.shape[1]), importances[indices], align="center")
plt.xticks(range(X.shape[1]), features_sorted, rotation=45)
plt.xlim([-1, X.shape[1]])
plt.show()

# Analisis kesalahan klasifikasi
misclassified_samples = X_test[y_test != y_pred]
misclassified_labels = y_test[y_test != y_pred]

# Simpan model ke file
joblib.dump(best_model, 'Project-ML/random_forest_model.pkl')

print("Misclassified samples:")
print(misclassified_samples)
print("True labels of misclassified samples:")
print(misclassified_labels)
print("Predicted labels of misclassified samples:")
print(y_pred[y_test != y_pred])