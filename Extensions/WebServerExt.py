import json
from TDStoreTools import StorageManager
from typing import Union, Optional, Any
import secrets
import dat_utils

class WebServer:
    """
    WebServer description
    """
    PUBLIC_ROUTES = ['/login', '/auth', 'style.css', '/theme']
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self._server = self.ownerComp.opex('webserver_ui')
        self._log_source = 'WebServer'
        # dict representing (<dat name>, <contenttype>, isPrivate(bool))
        self._uri_handlers = {
            '/':           ('text_html',    'text/html', True),
            '/index.html': ('text_html',    'text/html', True),
            '/login.html': ('text_login',    'text/html', False),
            '/login': ('text_login',    'text/html', False),
            '/style.css':  ('text_css',     'text/css', False),
            '/core.js':     ('text_core_js',      'application/javascript', True),
            '/widgets.js':     ('text_widgets_js',      'application/javascript', True),
            '/app.js':     ('text_js',      'application/javascript', True),
            '/midi.js':    ('text_midi_js', 'application/javascript', True),
            '/presets.js':    ('text_presets_js', 'application/javascript', True),
            '/assets/gumgum_logo.png':    ('gumgum_logo', 'image/png', False),
            '/assets/rawhide_logo.png':    ('rawhide_logo', 'image/png', False),
        }


    def onInitTD(self):
        self.RefreshPage()
        stored_items = [
            {
                'name': 'authenticated_clients',
                'default': set(),
                'property': False,
                'dependable': False,
                'readonly': True
            }
        ]

        self.stored = StorageManager(self, self.ownerComp, stored_items)
        

    def Start(self):
        ''' initialize webserverDAT '''
        parent.WebUI.Info('Web Server starting', self._log_source)
        self._server.par.active = True

    def Restart(self, delay=3):
        ''' Restart web server '''
        self.Shutdown()
        run(self.Start, delayFrames=60*delay)

    def Shutdown(self):
        if parent.WebUI.extensionsReady:
            parent.WebUI.Info('Web Server shutting down', self._log_source)
            self._server.par.active = False


    @property
    def Status(self) -> bool:
        return self._server.par.active.eval() == 1

    @property
    def Server(self):
        return self._server

    @property
    def Clients(self):
        return self._server.webSocketConnections

    def Broadcast(self, msg):
        for client in self.Clients:
            self._server.webSocketSendText(client, msg)


    def Send(self, msg, client):
        self._server.webSocketSendText(client, msg)

    def _send(self, msg, client):
        json.dumps({'test': 'test'})
        self._server.webSocketSendText(client, msg)

    def RefreshPage(self):
        self.Broadcast(
            json.dumps({'type': 'command', 'action': 'refresh'})
        )

    def RouteRequest(self, request, response) -> dict[str, str]:
        uri = request['uri']
        client_addr = request['clientAddress']
        try:
            if self.is_authenticated(client_addr):
                response = self._route_private(uri, request, response)
            else:
                response = self._route_public(uri, request, response)
        except Exception as e:
            parent.WebUI.Error(f'WebServer error: {e}', source='WebServer')
            response['data'] = json.dumps({'error': str(e)})
            response['headers'] = {'Content-Type': 'application/json'}
            response['statusCode'] = 500
            response['statusReason'] = 'Internal Server Error'

        return response

    def _handle_uri(self, uri, private=False) -> Optional[dict[str, str]]:
        response = {}

        if uri in self._uri_handlers:
            op_name, content_type, isPrivate = self._uri_handlers[uri]
            if private or not isPrivate:
                if content_type == 'image/png':
                    response['data'] = opex(f'assets/{op_name}').saveByteArray('.png')
                else:
                    response['data'] = opex(op_name).text
                response['headers'] = {'Content-Type': content_type}
            else:
                op_name, content_type, isPrivate = self._uri_handlers['/login.html']
                response['data'] = opex(op_name).text

        else:
            return None

        return response

    def _route_public(self, uri, request, response) -> dict[str, str]:

        handled_resp = self._handle_uri(uri, private=False)
        if handled_resp:
            response.update(handled_resp)

        elif uri == '/login':
            response['data']    = opex('text_login_html').text
            response['headers'] = {'Content-Type': 'text/html'}

        elif uri == '/auth' and request['method'] == 'POST':
            body     = json.loads(request['data'])
            password = body.get('passcode', '')
            # compare against whatever you store — operator storage, a table DAT, etc.
            if self.check_password(password):
                # set a session cookie or token however fits your auth approach
                self.authenticate(request.get('clientAddress'))
                response.update(self._handle_uri('/', private=True))
            else:
                response['statusCode']   = 401
                response['statusReason'] = 'Unauthorized'
                response['data']         = json.dumps({'ok': False})
                response['headers']      = {'Content-Type': 'application/json'}

        elif uri == '/theme':
            t   = parent.WebUI.opex('Styling/table_theme')
            out = {}
            for r in range(1, t.numRows):
                k = dat_utils.getCellVal(t, r, 'key')
                v = dat_utils.getCellVal(t, r, 'value')
                if k:
                    out[k] = v

            response['data']         = json.dumps(out)
            response['headers']      = {'Content-Type': 'application/json'}
        else:
            # redirect everything else to login page
            response['data']    = opex('text_login_html').text
            response['headers'] = {'Content-Type': 'text/html'}

        response['statusCode']   = 200
        response['statusReason'] = 'OK'
        return response


    def _route_private(self, uri, request, response) -> dict[str, str]:

        handled_resp = self._handle_uri(uri, private=True)
        if handled_resp:
            response.update(handled_resp)

        elif uri == '/login':
            response['data']    = opex('text_html').text
            response['headers'] = {'Content-Type': 'text/html'}

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
                k = dat_utils.getCellVal(t, r, 'key')
                v = dat_utils.getCellVal(t, r, 'value')
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

    def ProcessMessage(self, client, data):

        try:
            msg = json.loads(data)
        except json.JSONDecodeError as e:
            parent.WebUI.Error(
                f'ws: invalid JSON from {client}: {str(e)} - {data[:80]}',
                self._log_source
            )
            return

        t = msg.get('type')
        if not t:
            parent.WebUI.Error(
                f'ws: message missing type field: {data[:80]}',
                self._log_source
            )

        try:
            if t == 'control':

                parent.WebUI.Controls.Update(msg)

            elif t == 'preset_save':
                # values dict sent from browser: {channel: value}
                names = iop.PresetManager.Save(
                    msg['name'], msg['values']
                )
                # send updated list back to browser
                self.Send(client, json.dumps({'type': 'preset_list', 'names': names}))

            elif t == 'preset_recall':
                iop.PresetManager.Recall(msg['name'])

            elif t == 'preset_delete':
                names = iop.PresetManager.Delete(msg['name'])
                self.Send(client, json.dumps({'type': 'preset_list', 'names': names}))

            elif t == 'preset_list':
                names = iop.PresetManager.List()
                self.Send(client, json.dumps({'type': 'preset_list', 'names': names}))

            elif t == 'rtc_offer':
                parent.WebUI.Stream.InitConnection(client, msg)

            elif t == 'rtc_ice':
                parent.WebUI.Stream.AddIceCandidate(client, msg)

        except KeyError as e:
            parent.WebUI.Error(
                f'ws: missing field {e} in {t} message',
                self._log_source
            )

        except Exception as e:
            parent.WebUI.Error(
                f'ws: handler error [{t}]: {e}',
                self._log_source
            )

    def create_panels(self, config: tableDAT) -> dict[str, list[dict[str, Any]]]:
        panels = {}
        widget_fields = [
            ('type', True),
            ('label', True),
            ('channel', True),
            ('default', True),
            ('width', False),
            ('height', False),
            ('size', False),
            ('value', False),
            ('default_x', False),
            ('default_y', False),
            ('channel_x', False),
            ('channel_y', False),
            ('icon', False),
            ('tooltip', False),
            ('midi_cc', False),
            ('midi_ch', False)
            ]
        for row in range(1, config.numRows):
            widget = {}
            panel = dat_utils.getCellVal(config, row, 'panel')
            for field, required in widget_fields:
                v = dat_utils.getCellVal(config, row, field, cast=True)
                # skip writing fields for optional values
                if v == '':
                    if required:
                        widget[field] = v
                    else:
                        continue
                widget[field] = v
            panels.setdefault(panel, []).append(widget)
        return panels

    def BuildConfig(self, request):

        def cell(table, row, col):
            c = table[row, col]
            return c.val.strip() if c is not None else ''

        pars = request.get('pars', {})
        view_name = pars.get('view', None)

        if view_name:
            view_comp    = iop.Views.GetView(view_name)
            config_table = view_comp.opex('table_config')
            layout_table = view_comp.opex('table_layout')
        else:
            layout_table = iop.Views.opex('table_layout') if iop.Views.op('table_layout') else None
            config_table = op('table_config')

        panels = self.create_panels(config_table)

        layout = []
        if layout_table:
            rows_seen     = {}
            cols_seen     = {}
            cells         = {}
            direction_map = {}
            max_per_map   = {}

            for r in range(1, layout_table.numRows):
                row_idx = dat_utils.getCellVal(layout_table, r, 'row', cast=True)
                col_idx = dat_utils.getCellVal(layout_table, r, 'col', cast=True)
                panel   = dat_utils.getCellVal(layout_table, r, 'panel', cast=True)
                panel_label   = dat_utils.getCellVal(layout_table, r, 'panel_label', cast=True)
                rf      = dat_utils.getCellVal(layout_table, r, 'row_flex', cast=True)
                cf      = dat_utils.getCellVal(layout_table, r, 'col_flex', cast=True)
                d       = dat_utils.getCellVal(layout_table, r, 'direction', cast=True)
                mp      = dat_utils.getCellVal(layout_table, r, 'max_per', cast=True)

                if row_idx not in rows_seen and rf:
                    rows_seen[row_idx] = rf
                if (row_idx, col_idx) not in cols_seen and cf:
                    cols_seen[(row_idx, col_idx)] = cf

                cells[(row_idx, col_idx)]         = {'panel_id': panel, 'panel_label': panel_label}
                direction_map[(row_idx, col_idx)] = d if d else 'row'
                max_per_map[(row_idx, col_idx)]   = mp if mp else None

            for row_idx in sorted(rows_seen.keys()):
                col_indices = sorted(k[1] for k in cols_seen if k[0] == row_idx)
                cols = []
                for col_idx in col_indices:
                    panel_name = cells.get((row_idx, col_idx), '')['panel_id']
                    panel_label = cells.get((row_idx, col_idx), '')['panel_label']
                    cols.append({
                        'col':              col_idx,
                        'col_flex':         cols_seen.get((row_idx, col_idx), 1),
                        'panel':            panel_name,
                        'panel_label':      panel_label,
                        'widgets':          panels.get(panel_name, []),
                        'direction':        direction_map.get((row_idx, col_idx), 'row'),
                        'max_per':          max_per_map.get((row_idx, col_idx), None),

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

    ### Authentication ---------- 
    def check_password(self, password: str) -> bool:
        return password == secrets.WEB_AUTH_PASS

    def authenticate(self, client_addr):
        ip = client_addr.split(':')[0]
        self.stored['authenticated_clients'].add(ip)

    def deauthenticate(self, client_addr):
        ip = client_addr.split(':')[0]
        self.stored['authenticated_clients'].discard(ip)

    def is_authenticated(self, client_addr):
        auth = self.stored.get('authenticated_clients', set())
        # port is ephemeral, take only ip
        ip = client_addr.split(':')[0]
        return ip in auth
