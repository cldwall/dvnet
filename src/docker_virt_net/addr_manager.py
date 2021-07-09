next_subn_addr = {}

def request_ip(subnet):
    if subnet in next_subn_addr:
        next_subn_addr[subnet] += 1
        return "{}/{}".format(
            binary_to_addr(next_subn_addr[subnet]),
            subnet.split('/')[1]
        )

    next_subn_addr[subnet] = get_net_addr(subnet) + 1
    return "{}/{}".format(
            binary_to_addr(next_subn_addr[subnet]),
            subnet.split('/')[1]
        )

def addr_to_binary(addr):
    bin_ip, loop_count = 0, 0
    for x in reversed(addr.split('/')[0].split('.')):
        bin_ip |= int(x) << loop_count * 8
        loop_count += 1
    return bin_ip

def binary_to_addr(bin):
    addr = ""
    for i in range(3, -1, -1):
        addr += str(bin >> 8 * i & 0xFF) + '.'
    return addr[:len(addr) - 1]

def get_net_addr(subn):
    mask = 0
    for i in range(int(subn.split('/')[1])):
        mask |= 0x1 << (31 - i)
    return addr_to_binary(subn) & mask

def get_brd_addr(subn):
    mask = 0
    for i in range(int(subn.split('/')[1])):
        mask |= 0x1 << (31 - i)
    return get_net_addr(subn) | ~mask
