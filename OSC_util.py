import pythonosc.udp_client
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.udp_client import UDPClient
from pythonosc import osc_message_builder
import time
import random
import numpy as np

IP = "127.0.0.1"
CLIENT_PORT = 2222
SERVER_PORT = 2223

def main():

  client = SimpleUDPClient(IP, CLIENT_PORT)

  while True:
    n1 = random.randint(100, 1024)
    n2 = random.randint(100, 1024)

    client.send_message("/some/address", [n1,n2])

    intervals = np.arange(10)/10
    s = np.random.randint(0,100)%10
    time.sleep(intervals[s])

if __name__ == "__main__":
  main()