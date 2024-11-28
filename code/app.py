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
from flask import Flask, render_template, jsonify
from threading import Thread
import atexit

# Load Random Forest model with joblib
model = joblib.load('random_forest_model.pkl')

# Setup sensor DHT22 using adafruit_dht
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

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyAz56HKM6zZYCiVK59D90COwOzpxp6bcio",
    "authDomain": "air-quality-732f8.firebaseapp.com",
    "databaseURL": "https://air-quality-732f8-default-rtdb.firebaseio.com",
    "storageBucket": "air-quality-732f8.appspot.com"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Initialize Flask app
app = Flask(__name__)

# Global variable to store the latest sensor data
latest_sensor_data = {}

# Define CSV file name
csv_file = 'sensor_data.csv'

# Function to read sensors
def read_sensors():
    temperature = None
    humidity = None

    for _ in range(5):  # Try up to 5 times to get a valid reading
        try:
            temperature = dhtDevice.temperature
            humidity = dhtDevice.humidity
            if temperature is not None and humidity is not None:
                break
        except RuntimeError as error:
            print(f"Failed to retrieve data from DHT22 sensor: {error}")
            time.sleep(2)  # Wait before retrying

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
    except Exception as e:
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

# Route to render the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to get real-time data
@app.route('/realtime-data')
def realtime_data():
    return jsonify(latest_sensor_data)

# Function to update the sensor data
def update_sensor_data():
    global latest_sensor_data

    while True:
        temperature, humidity, mq2_value, mq135_value = read_sensors()
        timestamp = int(time.time())
        
        concentrations = mq135_to_concentrations(mq135_value)
        air_quality_category = predict_air_quality(concentrations, temperature, humidity, LOCATION, timestamp)
        
        latest_sensor_data = {
            'temperature': temperature,
            'humidity': humidity,
            'mq2_value': mq2_value,
            'pm10': concentrations["pm10"],
            'so2': concentrations["so2"],
            'co': concentrations["co"],
            'o3': concentrations["o3"],
            'no2': concentrations["no2"],
            'air_quality_category': air_quality_category,
            'timestamp': timestamp
        }
        
        control_alerts(temperature, mq2_value)
        
        save_to_csv([
            timestamp, temperature, humidity, mq2_value,
            concentrations["pm10"], concentrations["so2"],
            concentrations["co"], concentrations["o3"],
            concentrations["no2"], air_quality_category
        ])
        
        send_to_firebase(timestamp, latest_sensor_data)
        
        time.sleep(2)

# Clean up GPIO on exit
def cleanup_gpio():
    GPIO.cleanup()

atexit.register(cleanup_gpio)

# Start the sensor data update loop in a separate thread
sensor_thread = Thread(target=update_sensor_data)
sensor_thread.daemon = True
sensor_thread.start()

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
