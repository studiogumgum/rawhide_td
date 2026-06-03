import logging
import json
import platform
import hostconfig ## dict of hostnames where we run in debug mode
import secrets
class WebUI:
    """
    Top-level facade for the BUSKER web UI system.
    
    Promoted members are accessible from anywhere in the network.
    All sub-systems (WebServer, RTC, Views, Style, Presets) are
    accessed through this extension rather than directly.

    Routing config coLtrols which log sources get forwarded to
    the browser. Sources not listed fall through to 'default'.
    """

    # minimum level and handlers per source
    # handlers: 'textport' is handled by the logger COMP itself
    #           'webui'    forwards to browser via tdlog WS message
    LOG_ROUTES = {
        'WebServer':     {'min_level': logging.INFO,    'webui': True},
        'RTC':           {'min_level': logging.DEBUG,   'webui': True},
        'PresetManager': {'min_level': logging.INFO,    'webui': True},
        'Views':         {'min_level': logging.WARNING, 'webui': False},
        'Style':         {'min_level': logging.WARNING, 'webui': False},
        'Input':         {'min_level': logging.DEBUG,   'webui': False},
        'default':       {'min_level': logging.DEBUG,   'webui': False},
    }

    # map standard level names to browser log levels
    BROWSER_LEVELS = {
        'DEBUG':    'debug',
        'INFO':     'info',
        'WARNING':  'warn',
        'ERROR':    'err',
        'CRITICAL': 'err',
    }

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self._root = ownerComp.parent()
        self._webuiHandler = None

    def onInitTD(self):
        """
        Called after all extensions are promoted and available.
        Safe to access sub-extension references here.
        """
        self._registerWebuiHandler()
        self._host_config()
        self.Stream.CloseConnection()
        run(self.WebServer.RefreshPage, delayFrames=60*3)


    def _host_config(self):
        hostname = platform.node()
        config = hostconfig.HOSTS.get(hostname, None)
        self.ownerComp.store('host', hostname)
        if not config:
            config = hostconfig.HOSTS['default']
        self.ownerComp.store('private', config['private'])
        self._set_privacy(config['private'])

    def Save(self):
        toxpath = self.ownerComp.filePath
        self.Info(f'Saving external .tox to {toxpath}')
        saved = self.ownerComp.saveExternalTox(password=secrets.KEY)
        if saved < 1:
            self.Error(f'Error saving to {toxpath}, check path settings')


    def _set_privacy(self, private: bool):
        if private and not self._root.isPrivate:
            self.Warning(f'External host {self.ownerComp.fetch("host")} detected, project locked')
            self._root.addPrivacy(secrets.KEY)
        elif not private and self._root.isPrivate:
            self.Info(f'Host {self.ownerComp.fetch("host")} approved, unlocking project')
            self._root.removePrivacy(secrets.KEY)
            


    def onDestroyTD(self):
        self._unregisterWebuiHandler()

    # ── sub-system accessors ──────────────────────────────────

    @property
    def RootComp(self):
        return self._root

    @property
    def WebServer(self):
        return self.ownerComp.opex('WebServer')

    @property
    def Stream(self):
        return self.ownerComp.opex('VideoStream')

    @property
    def Controls(self):
        return self.ownerComp.opex('UI_Controls')

    @property
    def RTC(self):
        return self.ownerComp.opex('VideoStream').RTC

    @property
    def Views(self):
        return self.ownerComp.opex('Views')

    @property
    def Style(self):
        return self.ownerComp.opex('style').Style

    @property
    def Presets(self):
        return self.ownerComp.opex('presets').PresetManager

    @property
    def Logger(self):
        return self.ownerComp.opex('webui_logger')

    @property
    def _logger(self):
        #return self.ownerComp.opex('webui_logger').ext.Logger  # the palette Logger extension
        return self.ownerComp.opex('webui_logger')

    # ── Project Status ───────────────────────────────────────────────

    @property
    def Status(self) -> dict:
        return {
            'saveTime': project.saveTime,
            'webui_version': self.ownerComp.fetch('version', ''),
            'td_version': app.version,
            'td_build': app.build,
            'deployment': self.ownerComp.fetch('deployment', 'dev'),
            'private': self.ownerComp.fetch('private'),
            'launchtime': app.launchTime,
        }

    # ── logging ───────────────────────────────────────────────

    def Log(self, level: str, message: str, source: str = 'WebUI'):
        """
        Log a message through the project Logger.
        level:  'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        source: name of the calling component/extension
        """
        browser_level = self.BROWSER_LEVELS.get(level, 'info')
        self._logger.Log(message, level=level, browser_level=browser_level, td_source=source)

    def Debug(self, message, source='WebUI'):
        self.Log('DEBUG', message, source)

    def Info(self, message, source='WebUI'):
        self.Log('INFO', message, source)

    def Warning(self, message, source='WebUI'):
        self.Log('WARNING', message, source)

    def Error(self, message, source='WebUI'):
        self.Log('ERROR', message, source)

    # ── webui log handler ─────────────────────────────────────

    # TODO: low priority, this whole thing doesn't work
    def _registerWebuiHandler(self):
        """
        Register a custom logging.Handler with the palette Logger
        that intercepts records and forwards them to the browser
        based on LOG_ROUTES.
        """
        outer = self

        class WebuiHandler(logging.Handler):
            def emit(self, record):
                try:
                    source = getattr(record, 'source', 'default')
                    route  = outer.LOG_ROUTES.get(source,
                             outer.LOG_ROUTES['default'])

                    if not route['webui']:
                        return
                    if record.levelno < route['min_level']:
                        return

                    browser_level = outer.BROWSER_LEVELS.get(
                        record.levelname, 'info')
                    prefix  = f'[{source}] ' if source else ''
                    logmsg = json.dumps({
                        'type':    'tdlog',
                        'level':   browser_level,
                        'message': prefix + record.getMessage(),
                        'source': source.lower()
                    })
                    outer.Broadcast(logmsg)
                    # outer.Broadcast({
                    #     'type':    'tdlog',
                    #     'level':   browser_level,
                    #     'message': prefix + record.getMessage(),
                    # })
                except Exception as e:
                    debug(e)
                    pass  # never let a log handler crash the network

        self._webuiHandler = WebuiHandler()
        # fixes race condition, but hacky. logger might init after us,
        # in which case this won't work
        if self._logger.extensionsReady:
            self._logger.AddExtraHandler(self._webuiHandler)

    def _unregisterWebuiHandler(self):
        if self._webuiHandler:
            self._logger.DeleteExtraHandler(self._webuiHandler)
            self._webuiHandler = None

    # ── websocket ─────────────────────────────────────────────

    def Broadcast(self, msg: dict):
        """Send a JSON-serialisable dict to all connected browser clients."""
        if self.WebServer.extensionsReady:
            self.WebServer.Broadcast(json.dumps(msg))

    def Send(self, msg, client):
        if self.WebServer.extensionsReady:
            self.WebServer.Send(msg, client)



        
        
