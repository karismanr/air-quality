import time
import board
import busio
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO
import pyrebase
import csv
import joblib
from datetime import datetime

# Load Random Forest model with joblib
model = joblib.load('random_forest_model.pkl')

# Setup sensor DHT22 menggunakan adafruit_dht
dhtDevice = adafruit_dht.DHT22(board.D4)

# Setup I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Setup ADS1115
ads = ADS.ADS1115(i2c)
chan_mq2 = AnalogIn(ads, ADS.P0)
chan_mq135 = AnalogIn(ads, ADS.P1)

# Setup GPIO for Buzzer and LEDs
BUZZER_PIN = 17
RED_LED_PIN = 16
GREEN_LED_PIN = 20
YELLOW_LED_PIN = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_LED_PIN, GPIO.OUT)

# Threshold for gas leakage detection (MQ2)
GAS_THRESHOLD = 8000  # Adjust this value based on calibration

# Location of the Raspberry Pi
LOCATION = "RUANG TAMU"

# Konfigurasi Firebase
firebase_config = {
    "apiKey": "YOUR_API_KEY_HERE",
    "authDomain": "air-quality-732f8.firebaseapp.com",
    "databaseURL": "https://air-quality-732f8-default-rtdb.firebaseio.com",
    "storageBucket": "air-quality-732f8.appspot.com"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Create or open the CSV file and write the headers if it doesn't exist
csv_file = '../project/data.csv'
with open(csv_file, mode='a', newline='') as file:
    writer = csv.writer(file)
    if file.tell() == 0:
        writer.writerow(["timestamp", "location", "temperature", "humidity", "gas_leakage_value", "pm10", "so2", "co", "o3", "no2", "air_quality_category"])

# Function to read sensors
def read_sensors():
    try:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
    except RuntimeError as error:
        print(f"Failed to retrieve data from DHT22 sensor: {error}")
        temperature, humidity = None, None

    mq2_value = chan_mq2.value
    mq135_value = chan_mq135.value

    return temperature, humidity, mq2_value, mq135_value

# Function to convert MQ135 sensor values to various pollutants concentrations (ppm)
def mq135_to_concentrations(mq135_value):
    return {
        "pm10": mq135_value * 0.02,
        "so2": mq135_value * 0.015,
        "co": mq135_value * 0.05,
        "o3": mq135_value * 0.01,
        "no2": mq135_value * 0.025
    }

# Function to control buzzer and LEDs
def control_alerts(temperature, mq2_value):
    if temperature is not None:
        if temperature < 18 or temperature > 32:
            GPIO.output(RED_LED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        elif 19 <= temperature <= 27:
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
            GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        elif 28 <= temperature <= 31:
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)

    if mq2_value > GAS_THRESHOLD:
        print("AWAS ADA GAS BOCOR!")
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
    else:
        GPIO.output(BUZZER_PIN, GPIO.LOW)

# Function to save data to CSV
def save_to_csv(data):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

# Function to send data to Firebase
def send_to_firebase(path, data):
    try:
        db.child(f"sensor_data/{path}").set(data)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to send data to Firebase: {e}")

# Function to make air quality prediction using the Random Forest model
def predict_air_quality(concentrations, temperature, humidity, location, timestamp):
    # Converting timestamp to datetime
    timestamp = datetime.fromtimestamp(timestamp)
    
    # Extracting time features
    year = timestamp.year
    month = timestamp.month
    day = timestamp.day
    hour = timestamp.hour

    # One-hot encoding the location
    location_dict = {"RUANG TAMU": 0, "RUANG KELUARGA": 1}  # Adjust based on actual locations used in training
    location_value = location_dict.get(location, 0)

    # Creating feature vector
    feature_vector = [
        temperature,
        humidity,
        concentrations["pm10"],
        concentrations["so2"],
        concentrations["co"],
        concentrations["o3"],
        concentrations["no2"],
        year,
        month,
        day,
        hour,
        location_value
    ]
    prediction = model.predict([feature_vector])
    return prediction[0]

# Main loop
try:
    while True:
        temperature, humidity, mq2_value, mq135_value = read_sensors()
        timestamp = int(time.time())
        
        concentrations = mq135_to_concentrations(mq135_value)
        air_quality_category = predict_air_quality(concentrations, temperature, humidity, LOCATION, timestamp)
        
        print(f"Location: {LOCATION}")
        if temperature is not None and humidity is not None:
            print(f"Temp: {temperature:.1f}C  Humidity: {humidity:.1f}%")
        print(f"Gas Leakage Value: {mq2_value}")
        print(f"Air Quality Category: {air_quality_category}")
        
        control_alerts(temperature, mq2_value)

        csv_data = [
            timestamp,
            LOCATION,
            temperature,
            humidity,
            mq2_value,
            concentrations["pm10"],
            concentrations["so2"],
            concentrations["co"],
            concentrations["o3"],
            concentrations["no2"],
            air_quality_category
        ]
        save_to_csv(csv_data)

        dht22_data = {
            "location": LOCATION,
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": timestamp
        }
        send_to_firebase("dht22", dht22_data)
        
        gas_data = {
            "location": LOCATION,
            "gas_leakage_value": mq2_value,
            "timestamp": timestamp
        }
        send_to_firebase("mq2", gas_data)
        
        air_quality_data = {
            "location": LOCATION,
            "pm10": concentrations["pm10"],
            "so2": concentrations["so2"],
            "co": concentrations["co"],
            "o3": concentrations["o3"],
            "no2": concentrations["no2"],
            "air_quality_category": air_quality_category,
            "timestamp": timestamp
        }
        send_to_firebase("air_quality", air_quality_data)
        
        if mq2_value > GAS_THRESHOLD:
            gas_leak_warning = {
                "location": LOCATION,
                "warning": "AWAS ADA GAS BOCOR!",
                "gas_leakage_value": mq2_value,
                "timestamp": timestamp
            }
            send_to_firebase("gas_leak_warning", gas_leak_warning)
        
        time.sleep(2)

except KeyboardInterrupt:
    print("Program stopped by User")
finally:
    GPIO.cleanup()
