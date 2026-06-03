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
    if request['method'] == 'GET':
        uri = request['uri']
        client = request['clientAddress']

        handlers = {
                '/':           ('text_html',    'text/html'),
                '/index.html': ('text_html',    'text/html'),
                '/login': ('text_login',    'text/html'),
                '/login.html': ('text_login',    'text/html'),
                '/style.css':  ('text_css',     'text/css'),
                '/core.js':     ('text_core_js',      'application/javascript'),
                '/widgets.js':     ('text_widgets_js',      'application/javascript'),
                '/app.js':     ('text_js',      'application/javascript'),
                '/midi.js':    ('text_midi_js', 'application/javascript'),
                '/presets.js':    ('text_presets_js', 'application/javascript'),
                '/assets/gumgum_logo.png':    ('gumgum_logo', 'image/png'),
                '/assets/rawhide_logo.png':    ('rawhide_logo', 'image/png'),
                }

        if uri in handlers:
            op_name, content_type = handlers[uri]
            if content_type == 'image/png':
                response['data'] = opex(f'assets/{op_name}').saveByteArray('.png')
            else:
                response['data'] = opex(op_name).text
            response['headers'] = {'Content-Type': content_type}

        elif uri == '/config':
            try:
                response['data'] = parent.WebServer.BuildConfig(request)
                response['headers'] = {'Content-Type': 'application/json'}
            except Exception as e:
                parent.WebUI.Error(f'buildConfig error: {e}', source='WebServer')
                response['data'] = json.dumps({'error': str(e)})
                response['headers'] = {'Content-Type': 'application/json'}
                response['statusCode'] = 500
                response['statusReason'] = 'Internal Server Error'
                return response  # return early, skip the 200 below

        elif uri == '/presets':
            names = iop.PresetManager.List()
            response['data'] = json.dumps({'names': names})
            response['headers'] = {'Content-Type': 'application/json'}

        elif uri == '/views':
            views = []
            t = iop.Views.opex('table_views')
            for r in range(1, t.numRows):
                views.append({'name': t[r,'name'].val, 'label': t[r,'label'].val})
            response['data'] = json.dumps(views)
            response['headers'] = {'Content-Type': 'application/json'}

        elif uri == '/state':
            view_name = request.get('pars', {}).get('view', None)
            if view_name:
                response['data'] = json.dumps(parent.WebUI.Views.GetViewState(view_name))
                response['headers'] = {'Content-Type': 'application/json'}
            else:
                parent.WebUI.Error(f'View {view_name} not found', source='WebServer')
                response['statusCode']   = 404
                response['statusReason'] = 'Not Found'


        elif uri == '/theme':
            t   = parent.WebUI.opex('Styling/table_theme')
            out = {}
            for r in range(1, t.numRows):
                k = getCellVal(t, r, 'key')
                v = getCellVal(t, r, 'value')
                if k:
                    out[k] = v
            response['data']         = json.dumps(out)
            response['headers']      = {'Content-Type': 'application/json'}

        elif uri == '/refresh':
            # force a refresh of the page
            response['data'] = json.dumps({'type': 'command', 'action': 'refresh'})
            response['headers']      = {'Content-Type': 'application/json'}

        elif uri == '/health':
            response['data'] = json.dumps(parent.WebUI.Status)
            response['headers']      = {'Content-Type': 'application/json'}



        elif uri.startswith('/fonts/'):
            import os
            filename  = os.path.basename(uri[len('/fonts/'):])
            font_path = os.path.join(project.folder, 'fonts', filename)
            if os.path.exists(font_path):
                with open(font_path, 'rb') as f:
                    response['data']         = f.read()
                response['headers']      = {'Content-Type': 'font/woff2'}
            else:
                response['statusCode']   = 404
                response['statusReason'] = 'Not Found'

        else:
            response['statusCode'] = 404
            response['statusReason'] = 'Not Found'
            response['data'] = ''
            return response

        response['statusCode'] = 200
        response['statusReason'] = 'OK'
        return response

def cellToNum(cell):
    pattern = r'(\d+(?:\.\d+)?)'
    match = re.match(pattern, cell.val)
    if match:
        return match.group(1)
    else:
        return None

def getCellVal(table, row, col):
    cell = table[row, col]
    return cell.val if cell is not None else ''

def buildConfig(request):
    import json

    def cell(table, row, col):
        c = table[row, col]
        return c.val.strip() if c is not None else ''

    pars = request.get('pars', {})
    view_name = pars.get('view', None)

    if view_name:
        view_comp    = op('Views').op(view_name)
        config_table = view_comp.op('table_config')
        layout_table = view_comp.op('table_layout')
    else:
        config_table = op('table_config')
        layout_table = op('table_layout') if op('table_layout') else None

    panels = {}
    for row in range(1, config_table.numRows):
        panel = cell(config_table, row, 'panel')
        widget = {
                'type':    cell(config_table, row, 'type'),
                'label':   cell(config_table, row, 'label'),
                'channel': cell(config_table, row, 'channel'),
                'default': float(cell(config_table, row, 'default') or 0),
                }
        for field in ('width', 'height', 'size', 'value', 'default_x', 'default_y'):
            v = cell(config_table, row, field)
            if v:
                widget[field] = float(v)
        for field in ('channel_x', 'channel_y', 'icon', 'tooltip'):
            v = cell(config_table, row, field)
            if v:
                widget[field] = v
        for field in ('midi_cc', 'midi_ch'):
            v = cell(config_table, row, field)
            if v:
                widget[field] = int(v)
        panels.setdefault(panel, []).append(widget)

    layout = []
    if layout_table:
        rows_seen     = {}
        cols_seen     = {}
        cells         = {}
        direction_map = {}
        max_per_map   = {}

        for r in range(1, layout_table.numRows):
            row_idx = int(cell(layout_table, r, 'row'))
            col_idx = int(cell(layout_table, r, 'col'))
            panel   = cell(layout_table, r, 'panel')
            rf      = cell(layout_table, r, 'row_flex')
            cf      = cell(layout_table, r, 'col_flex')
            d       = cell(layout_table, r, 'direction')
            mp      = cell(layout_table, r, 'max_per')

            if row_idx not in rows_seen and rf:
                rows_seen[row_idx] = float(rf)
            if (row_idx, col_idx) not in cols_seen and cf:
                cols_seen[(row_idx, col_idx)] = float(cf)

            cells[(row_idx, col_idx)]         = panel
            direction_map[(row_idx, col_idx)] = d if d else 'row'
            max_per_map[(row_idx, col_idx)]   = int(mp) if mp else None

        for row_idx in sorted(rows_seen.keys()):
            col_indices = sorted(k[1] for k in cols_seen if k[0] == row_idx)
            cols = []
            for col_idx in col_indices:
                panel_name = cells.get((row_idx, col_idx), '')
                cols.append({
                    'col':       col_idx,
                    'col_flex':  cols_seen.get((row_idx, col_idx), 1),
                    'panel':     panel_name,
                    'widgets':   panels.get(panel_name, []),
                    'direction': direction_map.get((row_idx, col_idx), 'row'),
                    'max_per':   max_per_map.get((row_idx, col_idx), None),
                    })
            layout.append({
                'row':      row_idx,
                'row_flex': rows_seen.get(row_idx, 1),
                'cols':     cols,
                })
    else:
        layout = [
                {
                    'row': i + 1,
                    'row_flex': 1,
                    'cols': [{'col': 1, 'col_flex': 1, 'panel': name, 'widgets': widgets}]
                    }
                for i, (name, widgets) in enumerate(panels.items())
                ]

    return json.dumps(layout)

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


