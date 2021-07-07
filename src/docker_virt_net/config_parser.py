import json, jsonschema, pathlib, logging, sys, networkx

log = logging.getLogger(__name__)

class ConfError(Exception):
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause

def parse_config(conf, schema = "net.schema"):
    """Loads the desired network configuration and performs initial validation.

        Args:
            conf (str): The user-specified path to the desired network configuration file.
            schema (str, optional): The JSON schema to validate the configuration against.

        Returns:
            networkx.Graph: A graph representing the desired virtual network.
    """
    try:
        net_conf = load_conf(conf, schema)
        log.info(f"Correctly loaded {conf}. Time to check it's okay...")
        validate_subnet_addresses(net_conf)
    except ConfError as err:
        log.critical(err.cause)
        sys.exit(-1)

def load_conf(conf_path, schema = "net.schema"):
    """Loads the desired network configuration and performs initial validation.

        Args:
            conf (str): The user-specified path to the desired network configuration file.
            schema (str, optional): The JSON schema to validate the configuration against.

        Returns:
            dictionary: The contents of the file specified by `conf`.
    """
    try:
        net_conf = json.loads(pathlib.Path(conf_path).read_text())
        jsonschema.validate(
            net_conf,
            schema = json.loads((pathlib.Path(__file__).parent / schema).read_text())
        )
    except FileNotFoundError as err:
        raise ConfError(f"Couldn't find file {err.filename}")
    except json.JSONDecodeError as err:
        raise ConfError(f"Could not decode {conf_path}: {err.msg} @ line {err.lineno}")
    except jsonschema.ValidationError as err:
        raise ConfError(f"Network configuration {conf_path} is NOT VALID: {err.message}")

    return net_conf

def validate_subnet_addresses(conf):
    """Validates the CIDR addresses for every subnet.

    Args:
        conf (dictionary): The network configuration whose addresses are to
            be validated.
    """
    for subnet in conf['subnets'].values():
        try:
            ip, mask = subnet['address'].split('/')
            if len(ip.split('.')) != 4:
                raise ValueError
            for oct in ip.split('.'):
                ioct = int(oct)
                if not 0 <= ioct <= 255:
                    raise ValueError
            if not 1 <= int(mask) <= 32:
                raise ValueError
        except ValueError:
            raise ConfError(f"IPv4 subnet range in CIDR notation {subnet['address']} is not valid.")
