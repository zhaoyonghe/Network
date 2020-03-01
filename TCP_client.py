#!/usr/bin/env python 
from socket import *

serverName = 'localhost'
serverPort = 8080
clientSocket = socket(AF_INET, SOCK_STREAM) # socket() 
clientSocket.connect((serverName,serverPort)) # connect() 
sentence = input('Input lowercase sentence: ')
clientSocket.send(sentence.encode()) # send() 
modifiedSentence = clientSocket.recv(1024).decode() # recv()
print('From Server:', str(modifiedSentence)) 
clientSocket.close() # close()
