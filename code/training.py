import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import joblib

# Memuat data dari file CSV
file_path = 'airquality.csv'
data = pd.read_csv(file_path)

# Menampilkan beberapa baris dari data untuk inspeksi awal
print(data.head())

# Periksa kolom yang tersedia dalam dataset
print(data.columns)

# Memastikan bahwa kolom target 'Air Quality Category' ada dalam dataset
target_column = 'Air Quality Category'
if target_column not in data.columns:
    raise ValueError(f"Kolom '{target_column}' tidak ditemukan dalam dataset.")

# Fitur yang digunakan
features = ['Temperature', 'Humidity', 'Gas Leakage Value', 'PM10', 'SO2', 'CO', 'O3', 'NO2', 'Location', 'Timestamp']

# Memisahkan data menjadi fitur (X) dan label (y)
X = data[features]
y = data[target_column]

# Mengonversi 'Location' menjadi numerik menggunakan one-hot encoding
X = pd.get_dummies(X, columns=['Location'], drop_first=True)

# Mengonversi 'Timestamp' menjadi fitur waktu (misalnya, tahun, bulan, hari, jam)
X['Timestamp'] = pd.to_datetime(X['Timestamp'])
X['Year'] = X['Timestamp'].dt.year
X['Month'] = X['Timestamp'].dt.month
X['Day'] = X['Timestamp'].dt.day
X['Hour'] = X['Timestamp'].dt.hour
X = X.drop(columns=['Timestamp'])

# Check the distribution of the condition
print(data[target_column].value_counts())

# Membagi data menjadi set pelatihan dan pengujian
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Melatih model Random Forest dengan hyperparameter terbaik
best_model = RandomForestClassifier(bootstrap=False, max_depth=None, min_samples_leaf=1, min_samples_split=2, n_estimators=100, random_state=42)
best_model.fit(X_train, y_train)

# Mengevaluasi performa model
y_pred = best_model.predict(X_test)

# Menggunakan classification_report dengan parameter zero_division=0 untuk menghilangkan peringatan
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred, zero_division=0))

# Analisis kesalahan klasifikasi
misclassified_samples = X_test[y_test != y_pred]
misclassified_labels = y_test[y_test != y_pred]

# Simpan model ke file
joblib.dump(best_model, 'coba_model.pkl')

print("Misclassified samples:")
print(misclassified_samples)
print("True labels of misclassified samples:")
print(misclassified_labels)
print("Predicted labels of misclassified samples:")
print(y_pred[y_test != y_pred])
