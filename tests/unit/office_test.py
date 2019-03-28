from unittest import TestCase
from navigation.office import Office

class Office_Test(TestCase):
    def test_create_office(self):
        office = Office("HOME", (1, 2))
        self.assertEqual('HOME', office.name)
        self.assertEqual((1, 2), office.coords)


    def test_right_neighbour(self):
        office = Office("HOME", (1, 2))
        self.assertEqual(office, office)

    def test_left_neighbour(self):
        office = Office("NEW", (2, 2))
        self.assertEqual(office, office)

    def test_upper_neighbour(self):
        office = Office("Another", (3, 2))
        self.assertEqual(office, office)

    def test_lower_neighbour(self):
        office = Office("Low", (1, 2))
        self.assertEqual(office, office)


    def test_all_neighbours(self):
        office = Office("HOME", (1, 2))
        right = None
        left = None
        upper = None
        lower = None

        expected = {
            "right": right,
            "left": left,
            "upper": upper,
            "lower": lower,}

        self.assertDictEqual(expected, office.getNeighbours())
