from datetime import datetime
import json


class Person:
    def __init__(self, username, name, coordinates):
        self.name = name  # type: str
        try:
            self.first, self.last = name.split()
        except ValueError:
            self.first, self.last = "", ""
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

    def json_dict(self):
        return {
            'name': self.name,
            'username': self.username,
            'x_coord': self.x,
            'y_coord': self.y,
        }

    def distance_to(self, other):
        if type(other) is not Person:
            return None
        else:
            return abs(self.x - other.x) + abs(self.y - other.y)

    @classmethod
    def from_params(cls, params):
        username, x, y = map(str.strip, params.split(','))
        name = " ".join(username.split('.')).title()
        return cls(username, name, (int(x), int(y)))

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            # return [Person.from_params(person) for person in json.load(f)]
            return [cls.from_params(person)
                    for person in f.readlines()]

    @classmethod
    def from_json(cls, json_str):
        j = json.loads(json_str)
        name = " ".join(j.username.split('.')).title()
        return cls(
            j.username,
            name,
            (int(j.x), int(j.y)),
        )

    @classmethod
    def from_json_file(cls, file):
        with open(file) as f:
            j = f.read()
        return [cls(
            p['username'],
            p['name'],
            (p['x_coord'], p['y_coord'])
        ) for p in json.loads(j)['offices'] if p]


class Progress:
    def __init__(self):
        self.stage = 0
        self.order_rank = (
            ('created', "created"),
            ('pickup', "pickup"),
            ('transit', "in transit"),
            ('delivered', "delivered"),
        )

    def next_stage(self):
        if 0 <= self.stage < 3:
            self.stage += 1
        else:
            raise Exception

    def get_stage(self):
        return self.order_rank[self.stage]

    def __repr__(self):
        return self.get_stage()


class Ticket:
    def __init__(self, pickup_time, sender, recipient, message,
                 created=None):
        self.id = \
            f'{datetime.now().strftime("%Y-%m-%d-%H%M%S")}_{sender.username}'
        self.pickup_time = pickup_time  # type: datetime
        self.sender = sender  # type: Person
        self.recipient = recipient  # type: Person
        self.message = message  # type: str
        self.status = Progress()
        self.pending = True
        self.accepted = None
        self.delivered = False
        if not created:
            self.created = datetime.utcnow()  # type: datetime

    def __repr__(self):
        return "Ticket[{}] {} --> {}".format(
            self.pickup_time,
            self.sender,
            self.recipient,
        )

    def progress(self):
        self.status.next_stage()

    def stage_text(self):
        return self.status.get_stage()[1]

    def to_params(self):
        return {
            'created': ('Created on', self.created),
            'pickup_time': ('Pickup time', self.pickup_time),
            'sender': ('Sender', self.sender),
            'recipient': ('Recipient', self.recipient),
            'message': ('Message', self.message),
            'status': ('Status', self.stage_text())
        }

    def to_json(self):
        return {
            'created': self.created.isoformat(),
            'pickup_time': self.pickup_time,
            'sender': self.sender.username,
            'recipient': self.recipient.username,
            'message': self.message,
            'status': self.stage_text(),
            'id': self.id,
        }


class TicketRegister:
    def __init__(self):
        self.tickets = []

    def new_ticket(self, ticket):
        self.tickets.append(ticket)

    # def get_tickets(self, user):
    #     return filter(lambda x: x.sender == user or x.recipient == user,
    #                   self.tickets)
    # if user in self.tickets:
    #     return self.tickets[user]

    def get_sent(self, user):
        return list(filter(lambda x: x.sender == user, self.tickets))

    def get_received(self, user):
        return list(filter(lambda x: x.recipient == user, self.tickets))

    def get_all_pending(self, user):
        return [ticket for ticket in self.get_received(user) if ticket.pending]


class Bot:
    def __init__(self, uid, name):
        self.uid = uid  # type: str
        self.name = name
        self.props = {
            'uid': uid,
            'name': name,
            'x_loc': 0,
            'y_loc': 0,
            'bearing': 0,
            'state': 'unknown',
            'battery_volts': 0.00,
            'battery_percent': 0,
            'dest': (0, 0),
            'route': "none",
        }

    def __str__(self):
        return "Bot '{name}' [{uid}] - {props}".format(
            name=self.name,
            uid=self.uid,
            props=self.props.items()
        )

    def __repr__(self):
        return str(self)

    def battery(self):
        # estimate battery % - between 5 and 8.21 Volt
        return max(0,
                   min(
                       round(100 * (self.props['battery_volts'] - 5) /
                             (8.21 - 5)),
                       100)
                   )

    def update_from_dict(self, props):
        for prop, val in props.items():
            self.props[prop] = val
        self.props['battery_percent'] = self.battery()

    def to_json(self):
        return json.dumps(self.props)

    @classmethod
    def from_params(cls, params):
        uid, name = map(str.strip, params.split(','))
        return cls(uid, name)

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            return {bot.name: bot for bot in [Bot.from_params(l)
                                              for l in f.readlines()]}


class Map:
    def __init__(self, offices=None):
        self.offices = offices  # type: dict[str: Person]

    def add_office(self, person):
        print(self.in_coordinates(person.coordinates))
        print(self.in_map(person))
        if self.in_map(person) or self.in_coordinates(person.coordinates):
            raise KeyError
        if person.coordinates == (0, 0):
            raise ValueError
        else:
            self.offices[person.username] = person

    def remove_office(self, person):
        if self.in_map(person):
            if type(person) is Person:
                person = person.username
            self.offices.pop(person)
        else:
            raise KeyError

    def distance(self, p1, p2):
        if not self.in_map(p1) and self.in_map(p2):
            return None
        else:
            return p1.distance_to(p2)

    def in_map(self, person):
        if type(person) is Person:
            person = person.username
        return person in self.offices

    def in_coordinates(self, coordinates):
        return list(filter(lambda x: x.coordinates == coordinates,
                           self.offices.values()))

    def get(self, person=None):
        if person:
            if self.in_map(person):
                return self.offices[person]
            else:
                raise KeyError
        return self.offices.copy()

    def get_without_me(self, me):
        # if me is Person:
        #     me = me.username
        m = self.get()
        if self.in_map(me):
            if type(me) is Person:
                me = me.username
            m.pop(me)
        return m

    def to_json(self):
        return json.dumps(
            {'offices': [o.json_dict() for o in self.offices.values()]}
        )

    def update(self, offices):
        self.offices = offices

    @classmethod
    def from_dict(cls, d):
        return Map(d)
