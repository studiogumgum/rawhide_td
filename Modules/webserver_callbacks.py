import json
import re
from typing import Optional
import secrets
"""
webserverDAT callbacks

dat - the connected Web Server DAT
request - A dictionary of the request fields. The dictionary will always 
    contain the below entries, plus any additional entries dependent on the 
    contents of the request
        'method' - The HTTP method of the request (ie. 'GET', 'PUT').
        'uri' - The client's requested URI path. If there are parameters 
            in the URI then they will be located under the 'pars' key in 
            the request dictionary.
        'pars' - The query parameters.
        'clientAddress' - The client's address.
        'serverAddress' - The server's address.
        'data' - The data of the HTTP request.
response - A dictionary defining the response, to be filled in during the 
    request method. Additional fields not specified below can be added 
    (eg. response['content-type'] = 'application/json').
        'statusCode' - A valid HTTP status code integer (ie. 200, 401, 404). 
            Default is 404.
        'statusReason' - The reason for the above status code being returned 
            (ie. 'Not Found.').
        'data' - The data to send back to the client. If displaying a 
            web-page, any HTML would be put here.
"""
from typing import Dict, Any


# return the response dictionary
def onHTTPRequest(dat: webserverDAT, request: Dict[str, Any], 
                  response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Called when an HTTP request is received.

    Args:
        dat: The connected Web Server DAT
        request: Dictionary of request fields
        response: Dictionary defining the response to be filled in

    Returns:
        Dict[str, Any]: The response dictionary
    """
    
    return parent.WebServer.RouteRequest(request, response)


def onWebSocketOpen(dat: webserverDAT, client: str, uri: str):
    """
    Called when a WebSocket connection is opened.

    Args:
        dat: The connected Web Server DAT
        client: The client identifier
        uri: The requested URI
    """
    parent.WebUI.Info('Websocket Opened:', source='WebServer')
    return

def onWebSocketClose(dat: webserverDAT, client: str):
    """
    Called when a WebSocket connection is closed.

    Args:
        dat: The connected Web Server DAT
        client: The client identifier
    """
    parent.WebUI.Stream.CleanupClient(client)
    
    return

def onWebSocketReceiveText(dat: webserverDAT, client: str, data: str):
    """
    Called when text data is received via WebSocket.

    Args:
        dat: The connected Web Server DAT
        client: The client identifier
        data: The text data received
    """
    parent.WebServer.ProcessMessage(client, data)
    return

def onWebSocketReceiveBinary(dat: webserverDAT, client: str, data: bytes):
    """
    Called when binary data is received via WebSocket.

    Args:
        dat: The connected Web Server DAT
        client: The client identifier
        data: The binary data received
    """
    dat.webSocketSendBinary(client, data)
    return

def onWebSocketReceivePing(dat: webserverDAT, client: str, data: bytes):
    """
    Called when a ping is received via WebSocket.

    Args:
        dat: The connected Web Server DAT
        client: The client identifier
        data: The ping data received
    """
    dat.webSocketSendPong(client, data=data);
    return

def onWebSocketReceivePong(dat: webserverDAT, client: str, data: bytes):
    """
    Called when a pong is received via WebSocket.

    Args:
        dat: The connected Web Server DAT
        client: The client identifier
        data: The pong data received
    """
    return

def onServerStart(dat: webserverDAT):
    """
    Called when the web server starts.

    Args:
        dat: The connected Web Server DAT
    """
    return

def onServerStop(dat: webserverDAT):
    """
    Called when the web server stops.

    Args:
        dat: The connected Web Server DAT
    """
    for client in dat.webSocketConnections:
        dat.webSocketClose(client)
    return


