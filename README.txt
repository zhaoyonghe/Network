/favicon.ico:
Notice that before requesting the /favicon.ico, the client will first request the index.html. Thus, I maintain a variable "curDomain": when the client first requests the index.html, record the domain to "curDomain"; when, after that, requesting the /favicon.ico, request it at "curDomain".


Multithreading:
Using the threading module, every time the proxy accepts a request from client, it creates a new thread and runs it to handle this request. When the new thread is handling the request, the main function of the proxy does not wait for its finish, instead, accepting the next request.


