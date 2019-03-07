#! /usr/bin/env python3

from office import Office
import json

class Map():
    def __init__(self, size=(10,10)):

        # Store dimensions of office space (default is 10x10)
        self.xlim = size[0]
        self.ylim = size[1]

        # We always have a 'home' at (0,0)
        self.home = Office()

        # Offices are stored in a hash table {coordinates : office}
        self.offices = {(0,0) : self.home}

    def addJsonFile(self, json_file):
        json_data = json.loads(json_file)
        for office in json_data['offices']:
            self.addOffice(Office(office['name'], (office['x_cord'], office['y_cord'])))

    def addOffices(self, new_offices):
        ''' Add a list of offices '''
        for new_office in new_offices:
            self.addOffice(new_office)

    def delOffices(self, old_offices):
        ''' Delete a list of offices '''
        for old_office in old_offices:
            self.delOffice(old_office)

    def addOffice(self, new_office):
        ''' Add a new office to the map '''

        # If office already exists stop
        if new_office.coords in self.offices:
            print("ERROR: Office already exists.")
            return

        # Otherwise we add the new office and find its neighbours
        self.offices[new_office.coords] = new_office
        self.addNeighbours(new_office)

    def delOffice(self, old_office):
        ''' Delete an office from the map '''

        if old_office.coords in self.offices:
            # We update the changes to neighbours and delete this office
            self.delNeighbours(old_office)
            del self.offices[old_office.coords]
        else:
            print("ERROR: Office not found.")

    def addNeighbours(self, office):
        ''' Find all existing neighbours of a new office (max of 4)
            We then also update the map to account for this new office'''

        (x, y) = office.coords

        # Find left neighbour
        for i in range(x-1, -1, -1):
            if (i, y) in self.offices:
                office.setLeftNeighbour(self.offices[(i, y)])
                # This means we update the right neighbour of this office
                self.offices[(i, y)].setRightNeighbour(office)
                break
        # Find right neighbour
        for i in range(x+1, self.xlim+1):
            if (i, y) in self.offices:
                office.setRightNeighbour(self.offices[(i, y)])
                # This means we update the left neighbour of this office
                self.offices[(i, y)].setLeftNeighbour(office)
                break
        # Find upper neighbour
        for i in range(y+1, self.ylim+1):
            if (x, i) in self.offices:
                office.setUpperNeighbour(self.offices[(x, i)])
                # This means we update the lower neighbour of this office
                self.offices[(x, i)].setLowerNeighbour(office)
                break
        # Find lower neighbour
        for i in range(y-1, -1, -1):
            if (x, i) in self.offices:
                office.setLowerNeighbour(self.offices[(x, i)])
                # This means we update the upper neighbour of this office
                self.offices[(x, i)].setUpperNeighbour(office)
                break

    def delNeighbours(self, office):
        ''' Update the map to account for the deletion of an office '''

        # We need to reassign the neighbours of the neighbouring offices
        if office.right is not None:
            office.right.setLeftNeighbour(office.left)
        if office.left is not None:
            office.left.setRightNeighbour(office.right)
        if office.upper is not None:
            office.upper.setLowerNeighbour(office.lower)
        if office.lower is not None:
            office.lower.setUpperNeighbour(office.upper)

    def neighbourDict(self):
        ''' Return a dictionary of {office : [neighbours]} in coordinates '''
        ndict = {}
        for key in self.offices.keys():
            ndict[key] = [office.coords for office in self.offices[key].getNeighbours().values() if office is not None]
        return ndict
