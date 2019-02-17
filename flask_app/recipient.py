class Recipient:
    def __init__(self, username, name, coordinates):
        self.name = name
        self.first, self.last = name.split()
        self.username = username
        self.coordinates = coordinates
        self.x, self.y = coordinates

    def __str__(self):
        return "Recipient@({x},{y}) [{name}]".format(
            x=self.x,
            y=self.y,
            name=self.name,
        )

    def __repr__(self):
        return "Recipient@({x},{y}) [{name}]".format(
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
            return [Recipient.from_params(recipient)
                    for recipient in f.readlines()]

# offices = Office.from_file("recipients.txt")
#
# print(offices)

# with open("recipients.txt") as f:
#     txt = [line.split(',') for line in map(str.strip, f.readlines())]
#     offices = [(name, (int(x), int(y))) for name, x, y in txt]
#     del txt
