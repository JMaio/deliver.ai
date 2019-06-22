import requests
import random
import time


def send_update(name='lion', battery=random.random() * 2.5 + 5,
                x=random.randint(-5, 5), y=random.randint(-5, 5)):
    r = requests.post(
        'http://localhost:5000/api/botinfo',
        params={
            'name': name,
            'battery_volts': battery,
            'x_loc': x,
            'y_loc': y,
        }
    )
    return r.text


if __name__ == "__main__":
    while True:
        print(send_update())
        time.sleep(5)
