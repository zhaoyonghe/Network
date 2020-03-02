=================================================================
How to run the code:
Run "python proxy.py", the default listen port number is 8080, or run "python proxy.py <port-number>" to define your own port number. The IP address is "localhost". 

"proxy.py" is a multithread proxy, if it fails (not likely), please test the "single_thread_proxy.py".

=================================================================
Data structure for caching:

<timestamp>
\r\n\r\n\r\n
<binary-file>

Just contains timestamp and the file (both in binary), separated by "\r\n\r\n\r\n". For jpg file, to check the timestamp, you need to first change the suffix to txt and then open.

When cache hits, the proxy will remove the timestamp, add the 200 status line and then send the message to the client.

=================================================================
BONUS PARTS:

/favicon.ico:
Notice that before requesting the /favicon.ico, the client will first request the index.html. Thus, I maintain a variable "curDomain": when the client first requests the index.html, record the domain to "curDomain"; when, after that, requesting the /favicon.ico, request it at "curDomain".


Multithreading:
Using the threading module, every time the proxy accepts a request from client, it creates a new thread and runs it to handle this request. When the new thread is handling the request, the main function of the proxy does not wait for its finish, instead, accepting the next request.


