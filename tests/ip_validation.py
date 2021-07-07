import unittest

# As our project contains several packages under ../src
    # we are adding said directory to python's path so
    # that the coloured_formatter class can be imported.
import sys
sys.path.insert(0, 'src/')

from docker_virt_net.config_parser import validate_subnet_addresses
from docker_virt_net.config_parser import ConfError

class TestColours(unittest.TestCase):
    def test_bad_ip(self):
        self.assertRaises(ConfError, validate_subnet_addresses, {"subnets": {"A": {"address": "10.0.-1.0/24"}}})

    def test_bad_format(self):
        self.assertRaises(ConfError, validate_subnet_addresses, {"subnets": {"A": {"address": "10.0.1.0"}}})

    def test_bad_mask(self):
        self.assertRaises(ConfError, validate_subnet_addresses, {"subnets": {"A": {"address": "10.0.1.0/40"}}})

    def test_good_ip(self):
        try:
            validate_subnet_addresses({"subnets": {"A": {"address": "10.0.1.0/24"}}})
        except:
            self.assertEqual(True, False)
        else:
            self.assertEqual(True, True)

if __name__ == '__main__':
    unittest.main()
