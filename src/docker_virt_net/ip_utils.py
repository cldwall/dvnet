def addr_to_binary(addr):
    """Returns an integer equivalent for an IPv4 address.

        Args:
            addr (str): An IPv4 address in A.B.C.D format.

        Returns:
            int: The equivalent representation of `addr`.
    """
    bin_ip, loop_count = 0, 0
    for x in reversed(addr.split('/')[0].split('.')):
        bin_ip |= int(x) << loop_count * 8
        loop_count += 1
    return bin_ip

def get_net_addr(subn):
    """Returns the network address for an IPv4 CIDR block.

        Args:
            subn (str): An IPv4 CIDR block in A.B.C.D/X format.

        Returns:
            int: The CIDR's block network address.
    """
    mask = 0
    for i in range(int(subn.split('/')[1])):
        mask |= 0x1 << (31 - i)
    return addr_to_binary(subn) & mask

def get_brd_addr(subn):
    """Returns the broadcast address for an IPv4 CIDR block.

        Args:
            subn (str): An IPv4 CIDR block in A.B.C.D/X format.

        Returns:
            int: The CIDR's block broadcast address.
    """
    mask = 0
    for i in range(int(subn.split('/')[1])):
        mask |= 0x1 << (31 - i)
    return get_net_addr(subn) | ~mask
