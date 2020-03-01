#!/usr/bin/env python 
import sys
from socket import *

proxyPort = 8080 # default port
if len(sys.argv) > 1:
	proxyPort = int(sys.argv[1])

# create socket to send messages to the server
serverName = 'localhost'
serverPort = 8888
toServerSocket = socket(AF_INET, SOCK_STREAM)
toServerSocket.connect((serverName,serverPort))
print("The proxy has connected to the server.")

# create proxy socket to receive messages from client
proxySocket = socket(AF_INET,SOCK_STREAM)
proxySocket.bind(('localhost',proxyPort)) 
proxySocket.listen(5)
print ("The proxy is ready to receive.")

# keep accepting the client
while True:
	connectionSocket, addr = proxySocket.accept()

	try:
		# get message from the client
		request = connectionSocket.recv(1024).decode()
		sentence = request.split(" ")[1][1:]

		# send the message from proxy to server and get the result
		toServerSocket.send(sentence.encode())
		modifiedSentence = toServerSocket.recv(1024).decode()
		print("From Server:", str(modifiedSentence))     

		# send the modified message to the client
		connectionSocket.send(modifiedSentence.encode())
	except:
		print("Some error.")
	finally:
		connectionSocket.close() # close()

toServerSocket.close() # close()

