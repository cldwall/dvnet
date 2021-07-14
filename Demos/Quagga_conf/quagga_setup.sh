#!/bin/bash

case $(hostname) in
    A-1)
        ipv4_addr="10.10.1.1"
        remote_ipv4_addr="10.10.2.1"
        ipv6_addr="200::1:1"
        iface="A-1-A_brd"
        ;;
    A-2)
        ipv4_addr="10.10.2.1"
        remote_ipv4_addr="10.10.1.1"
        ipv6_addr="200::2:1"
        iface="A-2-A_brd"
        ;;
    *)
        exit
        ;;
esac

# Install quagga
apt update && apt -y install quagga

# Assign the IP addresses to the loopbak interface
ip addr add $ipv4_addr dev lo
ip addr add $ipv6_addr dev lo

# Instantiate the IPv4-over-IPv6 (i.e. SIT) tunnel
tun_iface="tun_$(hostname)"
ip tunnel add $tun_iface mode sit remote $remote_ipv4_addr local $ipv4_addr dev $iface
ip link set $tun_iface up
ip link set $tun_iface multicast on

# Set up quagga's needed directories
    # Run directory (i.e. where it stores its PID file)
    mkdir /run/quagga
    chown quagga:quagga /run/quagga

    # The conf directory belongs to quagga after installation!

# Configure zebra
cat > /etc/quagga/zebra.conf <<-EOF
log file /etc/quagga/zebra.log
interface lo
interface $iface
interface $tun_iface
EOF

# Configure ospfd
cat > /etc/quagga/ospfd.conf <<-EOF
log file /etc/quagga/ospfd.log

interface $iface
  ip ospf hello-interval 5
  ip ospf area 0.0.0.1

router ospf
  ospf router-id $ipv4_addr
  redistribute connected
EOF

# Configure RIPngd
cat > /etc/quagga/ripngd.conf <<-EOF
log file /etc/quagga/ripngd.log

router ripng
  network $tun_iface
  redistribute connected
EOF

# Start the daemons
zebra -d -f /etc/quagga/zebra.conf
ospfd -d -f /etc/quagga/ospfd.conf
ripngd -d -f /etc/quagga/ripngd.conf
