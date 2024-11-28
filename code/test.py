import time
import Adafruit_DHT
import Adafruit_ADS1x15
import RPi.GPIO as GPIO

# Setup sensor DHT22
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# Setup ADS1115
adc = Adafruit_ADS1x15.ADS1115()
GAIN = 1

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
GAS_THRESHOLD = 6000  # Adjust this value based on calibration

# Location of the Raspberry Pi
LOCATION = "RUANG TAMU"

# Maximum pollutant values for air quality categories (ppm)
MAX_POLLUTANT_VALUES = {
    "PM10": 80,  # µg/m³
    "SO2": 60,  # ppm
    "CO": 200,  # ppm
    "O3": 40,  # ppm
    "NO2": 100  # ppm
}

# Function to read DHT22 sensor
def read_dht22():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        return humidity, temperature
    else:
        return None, None

# Function to read ADS1115 sensor
def read_ads1115(channel):
    try:
        return adc.read_adc(channel, gain=GAIN)
    except Exception as e:
        print(f"Failed to read ADS1115 on channel {channel}: {e}")
        return None

# Function to convert MQ135 sensor values to various pollutants concentrations (ppm)
def mq135_to_pm10(mq135_value):
    return mq135_value * 0.02  # Placeholder conversion

def mq135_to_so2(mq135_value):
    return mq135_value * 0.015  # Placeholder conversion

def mq135_to_co(mq135_value):
    return mq135_value * 0.05  # Placeholder conversion

def mq135_to_o3(mq135_value):
    return mq135_value * 0.01  # Placeholder conversion

def mq135_to_no2(mq135_value):
    return mq135_value * 0.025  # Placeholder conversion

# Functions to control buzzer and LEDs
def buzz_on():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)

def buzz_off():
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def led_red_on():
    GPIO.output(RED_LED_PIN, GPIO.HIGH)

def led_red_off():
    GPIO.output(RED_LED_PIN, GPIO.LOW)

def led_green_on():
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH)

def led_green_off():
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)

def led_yellow_on():
    GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)

def led_yellow_off():
    GPIO.output(YELLOW_LED_PIN, GPIO.LOW)

# Function to determine air quality category
def determine_air_quality(pm10, so2, co, o3, no2):
    max_values = MAX_POLLUTANT_VALUES
    if pm10 <= max_values["PM10"] and so2 <= max_values["SO2"] and co <= max_values["CO"] and o3 <= max_values["O3"] and no2 <= max_values["NO2"]:
        return "Baik"
    elif pm10 <= 1.5 * max_values["PM10"] and so2 <= 1.5 * max_values["SO2"] and co <= 1.5 * max_values["CO"] and o3 <= 1.5 * max_values["O3"] and no2 <= 1.5 * max_values["NO2"]:
        return "Sedang"
    else:
        return "Tinggi"

# Main loop
try:
    while True:
        # Read DHT22 sensor
        humidity, temperature = read_dht22()
        if humidity is not None and temperature is not None:
            print(f"Location: {LOCATION}")
            print(f"Temp: {temperature:.1f}C  Humidity: {humidity:.1f}%")
            
            # Control LEDs based on temperature
            if temperature < 18 or temperature > 32:
                led_red_on()
                led_green_off()
                led_yellow_off()
            elif 19 <= temperature <= 27:
                led_red_off()
                led_green_on()
                led_yellow_off()
            elif 28 <= temperature <= 31:
                led_red_off()
                led_green_off()
                led_yellow_on()
        else:
            print("Failed to retrieve data from DHT22 sensor")

        # Read MQ2 sensor (connected to A0)
        mq2_value = read_ads1115(0)
        if mq2_value is not None:
            print(f"Gas Leakage Value: {mq2_value}")

        # Read MQ135 sensor (connected to A1)
        mq135_value = read_ads1115(1)
        if mq135_value is not None:
            print(f"MQ135 Sensor Value: {mq135_value}")

            # Calculate pollutants concentrations from MQ135 sensor value
            pm10_concentration = mq135_to_pm10(mq135_value)
            so2_concentration = mq135_to_so2(mq135_value)
            co_concentration = mq135_to_co(mq135_value)
            o3_concentration = mq135_to_o3(mq135_value)
            no2_concentration = mq135_to_no2(mq135_value)
            
            print(f"PM10 Concentration: {pm10_concentration:.2f} ppm")
            print(f"SO2 Concentration: {so2_concentration:.2f} ppm")
            print(f"CO Concentration: {co_concentration:.2f} ppm")
            print(f"O3 Concentration: {o3_concentration:.2f} ppm")
            print(f"NO2 Concentration: {no2_concentration:.2f} ppm")

            # Determine air quality category
            air_quality_category = determine_air_quality(pm10_concentration, so2_concentration, co_concentration, o3_concentration, no2_concentration)
            print(f"Air Quality Category: {air_quality_category}")

        # Check for gas leakage
        if mq2_value is not None and mq2_value > GAS_THRESHOLD:
            print("AWAS ADA GAS BOCOR!")
            buzz_on()
        else:
            buzz_off()

        time.sleep(2)

except KeyboardInterrupt:
    print("Program stopped by User")
finally:
    GPIO.cleanup()
