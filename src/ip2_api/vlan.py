import logging
from .cmds import _execute

log = logging.getLogger(__name__)

# Be sure to check the following for some background:
    # VLAN iproute2 API example -> https://developers.redhat.com/blog/2017/09/14/vlan-filter-support-on-bridge#with_vlan_filtering
    # PVID and untagged VLAN ports -> https://www.megajason.com/2018/04/30/what-is-pvid/
    # bridge(8) -> https://www.man7.org/linux/man-pages/man8/bridge.8.html
    # Trunk ports -> https://unix.stackexchange.com/questions/556735/linux-vlan-aware-bridges-and-trunk-ports

class vlan:
    def __init__(self, vID):
        log.debug(f"Created VLAN with ID {vID}{' (i.e. a trunk VLAN)' if vID == 0 else ''}")
        self.vID = vID

    def addIface(self, ifaceName):
        if self.vID == 0:
            log.debug(f"Adding interface {ifaceName} as a trunk port")
            # Note the VLAN ID range is [0, 4095] given the VID is assigned 12 bits in a
                # 802.1Q tag. However, IDs 0 and 4095 are reserved and ID 1 is set as
                # PVID/Untagged by default. This leaves us with the [2, 4094] range seen below.
            _execute(
                ['bridge', 'vlan', 'add', 'dev', ifaceName, 'vid', '2-4094', 'master'],
                f"Error adding interface {ifaceName} as a trunk port"
            )
        else:
            log.debug(f"Adding interface {ifaceName} to VLAN with ID {self.vID}")
            _execute(
                ['bridge', 'vlan', 'add', 'dev', ifaceName, 'vid', f'{self.vID}',
                    'pvid', 'untagged', 'master'],
                f"Error adding interface {ifaceName} to VLAN with ID {self.vID}"
            )

    def delIface(self, ifaceName):
        log.debug(f"Adding interface {ifaceName} to VLAN with ID {self.vID}")
        _execute(
            ['bridge', 'vlan', 'del', 'dev', ifaceName, 'vid', f'{self.vID}',
                'pvid', 'untagged', 'master'],
            f"Error adding interface {ifaceName} to VLAN with ID {self.vID}"
        )
