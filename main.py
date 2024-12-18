import ntptime
import wifi
import network
from umqtt.simple import MQTTClient
import time
import machine
import ujson

WIFI_SSID = 'ster'
WIFI_PASSWORD = 'elskerogkode'
MQTT_BROKER = '79.171.148.142'
MQTT_PORT = 1883
MQTT_TOPIC = 'parking/update'

MQTT_USERNAME = 'grp2'
MQTT_PASSWORD = 'ElskerOgKode321'

SENSOR_PIN = 33

sensor = machine.Pin(SENSOR_PIN, machine.Pin.IN)

vehicle_present = None

street_name = 'ELSKEROGKODE STREET'
between_streets = 'STER GADE - SURE SIMON AVENUE'
device_id = 3

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)  # Disable Wi-Fi to ensure a clean state
    time.sleep(1)
    wlan.active(True)   # Enable Wi-Fi again

    for attempt in range(5):  # Try 5 times before giving up
        print("Attempting to connect to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(30):  # Wait up to 30 seconds for connection
            if wlan.isconnected():
                print(f"Connected to Wi-Fi: {wlan.ifconfig()}")
                return True
            time.sleep(1)
        print(f"Connection attempt {attempt + 1} failed. Retrying...")
        wlan.active(False)  # Reset Wi-Fi for the next attempt
        time.sleep(2)
        wlan.active(True)

    print("Wi-Fi connection failed after multiple attempts.")
    return False


def send_vehicle_state(client, timestamp):
    global vehicle_present
    if vehicle_present is not None:
        payload = {
            'streetName': street_name,
            'betweenStreets': between_streets,
            'deviceId': device_id,
            'vehiclePresent': vehicle_present,
            'timestamp': timestamp
        }
        payload_json = ujson.dumps(payload)
        client.publish(MQTT_TOPIC, payload_json)
        print(f"Published JSON: {payload_json} to {MQTT_TOPIC}")

def synchronize_time():
    attempt = 0
    while attempt < 5:
        try:
            ntptime.host = "time.google.com"
            ntptime.settime()  # Sync with NTP server
            print("Time synchronized with NTP server.")
            return True
        except Exception as e:
            print(f"Failed to synchronize time: {e}")
            attempt += 1
            time.sleep(2)
    print("Giving up on time synchronization.")
    return False

def get_current_time():
    current_time = time.localtime(time.time() + 3600)
    return "{:02}:{:02}:{:02}".format(current_time[3], current_time[4], current_time[5])

def check_sensor_state():
    global vehicle_present
    sensor_value = sensor.value()
    new_state = (sensor_value == 0)

    if new_state != vehicle_present:
        vehicle_present = new_state
        timestamp = get_current_time()  # Get the current timestamp as HH:MM:SS
        print(f"Vehicle present: {vehicle_present} at {timestamp}")
        return timestamp
    return None

def connect_mqtt():
    client_id = f"esp32_{device_id}"
    client = MQTTClient(client_id, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWORD)
    try:
        client.connect()
        print("Connected to MQTT broker")
        return client
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return None

def main():
    while True:
        if not connect_wifi():
            print("Wi-Fi connection failed. Retrying...")
            time.sleep(5)
            continue

        if not synchronize_time():
            print("Time synchronization failed. Retrying...")
            time.sleep(5)
            continue

        mqtt_client = connect_mqtt()
        if mqtt_client is None:
            print("Unable to connect to MQTT broker. Retrying...")
            time.sleep(5)
            continue

        while True:
            try:
                print("Checking sensor state...")
                timestamp = check_sensor_state()
                if timestamp is not None:
                    send_vehicle_state(mqtt_client, timestamp)

                mqtt_client.check_msg()
                time.sleep(5)
            except Exception as e:
                print(f"Error occurred: {e}. Resetting and reconnecting...")
                break

try:
    main()
except KeyboardInterrupt:
    print("Program interrupted.")
