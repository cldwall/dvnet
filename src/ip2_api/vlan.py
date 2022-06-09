import logging
from .cmds import _execute

log = logging.getLogger(__name__)

# Be sure to check the following for some background:
    # VLAN iproute2 API example -> https://developers.redhat.com/blog/2017/09/14/vlan-filter-support-on-bridge#with_vlan_filtering
    # PVID and untagged VLAN ports -> https://www.megajason.com/2018/04/30/what-is-pvid/
    # bridge(8) -> https://www.man7.org/linux/man-pages/man8/bridge.8.html

class vlan:
    def __init__(self, vID):
        log.debug(f"Created VLAN with ID {vID}")
        self.vID = vID

    def addIface(self, ifaceName):
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
