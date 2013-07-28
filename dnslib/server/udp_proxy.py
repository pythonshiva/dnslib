#!/usr/bin/env python
# coding=utf-8
"""
    Simple DNS proxy - listens on proxy port and forwards request/reply to real server
    passing data through dnslib and printing the raw/parsed data

    This is mostly for testing - normal usage would be to use dig to generate request 
    and compare outputs

    Options:

      --port=PORT          Proxy port (default: 8053)
      --bind=BIND          Proxy bind address (default: all)
      --dns=DNS            DNS server (default: 8.8.8.8)
      --dns_port=DNS_PORT  DNS server port (default: 53)

    Usage:

    # python udp_proxy.py

    (from another window)

    # dig @127.0.0.1 www.google.com -p 8053

"""
import optparse
import socket
from dnslib import DNSRecord, QTYPE

AF_INET = 2
SOCK_DGRAM = 2

parser = optparse.OptionParser(usage="Usage: %prog [options]")
parser.add_option("--port",type=int,default=8053,help="Proxy port (default: 8053)")
parser.add_option("--bind",default="127.0.0.1",help="Proxy bind address (default: 127.0.0.1)")
parser.add_option("--dns",default="8.8.8.8",help="DNS server (default: 8.8.8.8)")
parser.add_option("--dns_port",type=int,default=53,help="DNS server port (default: 53)")
parser.add_option("--dnslib", type=int, default=1, help="Use dnslib for querying and responding")
options,args = parser.parse_args()

proxy = socket.socket(AF_INET, SOCK_DGRAM)
proxy.bind((options.bind,options.port))

with_indent = lambda indent, obj: indent + str(obj).replace("\n", "\n" + indent)


while True:
    # Wait for client connection
    data,client = proxy.recvfrom(8192)
    # Parse and print request
    request = DNSRecord.parse(data)
    id = request.header.id
    qname = request.q.qname
    qtype = request.q.qtype
    print "------ Request (%s): %r (%s)" % (str(client),qname.label,QTYPE[qtype])
    print data.encode('hex')
    print with_indent("  ", request)
    # Use dnslib to make request
    if options.dnslib:
        data = request.pack()
    # Send request to server
    s = socket.socket(AF_INET, SOCK_DGRAM)
    s.sendto(data,(options.dns,options.dns_port))
    # Wait for reply
    data,server = s.recvfrom(8192)
    # Parse and print reply
    reply = DNSRecord.parse(data)
    id = reply.header.id
    qname = reply.q.qname
    qtype = reply.q.qtype
    print "------ Reply (%s): %r (%s)" % (str(server),qname.label,QTYPE[qtype])
    print data.encode('hex')
    print with_indent("  ", reply)
    print
    # Use dnslib to make reply
    if options.dnslib:
        data = reply.pack()
    # Send reply to client
    proxy.sendto(data,client)
