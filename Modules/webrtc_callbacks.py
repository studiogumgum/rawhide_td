import json
"""
WebRTC DAT Callbacks

me - this DAT.
"""

def onOffer(webrtcDAT: webrtcDAT, connectionId: str, localSdp: str):
    """
    Triggered after webrtcDAT.createOffer.
    This callback should set the local description then pass it on to the
    remote peer via the signalling server.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        localSdp: Local SDP offer
    """
    webrtcDAT.setLocalDescription(connectionId, 'offer', localSdp, stereo=False)
    # Send localSdp to signalling server
    return

def onAnswer(webrtcDAT: webrtcDAT, connectionId: str, localSdp: str):
    """
    Triggered after webrtcDAT.createAnswer.
    This callback should set the local description then pass it on to the
    remote peer via the signalling server.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        localSdp: Local SDP answer
    """
    try:
        webrtcDAT.setLocalDescription(connectionId, 'answer', localSdp, stereo=False)
        msg = {'type': 'rtc_answer', 'sdp': localSdp}
        parent.Stream.SendToRTCClient(connectionId, msg)
    except Exception as e:
        parent.WebUI.Error(f'Error in onAnswer: {e}', source='RTC')

    # Send localSdp to signalling server
    return

def onNegotiationNeeded(webrtcDAT: webrtcDAT, connectionId: str):
    """
    Triggered when changes to the connection require negotiation via the
    signalling server (e.g. webrtcDAT.addTrack, webrtcDAT.removeTrack).

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
    """
    return

def onIceCandidate(webrtcDAT: webrtcDAT, connectionId: str, candidate: str,
                   lineIndex: int, sdpMid: str):
    """
    Triggered when a local ICE candidate is gathered.
    Local ICE candidates should be sent to remote peer via signalling server.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        candidate: ICE candidate string
        lineIndex: Line index in SDP
        sdpMid: SDP media ID
    """
    # Send candidate to signalling server
    try:
        msg = {'type': 'rtc_ice', 'candidate': candidate}
        parent.Stream.SendToRTCClient(connectionId, msg)
    except Exception as e:
        parent.WebUI.Error(f'Error in onIceCandidate: {e}', source='RTC')
    return

def onIceCandidateError(webrtcDAT: webrtcDAT, connectionId: str,
                        errorText: str):
    """
    Triggered when an ICE candidate error occurs.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        errorText: Error description
    """
    parent.WebUI.Error(errorText, source='RTC')
    return

def onTrack(webrtcDAT: webrtcDAT, connectionId: str, trackId: str,
            type: str):
    """
    Triggered on remote track added.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        trackId: Track identifier
        type: Track type
    """
    webrtcDAT.createAnswer(connectionId)
    return

def onRemoveTrack(webrtcDAT: webrtcDAT, connectionId: str, trackId: str,
                  type: str):
    """
    Triggered on remote track removed.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        trackId: Track identifier
        type: Track type
    """
    return

def onDataChannel(webrtcDAT: webrtcDAT, connectionId: str,
                  channelName: str):
    """
    Triggered when data channel is created remotely.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        channelName: Name of the data channel
    """
    return

def onDataChannelOpen(webrtcDAT: webrtcDAT, connectionId: str,
                      channelName: str):
    """
    Triggered when data channel is opened.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        channelName: Name of the data channel
    """
    return

def onDataChannelClose(webrtcDAT: webrtcDAT, connectionId: str,
                       channelName: str):
    """
    Triggered when data channel is closed.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        channelName: Name of the data channel
    """
    return

def onData(webrtcDAT: webrtcDAT, connectionId: str, channelName: str,
           data: str):
    """
    Triggered on receive data through data channel.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        channelName: Name of the data channel
        data: Received data
    """
    return

def onConnectionStateChange(webrtcDAT: webrtcDAT, connectionId: str,
                            newState: str):
    """
    Triggered when connection state changes.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        newState: New connection state
    """
    return

def onSignalingStateChange(webrtcDAT: webrtcDAT, connectionId: str,
                           newState: str):
    """
    Triggered when signaling state changes.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        newState: New signaling state
    """
    return

def onIceConnectionStateChange(webrtcDAT: webrtcDAT, connectionId: str,
                               newState: str):
    """
    Triggered when ICE connection state changes.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        newState: New ICE connection state
    """
    return

def onIceGatheringStateChange(webrtcDAT: webrtcDAT, connectionId: str,
                              newState: str):
    """
    Triggered when ICE gathering state changes.

    Args:
        webrtcDAT: The connected WebRTC DAT
        connectionId: UUID of the connection
        newState: New ICE gathering state
    """
    return
