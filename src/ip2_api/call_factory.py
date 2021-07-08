import subprocess
from .exceptions import IP2Error

def _call_factory(args, err_msg):
    try:
        subprocess.run(args, check = True)
    except subprocess.CalledProcessError as err:
        # Return codes as per:
            # https://manpages.debian.org/stretch/iproute2/ip.8.en.html
        if err.returncode == 1:
            err_msg = f"SYNTAX ERROR - {err_msg}"
        elif err.returncode == 2:
            err_msg = f"KERNEL ERROR - {err_msg}"
        else:
            err_msg = f"WEIRD RETURN CODE - {err_msg}"
        raise IP2Error(err_msg)
