#! /usr/bin/env python3

class Office():
    def __init__(self, name="HOME", coords=(0,0)):
        self.name = name
        self.coords = coords
        self.right = None
        self.left = None
        self.upper = None
        self.lower = None

    def setRightNeighbour(self, office):
        self.right = office
    
    def setLeftNeighbour(self, office):
        self.left = office

    def setUpperNeighbour(self, office):
        self.upper = office

    def setLowerNeighbour(self, office):
        self.lower = office

    def getNeighbours(self):
        return {"right" : self.right,
                "left" : self.left,
                "upper" : self.upper,
                "lower" : self.lower}