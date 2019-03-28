from unittest import TestCase
from navigation.map import Map

class Map_test(TestCase):
    def test_init_map(self):
        map = Map(self)
        self.assertEqual((5, 5), map)


    def test_json(self):
        pass
    #to do

    def test_add_office(self):
        pass

    def test_del_office(self):
        pass

