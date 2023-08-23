from operator import mod, sub
import socket
import ipaddress
import struct
import random
import netifaces
import binascii
import re
import threading
import logging

class pokeys_interface():
    def __init__(self, host):
        self.client_pk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) #socket.AF_INET  2
        self.connected = False
        self.req_mutex = threading.Lock()
        
        self.POKEYS_PORT_COM = 20055

        self.users = []
        self.blinds = dict()
        
        self.requestID = random.randint(0, 255)

        self.inputs = [False] * 55
        self.connect(host)

    def connect(self, address):
        if address == None:
            return False
        #print("Connecting to " + address)
        self.client_pk.connect((address, self.POKEYS_PORT_COM))
        self.client_pk.settimeout(1)
        #logging.error("connecting...")
        self.connected = True
        return self.connected

    def disconnect(self):
        #self.client.close()
        #self.client_pk.shutdown()
        self.client_pk.close()
        #return

    def prepare_command(self, cmdID, param1, param2, param3, param4, data, data_1):
        self.requestID = (self.requestID + 1) % 256

        req = bytearray(64)
        req[0] = 0xBB
        req[1] = cmdID
        req[2] = param1
        req[3] = param2
        req[4] = param3
        req[5] = param4
        req[6] = self.requestID
        req[7] = sum(req[0:7]) % 256
        i = 8
        for d in data_1:
            req[i] = d
            i+=1
        
        l = len(data)
        if l > 0:
            req[8:8+l] = bytearray(data)
        return req

    def send_request(self, command):
        if not self.connected:
            return None
        try:
            for rety in range(3):
                #print(f"Request: {command}")
                with self.req_mutex:
                    
                    self.client_pk.sendall(bytes(command))
                    response = self.client_pk.recv(1024)
                    
                    if response[6] == command[6]:
                        #print(f"Response: {response}")
                        return response
        except socket.timeout as t:
            print("Timeout - no response!")
            return None
        return None

    def get_name(self):        
        if not self.connected:
            return None

        resp = self.send_request(self.prepare_command(0x00, 0, 0, 0, 0, [], []))
        
        if resp != None:
            try:
                return resp[31:41].decode('UTF-8')
            except:
                return None
            
        return None
        
    def read_inputs(self):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0xCC, 0, 0, 0, 0, [], []))

        if resp != None:
            try:
                # Parse the response
                for i in range(55):
                    self.inputs[i] = (resp[8 + int(i / 8)] & (1 << (mod(i, 8)))) > 0
                return True
            except:
                return False
            
        return False   

    def set_output(self, pin, state):
        if not self.connected:
            return False
        resp = self.send_request(self.prepare_command(0x40, pin, 0 if state else 1, 0, 0, [], []))
        return True

    def set_poled_channel(self, ch, state):
        if not self.connected:
            return False
        resp = self.send_request(self.prepare_command(0xE6, 0x20, ch, state, 0, [], []))

    def set_pin_function(self, pin, function):
        if not self.connected:
            return False  #4=output, 2=input

        resp = self.send_request(self.prepare_command(0x10, pin, function, 0, 0, [], []))

    #    p = struct.pack("II", int(blind.refPos * 600000 / 100), int(blind.refAngle * 10000 / 100))
    #    resp = self.send_request_control_node(self.prepare_command(0x50, blind.ID, p))        
    
    #def stop_blind(self, blind):
    #    resp = self.send_request_control_node(self.prepare_command(0x51, blind.ID, []))   

    def read_pin_function(self, pin):
        resp = self.send_request(self.prepare_command(0x15, pin, 0, 0, 0, [], []))

        pinmode = list(resp[3:5])
        res = pinmode[0]

        return res #2=input, 4=output

    def read_digital_input(self, pin):
        resp = self.send_request(self.prepare_command(0x10, pin, 2, 0, 0, [0x40], []))
        return self.get_input(pin)

    def sensor_setup(self, i):
        #self.send_request(self.prepare_command(0x60, 0, 0, 0, 0, []))
        resp = self.send_request(self.prepare_command(0x76, i, 1, 0, 0, [], []))
        return True

    def read_sensor_values(self, i):
        resp = self.send_request(self.prepare_command(0x77, i, 1, 0, 0, [], []))
        return resp
    
    #parsed response of read_sensor_values()
    def sensor_readout(self, id):
        i = int(id)
        packet = self.read_sensor_values(i)
        valPacket = re.findall('..', binascii.hexlify(packet).decode())
        val_hex = str(valPacket[9])+str(valPacket[8])
        val = int(val_hex, base=16)/100
        return val

    def read_poextbus(self):
        resp = self.send_request(self.prepare_command(0xDA, 2,0,0,0,[],[]))
        l = list(resp)
        
        return l[8:18]

    def poextbus_on(self, pin):
        outputs = 10 *[0]
        outputs_state = self.read_poextbus()
        for out_card in range(9,0,-1):
            if pin < (((9-out_card) +1)* 8) and pin > ((9-out_card)*8):
                outputs[out_card] = 1 << (pin % 8)
                out_card_n = out_card

        if pin % 8 == 0:
            outputs[pin//8] = 1
            outputs.reverse()
            out_card_n = outputs.index(1)

        for i in range(len(outputs_state)):
            if (outputs_state[i] | outputs[i]) != outputs_state[i]:
                # Something new
                outputs_state[i] |= outputs[i]
                # send
                resp = self.send_request(self.prepare_command(0xDA, 1,0,0,0,[],outputs_state))
                if resp != None:
                    return True
            else:
                # Nothing new
                pass

    def poextbus_off(self, pin):
        outputs = 10 *[0]
        outputs_state = self.read_poextbus()
        for out_card in range(9,0,-1):
            if pin < (((9-out_card) +1)* 8) and pin > ((9-out_card)*8):
                outputs[out_card] = 1 << (pin % 8)

        if pin % 8 == 0:
            outputs[pin//8] = 1
            outputs.reverse()
            
        for i in range(len(outputs_state)):

            if (outputs_state[i] & outputs[i]):
                # Something new
                outputs_state[i] &= ~outputs[i]
                # send
            
                resp = self.send_request(self.prepare_command(0xDA, 1,0,0,0,[],outputs_state))
                if resp != None:
                    return True
            else:
                # Nothing new
                pass
        if outputs == outputs_state:
            outputs = list(map(sub, outputs_state, outputs))
        
            resp = self.send_request(self.prepare_command(0xDA, 1,0,0,0,[],outputs))
            if resp != None:
                    return True

