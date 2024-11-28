import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Langkah 1: Memuat dan Memproses Data
# Memuat dataset (misalnya, data.csv)
df = pd.read_csv('airquality.csv')

# Melihat beberapa baris pertama dari dataset
print(df.head())

# Memisahkan kolom numerik dan kolom kategori
numeric_columns = ['Temperature', 'Humidity', 'Gas Leakage Value', 'PM10', 'SO2', 'CO', 'O3', 'NO2']
categorical_columns = ['Location', 'Timestamp']  # Kolom kategori yang perlu encoding

# Menangani nilai yang hilang untuk kolom numerik
df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].mean())

# Menangani nilai yang hilang untuk kolom kategori
df[categorical_columns] = df[categorical_columns].fillna(df[categorical_columns].mode().iloc[0])

# Menangani data kategori (encoding)
df = pd.get_dummies(df, columns=categorical_columns, drop_first=True)

# Memisahkan fitur dan target
X = df.drop('Air Quality Category', axis=1)  # Fitur
y = df['Air Quality Category']  # Target

# Langkah 2: Menyiapkan Data untuk Pelatihan dan Pengujian
# Membagi data menjadi data pelatihan dan pengujian
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Langkah 3: Membuat dan Melatih Model Machine Learning (Menggunakan Decision Tree)
# Membuat model
model = DecisionTreeClassifier(random_state=42)

# Melatih model
model.fit(X_train, y_train)

# Langkah 4: Mengevaluasi Model
# Menggunakan model untuk membuat prediksi
y_pred = model.predict(X_test)

# Menghitung akurasi dan laporan klasifikasi
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {accuracy}")
print(f"Classification Report:\n{report}")

# Langkah 5: Menyimpan Model yang Telah Dilatih
# Menyimpan model
joblib.dump(model, 'tes_model.sav')
