import unittest
from approximation import *


class ApproximationTest(unittest.TestCase):

    def test_create_approximate_location(self):
        real_location = Location(25.235, 65.632)
        fake_location = create_approximate_location(real_location, LOCATION_APPROXIMATION_RADIUS_KM)
        real_distance = get_distance(real_location, fake_location)

        self.assertTrue(0 < real_distance <= LOCATION_APPROXIMATION_RADIUS_KM)


if __name__ == '__main__':
    unittest.main()
