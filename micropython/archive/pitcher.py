import network
import esp32
from esp import espnow
from binascii import hexlify, unhexlify
from machine import Timer


wlan = network.WLAN(network.STA_IF)
if not wlan.active():
    wlan.active(True)

esp_obj = espnow.ESPNow()
esp_obj.init()

BROADCAST = unhexlify('ffffffffffff')
SEND_BROADCAST = False

def peer_check(peer):
    try:
        esp_obj.get_peer(peer)
        return True
    except Exception as error:
        return False


def peer_add(peer):
    if not peer_check(peer):
        try:
            esp_obj.add_peer(peer)
        except Exception as error:
            print(error)


def peer_send(peer, message):
    if peer_check(peer):
        esp_obj.send(peer, message, False)
    else:
        print("Unknown peer")


def peers_decode(peers):
    for peer in peers:

        ifidx_type = {
            0: "Station",
            1: "Access Point"
        }

        (mac, lmk, channel, ifidx, encrypt) = peer
        print('MAC: %s' % hexlify(mac).decode())
        print('Local Master Key: %s' % hexlify(lmk).decode())
        print('Channel: %s' % channel)
        print('Interface Index: %s' % ifidx_type.get(ifidx))
        print('Encrypt: %s' % encrypt)


def message_receive():

    (mac, message) = esp_obj.irecv()
    print(hexlify(mac).decode(), message.decode())

    if not peer_check(mac):

        print("New peer discovered: %s" % hexlify(mac).decode())
        peer_add(mac)

        peers_decode(esp_obj.get_peers())


def handle_timer(timer):
    global SEND_BROADCAST
    SEND_BROADCAST = True


if not peer_check(BROADCAST):
    peer_add(BROADCAST)

timer0 = Timer(0)
timer0.init(period=5000, mode=Timer.PERIODIC, callback=handle_timer)

while True:

    if SEND_BROADCAST:
        peer_send(BROADCAST, str(esp32.raw_temperature()))
        SEND_BROADCAST = False
    
    if esp_obj.poll():
        message_receive()
