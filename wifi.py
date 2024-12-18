# -*- coding: utf-8 -*-

import network
import sys
import time

def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    
    while True:
        if not sta_if.isconnected():
            print("Connection lost. Attempting to reconnect to Wi-Fi...")
            sta_if.active(True)
            try:
                sta_if.config(dhcp_hostname="My ProS3")
                sta_if.connect("ster", "elskerogkode")  # Wi-Fi credentials
            except Exception as err:
                sta_if.active(False)
                print("Error:", err)
                time.sleep(5)
                continue

            print("Reconnecting", end="")
            n = 0
            while not sta_if.isconnected():
                print(".", end="")
                time.sleep(1)
                n += 1
                if n == 60:
                    break

            if n == 60:
                sta_if.active(False)
                print("\nGiving up! Not connected!")
            else:
                print("\nReconnected with IP: ", sta_if.ifconfig()[0])
                break
        else:
            print(f"Already connected with IP: {sta_if.ifconfig()[0]}")
            break

if __name__ == "__main__":
    connect_wifi()
