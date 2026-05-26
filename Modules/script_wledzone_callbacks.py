"""
zone_script_dat.py — TouchDesigner Zone Script DAT
====================================================
Prototype for the child zone COMP's internal logic.

Network structure:
    [Constant CHOP r/g/b/w]
        → [CHOP to DAT]
            → [this Script DAT]  — builds JSON, fires request on debounce
    [Timer CHOP]  — one-shot 0.2s debounce timer
    [Web Client DAT]  — fires HTTP request

DAT names assumed:
    - This DAT:         zone_script
    - Web Client DAT:   webclient1
    - Timer CHOP:       timer1

Usage from elsewhere in the network:
    op('zone_script').module.set_zone({'r': 1.0, 'bri': 0.5})
    op('zone_script').module.zone_on()
    op('zone_script').module.zone_off()
"""

import json

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HUB_URL   = "http://192.168.50.9:5000"   # Pi's VLAN 1 address
ZONE_NAME = "lx-bar-01"
TIMEOUT   = 3000                          # milliseconds, per webclientDAT API

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _post(params: dict):
    """Fire a POST to the hub immediately, no debounce."""
    url = f"{HUB_URL}/zone/{ZONE_NAME}"
    opex('webclient').request(
            url,
            "POST",
            header={"Content-Type": "application/json"},
            data=json.dumps(params),
            timeout=TIMEOUT
            )


def _read_chops() -> dict:
    """Read current r/g/b/w values from the wired CHOP to DAT input."""
    src = opex('script_wledzone').inputs[0]
    if src is None or src.numRows < 2:
        return {}
    # CHOPtoDAT default format: column 0 = channel name, column 1 = value
    values = {}
    for row in range(src.numRows):
        name = src[row, 0].val
        val  = float(src[row, 1].val)
        if name in ('r', 'g', 'b', 'w', 'bri'):
            values[name] = val
        # test
        values['transition'] = 10;
    return values

# ---------------------------------------------------------------------------
# Debounce — called by Timer CHOP callbacks DAT on onDone
# ---------------------------------------------------------------------------

def send_pending():
    """
    Called by the Timer CHOP's callbacks DAT when the debounce timer completes.
    Reads current CHOP values and fires the request.
    """
    params = _read_chops()
    if params:
        debug(params)
        _post(params)

# ---------------------------------------------------------------------------
# Public interface — call from parent COMP or other DATs
# ---------------------------------------------------------------------------

def set_zone(params: dict):
    """
    Set zone parameters and restart the debounce timer.
    Partial updates supported — omit any key to preserve device state.

    Examples:
        op('zone_script').module.set_zone({'r': 1.0, 'g': 0.0, 'b': 0.0, 'w': 0.0, 'bri': 0.8})
        op('zone_script').module.set_zone({'bri': 0.5})
    """
    op('timer_debounce').par.start.pulse()


def zone_on():
    """Turn zone on, preserving current colour and brightness."""
    _post({'on': True})


def zone_off():
    """Turn zone off."""
    _post({'on': False})


# ---------------------------------------------------------------------------
# TouchDesigner cook entry point
# ---------------------------------------------------------------------------

def onCook(scriptDAT):
    opex('timer_debounce').par.start.pulse()
    #send_pending()
    pass   # driven by external calls and timer, not by cooking
