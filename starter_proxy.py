from socket import *
import re
import select
import sys
import os
from datetime import datetime
import time

BUFF_SIZE = 2048

# For example, it will send something like this:
# GET /~ge2211/4119/test1/www.google.com/index.html HTTP/1.0\r\n\r\n
def sendToServer(toServerSocket, requestPath):
	# Send GET request to server socket
	# Does not return anything
	requestToServer = "GET " + requestPath + " HTTP/1.0\r\n\r\n"
	print(requestToServer)
	toServerSocket.send(requestToServer.encode())

def waitForSocketReadable(skt, name):
	count = 0
	while count < 301:
		readable, _, _ = select.select([skt], [], [], 0)
		if readable:
			break
		if count % 50 == 0:
			print("waiting for the " + name + " to become readable..... count = " + str(count))
		count += 1
		time.sleep(0.01)

def receiveFromServer(toServerSocket):
	# Receive message from socket
	# Returns a tuple rawResponse(byte), responseCode, indicator, responseBody(byte)
	# Uses nonblocking select call (timeout=0)
	waitForSocketReadable(toServerSocket, "toServerSocket")

	readable, _, _ = select.select([toServerSocket], [], [], 0)
	if not readable:
		# error
		return None, None, None, None

	rawResponse = bytearray()
	# First receive the top part of the message, including status line and header lines 
	indicator = toServerSocket.recv(BUFF_SIZE)
	rawResponse.extend(indicator)
	print(indicator)

	# Get the entire content length of this response message
	indicator = indicator.decode(errors='ignore')
	pattern = re.compile(r'(?<=Content-Length: )\d+')
	lenList = pattern.findall(indicator)
	if len(lenList) == 0:
		# If we cannot find the content length in the header lines
		responseCode = indicator.split(" ", 2)[1]
		responseBody = rawResponse.split(b'\r\n\r\n')[1]
		return rawResponse, responseCode, indicator, responseBody

	n = lenList[0]
	print("Content-Length: " + n)
	# Recieve all the content
	while int(n) > len(rawResponse):
		packet = toServerSocket.recv(int(n))
		if not packet:
			break
		#print(packet)
		rawResponse.extend(packet)

	#print("Receive from server:\n")
	#print(rawResponse)

	responseCode = indicator.split(" ", 2)[1]
	responseBody = rawResponse.split(b'\r\n\r\n')[1]
	return rawResponse, responseCode, indicator, responseBody


'''
clientMessage should be some thing like this:
GET /www.columbia.edu/~ge2211/4119/test2/www.hats.com/e2.jpg HTTP/1.0
Host: localhost:8080
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0
Accept: image/webp,*/*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
Referer: http://localhost:8080/www.columbia.edu/~ge2211/4119/test2/www.hats.com/
Cookie: BIGipServer~CUIT~www.columbia.edu-80-pool=1311259520.20480.0000

This method will extract the domain and the path of the file.
We only need to look at the "/www.columbia.edu/~ge2211/4119/test2/www.hats.com/e2.jpg"
in the first line, where "www.columbia.edu" should be the domain,
and "/~ge2211/4119/test2/www.hats.com/e2.jpg" should be the path.
'''
def getDomainAndPath(clientMessage):
	if len(clientMessage) == 0:
		return None, None

	# find the desired part, expected to be like:
	# "/www.columbia.edu/~ge2211/4119/test2/www.hats.com/e2.jpg"
	request = clientMessage.split(" ")[1]
	print(request)

	if request == "/favicon.ico":
		return None, "/favicon.ico"
	if "ajax" in request and "node" in request:
		return None, None

	domain, path = getDomainAndPathFromURL(request)

	# Referer
	pattern = re.compile(r'(?<=Referer: )\S+')
	refererList = pattern.findall(clientMessage)
	goodPath = None
	if len(refererList) > 0:
		print("-----------------------")
		print(refererList[0])
		goodPath = refererList[0].split(domain)[-1]

	if goodPath is not None and len(goodPath) > 0:
		pathList = path.split("/")
		goodPathList = goodPath.split("/")

		i = 0
		while i < len(pathList) and i < len(goodPathList):
			if pathList[i] != goodPathList[i]:
				break
			i += 1

		goodPathList.extend(pathList[i:])
		path = "/".join(goodPathList)

	return domain, path

def getDomainAndPathFromURL(fileURL):
	# expected to be like:
	# ["", "www.columbia.edu", "~ge2211/4119/test2/www.hats.com/e2.jpg"]
	temp = fileURL.split("/", 2)
	domain = temp[1]
	if len(temp) == 2:
		path = "/index.html"
	elif temp[2][-1] == "/":
		path = "/" + temp[2] + "index.html"
	else:
		path = "/" + temp[2]

	return domain, path

def addStatusLine(bfile):
	return b'HTTP/1.0 200 OK\r\n\r\n' + bfile

def addTimeStamp(bfile):
	return str(datetime.now()).encode() + b'\r\n\r\n\r\n' + bfile

def removeTimeStamp(bfile):
	return bfile.split(b'\r\n\r\n\r\n')[1]

# first line is "GET /path HTTP/1.0\r\n" so we want /path/
def checkCache(domain, path, justCheck):
	# Checks cache for file
	# returns the body and response code from the server
	fileName = domain + path

	# Check if the request exists in cache
	if os.path.isfile(fileName):
		if justCheck:
			return True, None
		with open(fileName, "rb") as f:
			bfile = f.read()
		return True, addStatusLine(removeTimeStamp(bfile))
	else:
		return False, None

def saveCache(domain, path, bfile):
	fileName = domain + path
	exists, _ = checkCache(domain, path, True)
	if not exists:
		dir = "/".join(fileName.split("/")[:-1])
		if not os.path.exists(dir):
			os.makedirs(dir)
		with open(fileName, "wb") as f:
			f.write(addTimeStamp(bfile))

def connectToServer(serverName, serverPort):
	toServerSocket = socket(AF_INET, SOCK_STREAM)
	toServerSocket.connect((serverName, serverPort))
	print("The proxy has connected to the server...")
	return toServerSocket

def main():
	count = 0

	serverPort = 80
	
	proxyPort = 8080 # default proxy port
	if len(sys.argv) > 1:
		proxyPort = int(sys.argv[1])

	# Create a proxy socket to listen from the client
	proxySocket = socket(AF_INET,SOCK_STREAM)
	proxySocket.bind(('localhost', proxyPort))
	proxySocket.listen(5) # what is the listen??
	print("The proxy is ready to receive from client...")

	# The current domain that the client is requesting
	curDomain = None

	while True:
		count += 1
		print("========================================================")
		print(count)
		print("========================================================")

		# Accept a connection
		clientSocket, clientAddr = proxySocket.accept()

		waitForSocketReadable(clientSocket, "clientSocket")

		readable, _, _ = select.select([clientSocket], [], [], 0)
		if readable:
			# Receive 2048 bytes from client
			clientMessage = clientSocket.recv(BUFF_SIZE).decode(errors="ignore")

			# Parse the request
			domain, path = getDomainAndPath(clientMessage)
			if domain is None and path is None:
				clientSocket.close()  # close socket to wait for new request
				continue

			print("\nClient message : \n****\n" + clientMessage + "\n****\n" )

			if domain is None and path == "/favicon.ico" and curDomain is not None:
				domain = curDomain

			curDomain = domain
			
			# check the cache
			hit, rawResponse = checkCache(domain, path, False)
			if hit:
				print("cache hit..............................................")
				clientSocket.send(rawResponse)
				clientSocket.close()  # close socket to wait for new request
				continue
			

			# cache miss, request the server
			toServerSocket = connectToServer(domain, serverPort)

			# Send the request to server
			sendToServer(toServerSocket, path)

			# receive the response from server
			rawResponse, code, indicator, responseBody = receiveFromServer(toServerSocket)

			if code == "200":
				print("200 save to cache")
				saveCache(domain, path, responseBody)
			elif code == "404":
				print("404 do nothing")
			elif code == "301":
				print("301 redirect")
				pattern = re.compile(r'(?<=Location: )\S+')
				print("-----------------------")
				print(pattern.findall(indicator)[0])
				redirectedPath = pattern.findall(indicator)[0]
				newDomain, newPath = None, None
				if redirectedPath[0:7] == "http://":
					newDomain, newPath = getDomainAndPathFromURL(redirectedPath[6:])
				else:
					newDomain, newPath = getDomainAndPathFromURL(redirectedPath)
				print("redirect to:")
				print(newDomain)
				print(newPath)

				# check the cache
				hit, rawResponse = checkCache(newDomain, newPath, False)
				if hit:
					print("cache hit..............................................")
					clientSocket.send(rawResponse)
					clientSocket.close()  # close socket to wait for new request
					continue

				toServerSocket = connectToServer(newDomain, serverPort)
				sendToServer(toServerSocket, newPath)
				rawResponse, code, indicator, responseBody = receiveFromServer(toServerSocket)
				# TODO save cache
				saveCache(newDomain, newPath, responseBody)
			else:
				print("=====================================")
				print("This will not happen with high probability............")
				print("=====================================")
				clientSocket.close()  # close socket to wait for new request
				toServerSocket.close()
				continue


			#print("From Server:", str(file))     

			# send the modified message to the client
			print("cache miss..............................................")
			print("to client")
			#print(addStatusLine(responseBody))
			clientSocket.send(addStatusLine(responseBody))
			clientSocket.close()  # close socket to wait for new request
			toServerSocket.close() # close
		else:
			# Or other error handling 
			clientSocket.close()

	proxySocket.close()

if __name__ == "__main__":
	main()