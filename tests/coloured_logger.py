import unittest

# As our project contains several packages under ../src
    # we are adding said directory to python's path so
    # that the coloured_formatter class can be imported.
import sys
sys.path.insert(0, 'src/')

import logging
from docker_virt_net.coloured_log_formatter import coloured_formatter

class TestColours(unittest.TestCase):
    def test_colour_output(self):
        # Adapted from Sergey Pleshakov's answer on
            # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output

        logger = logging.getLogger("foo")
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(coloured_formatter())

        logger.addHandler(ch)

        logger.debug("DBG message :P")
        logger.info("INFO message :)")
        logger.warning("WARNING message :|")
        logger.error("ERROR message :(")
        logger.critical("CRITICAL message :'(")

        self.assertEqual(True, True)

if __name__ == '__main__':
    unittest.main()
