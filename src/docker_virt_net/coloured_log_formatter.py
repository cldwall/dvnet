import logging

# Adapted from Sergey Pleshakov's answer on
    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output

class coloured_formatter(logging.Formatter):
    # Check https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_(Control_Sequence_Introducer)_sequences
        # for a discussion on the nature of these sequences.
    reset    = "\033[0m"
    cyan     = "\033[38;2;0;255;255m"
    lime     = "\033[38;2;0;255;0m"
    orange   = "\033[38;2;255;128;0m"
    red      = "\033[38;2;255;0;0m"
    bold_red = "\033[38;2;255;0;0;1m"

    # Check https://docs.python.org/3/library/logging.html#logrecord-attributes
        # for a table containing the available fields.
    format = "%(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    formats = {
        logging.DEBUG:    cyan + format + reset,
        logging.INFO:     lime + format + reset,
        logging.WARNING:  orange + format + reset,
        logging.ERROR:    red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        """Wraps the incoming message between colours.

        This method leverages ANSI Escape Codes to colour
        incoming log messages.

        Args:
            record (logging.LogRecord): The log entry being formatted.

        Returns:
            str: The log entry with colours already applied.
        """

        log_format = self.formats[record.levelno]
        log_formatter = logging.Formatter(log_format)
        return log_formatter.format(record)
