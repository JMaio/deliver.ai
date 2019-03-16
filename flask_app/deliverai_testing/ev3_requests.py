import requests
import random
import time

if __name__ == "__main__":
    while True:
        r = requests.post(
            'http://localhost:5000/api/botinfo',
            params={
                'name': 'lion',
                'battery_volts': random.random() * 2.5 + 5,
                'x_loc': random.randint(-5, 5),
                'y_loc': -random.randint(-5, 5)
            }
        )
        print(r.text)
        time.sleep(5)
