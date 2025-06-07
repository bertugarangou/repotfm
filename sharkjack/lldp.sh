#!/bin/bash
# Nom: lldp.sh
# Autor: carquinyolis
# V: 1.2
# Ultima edició: 28/1/2025
# Descripció: Reconeixament ràpid IP i LLDP d'una xarxa.

LOOT_DIR_LLDPD=/root/loot/lldpd
LOOT_DIR_IFCONFIG=/root/loot/ifconfig
LLDPD_DIR=/etc/shark/lldpd
IFCONFIG_DIR=/etc/shark/ifconfig
DNS_FILE=/etc/resolv.conf
NAMESERVER=172.16.217.5
HOSTNAME=PC-PAPARAPUPI
function finish() {
        LED CLEANUP
        wait $1
        kill $1 &> /dev/null
        echo $LLDPD_M > $LLDPD_FILE
        echo $IFCONFIG_M > $IFCONFIG_FILE
        sync
        LED FINISH
        SERIAL_WRITE [*] Script finished
        echo "[*] Script finished"
}
function setup() {
        SERIAL_WRITE DNS: $NAMESERVER
        echo -e "DNS: $NAMESERVER"
        SERIAL_WRITE [*] Getting DHCP IP
        echo "[*] Getting DHCP IP"
        LED SETUP
        NETMODE DHCP_CLIENT
        while ! ifconfig eth0 | grep "inet addr"; do sleep 1; done
        echo "nameserver " $NAMESERVER > $DNS_FILE
        SERIAL_WRITE [*] Setting files
        echo "[*] Setting files"
        mkdir -p $LOOT_DIR_LLDPD &> /dev/null
        mkdir -p $LLDPD_DIR &> /dev/null
        LLDPD_FILE=$LLDPD_DIR/lldpd-count
        if [ ! -f $LLDPD_FILE ]; then
                touch $LLDPD_FILE && echo 0 > $LLDPD_FILE
        fi
        mkdir -p $LOOT_DIR_IFCONFIG &> /dev/null
        mkdir -p $IFCONFIG_DIR &> /dev/null
        IFCONFIG_FILE=$IFCONFIG_DIR/ifconfig-count
        if [ ! -f $IFCONFIG_FILE ]; then
                touch $IFCONFIG_FILE && echo 0 > $IFCONFIG_FILE
        fi
        uci set system.@system[0].hostname=$HOSTNAME
        uci commit system
        /etc/init.d/system reload
        while [ -z "$SUBNET" ]; do
                sleep 1s && find_subnet
        done
        SERIAL_WRITE "[*] Loading lldp (6s)"
        echo "[*] Loading lldp (4s)"
        lldpd -I eth0
        sleep 2
        /etc/init.d/lldpd restart
        sleep 4
}

function find_subnet() {
        SUBNET=$(ip addr | grep -i eth0 | grep -i inet | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}[\/]{1}[0-9]{1,2}" | sed 's/\.[0-9]*\//\.0\//')
}

function run() {
        setup
        SERIAL_WRITE $(IPIP=$(ifconfig eth0 | grep "inet addr"))
        echo $(IPIP=$(ifconfig eth0 | grep "inet addr"))
        LED ATTACK
        tpid=$!
        SERIAL_WRITE [*] LLDP scanning
        echo "[*] LLDP scanning"
        LLDPD_N=$(cat $LLDPD_FILE)
        LLDPD_M=$(( $LLDPD_N + 1 ))
        lldpcli show neighbor details > $LOOT_DIR_LLDPD/lldpd_$LLDPD_M.txt
        lldpcli show interfaces details >> $LOOT_DIR_LLDPD/lldpd_$LLDPD_M.txt
        SERIAL_WRITE $(lldpcli show neighbor details)
        echo $(lldpcli show neighbor details)
        IFCONFIG_N=$(cat $IFCONFIG_FILE)
        IFCONFIG_M=$(( $IFCONFIG_N + 1 ))
        ifconfig eth0 > $LOOT_DIR_IFCONFIG/ifconfig_$IFCONFIG_M.txt
        ip addr show dev eth0 >> $LOOT_DIR_IFCONFIG/ifconfig_$IFCONFIG_M.txt
        finish $tpid
}
run
exit 0
