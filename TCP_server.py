#!/usr/bin/env python

from socket import *

serverPort = 8080
serverSocket = socket(AF_INET,SOCK_STREAM) # socket()
serverSocket.bind(('',serverPort)) # bind() 
serverSocket.listen(1) # liste() 
print ('The server is ready to receive') 
while True:
    connectionSocket, addr = serverSocket.accept() # accept() --> returns connection sock 
    sentence = connectionSocket.recv(1024).decode() # recv()
    capitalizedSentence = sentence.upper()
    connectionSocket.send(capitalizedSentence.encode()) # send() 
    connectionSocket.close() # close()
