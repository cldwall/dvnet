import subprocess, os
from .exceptions import IP2Error, UtilError

def _execute(args, err_msg):
    if not os.geteuid() == 0:
        raise IP2Error("Calls to iproute2 must be made by root")
    try:
        subprocess.run(
            args,
            check = True,
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as err:
        if args[0] == 'ip':
            # Return codes as per:
                # https://manpages.debian.org/stretch/iproute2/ip.8.en.html
            if err.returncode == 1:
                err_msg = f"SYNTAX ERROR - {err_msg}"
            elif err.returncode == 2:
                err_msg = f"KERNEL ERROR - {err_msg}"
            else:
                err_msg = f"WEIRD RETURN CODE - {err_msg}"
            raise IP2Error(err_msg)
        else:
            raise UtilError(err_msg)

def _get_value(args, err_msg):
    try:
        return subprocess.run(args, capture_output = True).stdout
    except subprocess.CalledProcessError:
        raise UtilError(err_msg)
