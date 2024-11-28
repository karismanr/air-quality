import Adafruit_DHT
import time
import RPi.GPIO as GPIO

# Definisikan pin yang terhubung ke sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 18  # Sesuaikan dengan pin yang digunakan

# Definisikan pin yang terhubung ke LED
GREEN_LED_PIN = 24  # Pin GPIO untuk LED hijau
YELLOW_LED_PIN = 23  # Pin GPIO untuk LED kuning
RED_LED_PIN = 22  # Pin GPIO untuk LED merah

# Waktu tunggu antara pembacaan (detik)
DELAY_SECONDS = 2

def setup_gpio():
    # Inisialisasi GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
    GPIO.setup(YELLOW_LED_PIN, GPIO.OUT)
    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)

def read_dht_sensor():
    # Membaca data dari sensor
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return humidity, temperature

def update_leds(temperature):
    if 23 <= temperature <= 27:
        # Suhu normal - LED hijau menyala
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
    elif 20 <= temperature < 23 or 27 < temperature <= 30:
        # Suhu moderate - LED kuning menyala
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
    else:
        # Suhu tidak normal - LED merah menyala
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.HIGH)

def main():
    setup_gpio()
    print("Starting DHT22 sensor reading...")
    try:
        while True:
            humidity, temperature = read_dht_sensor()
            if humidity is not None and temperature is not None:
                # Menampilkan hasil pembacaan
                print("Temperature: {:.1f}°C, Humidity: {:.1f}%".format(temperature, humidity))
                # Update LED berdasarkan suhu
                update_leds(temperature)
            else:
                print("Failed to retrieve data from sensor.")
                # Matikan semua LED jika gagal membaca
                GPIO.output(GREEN_LED_PIN, GPIO.LOW)
                GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
                GPIO.output(RED_LED_PIN, GPIO.LOW)
            
            # Tunggu sebelum membaca kembali
            time.sleep(DELAY_SECONDS)
            
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Reset semua pin GPIO
        GPIO.cleanup()
        
if __name__ == "__main__":
    main()
