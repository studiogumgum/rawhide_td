
from TDStoreTools import StorageManager
import TDFunctions as TDF

class Stream:
    """
    Web RTC Stream Handler Extension
    """
    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp
        self._webrtc = self.ownerComp.opex('webrtc')
        self._connections = {}

    def RTC(self):
        return self._webrtc

    @property
    def Connections(self):
        return self._connections

        
    def InitConnection(self, client, msg):
        #debug('Init RTC connection')
        connId = self._webrtc.openConnection()
        self._connections[connId] = {'client': client}
        self._webrtc.addTrack(connId, 'stream1', 'video')
        self._webrtc.setRemoteDescription(connId, 'offer', msg['sdp'])
        self._webrtc.createAnswer(connId)

    def CloseConnection(self, connId=None):
        
        if not connId:
            for cid in self._connections.keys(): 
                self._webrtc.closeConnection(cid)
        else:
            if self.connid_valid(connId):
                self._webrtc.closeConnection(connId)
            else:
                parent.WebUI.Warning(
                        f'no client found for connId {connId}',
                        source='RTC'
                        )

    def connid_valid(self, connId) -> bool:
        return connId in list(self._connections.keys())

    def SendToRTCClient(self, connId, msg):
        import json
        entry = self._connections.get(connId)
        if entry:
            parent.WebUI.Send(json.dumps(msg), entry['client'])
        else:
            parent.WebUI.Warning(
                    f'no client found for connId {connId}',
                    source='RTC'
                    )


    def CleanupClient(self, client):
        stale = [cid for cid, entry in self._connections.items()
                 if entry['client'] == client]
        for cid in stale:
            self._webrtc.closeConnection(cid)

            del self._connections[cid]

    def AddIceCandidate(self, client, msg):
        for id, entry in self._connections.items():
            c = entry['client']
            if c == client:

                c = msg['candidate']
                parent.WebUI.Debug(
                        f'Add Ice Candidate {c}',
                        source='RTC'
                        )
                self._webrtc.addIceCandidate(
                        id,
                        c['candidate'],
                        c['sdpMLineIndex'],
                        c['sdpMid']
                        )
                return
        parent.WebUI.Warning(
                f'no connection id found for client {client}',
                source='RTC'
                )
    # def onDestroyTD(self):
    #   """
    #   Called when the extension or component is being deleted. Use this
    #   instead of __del__ for cleanup tasks.
    #   """
    #   debug("onDestroyTD called")

    # def onInitTD(self):
    #   """
    #   Called after the extension is fully initialized and attached to the 
    #   component. Use this instead of __init__ for tasks that require other
    #   components' extensions to be available, or that use promoted members.
    #   """
    #   debug("onInitTD called")
