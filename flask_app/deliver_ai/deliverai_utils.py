import os
from datetime import datetime

from deliver_ai import server


class Person:
    def __init__(self, username, name, coordinates):
        self.name = name  # type: str
        self.first, self.last = name.split()
        self.username = username  # type: str
        self.coordinates = coordinates  # type: (int, int)
        self.x, self.y = coordinates

    def __str__(self):
        return "{name}@({x},{y})".format(
            x=self.x,
            y=self.y,
            name=self.name,
        )

    def __repr__(self):
        return "{name}@({x},{y})".format(
            x=self.x,
            y=self.y,
            name=self.name,
        )

    @classmethod
    def from_params(cls, params):
        username, name, x, y = map(str.strip, params.split(','))
        return cls(username, name, (int(x), int(y)))

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            return [Person.from_params(person)
                    for person in f.readlines()]


class Ticket:
    def __init__(self, pickup_time, sender, recipient, message,
                 created=datetime.now()):
        self.created = created
        self.pickup_time = pickup_time  # type: datetime
        self.sender = sender  # type: Person
        self.recipient = recipient  # type: Person
        self.message = message  # type: str

    def __repr__(self):
        return "Ticket[{}] {} --> {}".format(
            self.pickup_time,
            self.sender,
            self.recipient,
        )

    def to_params(self):
        return {
            'created': ('Created on', self.created),
            'pickup_time': ('Pickup time', self.pickup_time),
            'sender': ('Sender', self.sender),
            'recipient': ('Recipient', self.recipient),
            'message': ('Message', self.message),
        }


class Bot:
    def __init__(self, uid, name):
        self.uid = uid  # type: str
        self.name = name
        self.battery = 42

    def __str__(self):
        return "Bot '{name}' [{uid}]".format(
            name=self.name,
            uid=self.uid,
        )

    def __repr__(self):
        return "Bot '{name}' [{uid}]".format(
            name=self.name,
            uid=self.uid,
        )

    @classmethod
    def from_params(cls, params):
        uid, name = map(str.strip, params.split(','))
        return cls(uid, name)

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            return [Bot.from_params(bot)
                    for bot in f.readlines()]


path = os.path.dirname(os.path.abspath(__file__))

people = Person.from_file(os.path.join(path, '..', 'people.txt'))
people_map = {person.username: person for person in people}
user = people_map.pop("ash.ketchum", None)

# robots
bots = Bot.from_file(os.path.join(path, '..', "bots.txt"))

tickets = []

tcp_server = server.get_server()
