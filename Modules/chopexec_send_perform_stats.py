"""
CHOP Execute DAT

me - this DAT

Make sure the corresponding toggle is enabled in the CHOP Execute DAT.
"""

def onOffToOn(channel: Channel, sampleIndex: int, val: float, 
              prev: float):
    """
    Called when a channel changes from 0 to non-zero.

    Args:
        channel: The Channel object which has changed
        sampleIndex: The index of the changed sample
        val: The numeric value of the changed sample
        prev: The previous sample value
    """
    sendPerformStats()
    return

def sendPerformStats():
 
    p = opex('out1')  # your Perform CHOP
    msg = {
        'type': 'perf',
        'fps':      round(p['fps'].eval(), 1),
        'ram':      round(p['ram_percent'].eval(), 1),   # you compute this
        'vram':     round(p['vram_percent'].eval(), 1),  # you compute this
        'gpu_temp': round(p['gputemperature'].eval(), 1)
        }
    
    try:
        if parent.WebUI.extensionsReady:
            parent.WebUI.Broadcast(msg)
    except td.tdAttributeError:
        pass

    return

def whileOn(channel: Channel, sampleIndex: int, val: float, 
            prev: float):
    """
    Called every frame while a channel is non-zero.

    Args:
        channel: The Channel object which has changed
        sampleIndex: The index of the changed sample
        val: The numeric value of the changed sample
        prev: The previous sample value
    """
    return

def onOnToOff(channel: Channel, sampleIndex: int, val: float, 
              prev: float):
    """
    Called when a channel changes from non-zero to 0.

    Args:
        channel: The Channel object which has changed
        sampleIndex: The index of the changed sample
        val: The numeric value of the changed sample
        prev: The previous sample value
    """
    return

def whileOff(channel: Channel, sampleIndex: int, val: float, 
             prev: float):
    """
    Called every frame while a channel is 0.

    Args:
        channel: The Channel object which has changed
        sampleIndex: The index of the changed sample
        val: The numeric value of the changed sample
        prev: The previous sample value
    """
    return

def onValueChange(channel: Channel, sampleIndex: int, val: float, 
                  prev: float):
    """
    Called when a channel value changes.

    Args:
        channel: The Channel object which has changed
        sampleIndex: The index of the changed sample
        val: The numeric value of the changed sample
        prev: The previous sample value
    """
    return
