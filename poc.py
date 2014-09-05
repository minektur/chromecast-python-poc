#!/usr/bin/env python
import cast_channel_pb2
import socket, ssl, select, time, re
from thread import start_new_thread
from struct import pack,unpack
import sys, os
import json
from hexdump import hexdump

request_id = os.getpid()

chromecast_server = "192.168.0.138"
#chromecast_server = "127.0.0.1"

namespace = { 'con':        'urn:x-cast:com.google.cast.tp.connection',
              'receiver':   'urn:x-cast:com.google.cast.receiver',
              'cast':       'urn:x-cast:com.google.cast.media',
              'heartbeat':  'urn:x-cast:com.google.cast.tp.heartbeat',
              'message':    'urn:x-cast:com.google.cast.player.message',
              'media':      "urn:x-cast:com.google.cast.media",
            }

def make_msg(nspace = None):
    msg = cast_channel_pb2.CastMessage()
    msg.protocol_version = msg.CASTV2_1_0
    msg.source_id = "sender-0"
    msg.destination_id = "receiver-0"
    msg.payload_type = cast_channel_pb2.CastMessage.STRING;
    if nspace:
        msg.namespace = namespace[nspace]
    return msg

#def hexdump(msg):
#    f = os.popen("/usr/bin/hexdump -C", "w")
#    f.write(msg)
#    f.close()

def format_msg(msg):
    #prepend message with Big-Endian 4 byte payload size
    be_size = pack(">I",msg.ByteSize())
    return be_size + msg.SerializeToString()

def read_message(soc):
    #first 4 bytes is Big-Endian payload length
    data=""
    while len(data) < 4:
        frag = soc.recv(1)
        data += frag
    read_len = unpack(">I", data)[0]
    #now read the payload
    data=""
    while len(data) < read_len:
        frag = soc.recv(2048)
        data += frag
        print "."
    return data

def get_response(soc):
    print "\nReading ..."
    #get the data
    payload=read_message(soc)
    response = make_msg()
    response.ParseFromString(payload)
    resp = json.loads(response.payload_utf8)
    print json.dumps(resp, indent=4)
    return resp

def send_pong(soc):
    print "Sending PONG"
    msg.namespace=namespace['heartbeat']
    msg.payload_utf8 = """{ "type": "PONG" }"""
    message = format_msg(msg)
    soc.sendall(message)



##################################################
soc = socket.socket()
soc = ssl.wrap_socket(soc)
soc.connect((chromecast_server,8009))
msg = make_msg()

print "Connecting ..."
msg.namespace=namespace['con']
msg.payload_utf8 = """{"type":"CONNECT","origin":{}}"""
message = format_msg(msg)
soc.sendall(message)
#hexdump(message)


print "Sending get_status..."
msg.namespace = namespace['receiver']
msg.payload_utf8 = """{"type":"GET_STATUS","requestId":%s}""" % (request_id)
message = format_msg(msg)
soc.sendall(message)
#hexdump(message)


resp = get_response(soc)
session = resp['status']['applications'][0]['sessionId']

print "Sending Launch App"
msg.namespace = namespace['receiver']
msg.payload_utf8 = """{"type":"LAUNCH","requestId":%s,"appId":"CC1AD845"}""" % (request_id)
message = format_msg(msg)
soc.sendall(message)
#hexdump(message)

resp = get_response(soc)

print "Sending Launch App"
msg.namespace = namespace['con']
msg.payload_utf8 = """{"type":"CONNECT","origin":{}}"""
message = format_msg(msg)
soc.sendall(message)
#hexdump(message)

resp = get_response(soc)

print "Sending load URL"
msg.namespace = namespace['media']
data = """{"type":"LOAD","requestId":%s,"sessionId":"%s","media":{"contentId":"http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4","streamType":"buffered","contentType":"video/mp4"},"autoplay":true,"currentTime":0,"customData":{"payload":{"title:":"Big Buck Bunny","thumb":"images/BigBuckBunny.jpg"}}}""" % (request_id, session)

msg.payload_utf8 =data
message = format_msg(msg)
soc.sendall(message)

try:
    while True:
        resp = get_response(soc)
        if resp['type'] == 'PING':
            send_pong(soc)
finally:
    soc.close




