#!/usr/bin/env python
import sys, re, pika, json, ConfigParser

config = ConfigParser.ConfigParser()
config.read("traphandler_setting.txt")

counter = 1
hostname = "localhost"
ip_address = "127.0.0.1"
body = ""
var_bind = {}
var_bind_assoc = []

rabbitmq_host = config.get("rabbitmq","host")
rabbitmq_user = config.get("rabbitmq","user")
rabbitmq_pass = config.get("rabbitmq","pass")

pattern = r'[0-9]+(?:\.[0-9]+){3}'

acm_loss = False
receiver_unlocked = False
channel_unlocked = False

# TODO: identify type of SNMP trap: acm-loss, receiver unlocked
# Keyword: NOVELSAT-COMMON-MIB::nsCommonMonitorEventsDescription = acm client was lost

line = sys.stdin.readline()
while line:
    if counter==1:
        clean_hostname = "68.23.92.50"
        hostname = re.findall(pattern, line)
        clean_hostname = hostname[0]
        body = clean_hostname + "\n"
        var_bind['hostname'] = clean_hostname
    elif counter==2:
        clean_hostname = "68.23.92.50"
        ip_address = re.findall(pattern, line)
        clean_hostname = ip_address[1]
        body = body + clean_hostname + "\n"
        var_bind['ip_address'] = clean_hostname
    else:
        var_bind_assoc = line.split(" ", 1)
        vb_key = var_bind_assoc[0].strip()
        vb_value = var_bind_assoc[1].strip()
        var_bind[vb_key] = vb_value
        if vb_value == "acm client was lost":
            acm_loss = True
        elif vb_value == "receiver unlocked" or vb_value == "receiver locked":
            receiver_unlocked = True
        body = body + line

    print line
    counter += 1
    line = sys.stdin.readline()

routing_key = ""
if acm_loss:
    routing_key= "acm_loss"
elif receiver_unlocked:
    routing_key = "receiver_unlocked"

#queue_name = "hello"
#routing_key = "hello"
json_body = json.dumps(var_bind)

queue_name = routing_key
credentials = pika.PlainCredentials(rabbitmq_user,rabbitmq_pass)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue=queue_name)
channel.basic_publish(exchange='', routing_key=routing_key, body=json_body)

print(" [x] Sent SNMP Trap!")
connection.close()