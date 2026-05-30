"""
Script DAT Callbacks

me - this DAT

scriptOp - the OP which is cooking
"""

# press 'Setup Parameters' in the OP to call this function to re-create the
# parameters.
def onSetupParameters(scriptOp: scriptDAT):
    """
    Called to setup custom parameters for the Script DAT.
    """
    page = scriptOp.appendCustomPage('Custom')
    p = page.appendFloat('Valuea', label='Value A')
    p = page.appendFloat('Valueb', label='Value B')
    return

def onPulse(par: Par):
    """
    Called when a custom pulse parameter is pushed.

    Args:
        par: The parameter that was pulsed
    """
    return

def onCook(scriptOp: scriptDAT):
    """
    Called when the Script DAT needs to cook.
    """
    import re
    scriptOp.clear()
    if len(scriptOp.inputs) < 1:
        return

    if not parent().extensionsReady:
        return
    fixture_attrs = parent.FixtureGroup.FixtureAttributes
    if not fixture_attrs:
        return

    s = scriptOp.inputs[0]
    
    if s.col('FixtureID') is None or s.col('index') is None:
        return
    scriptOp.appendCol(s.col('FixtureID'))
    scriptOp.appendCol(s.col('index'))
    if s.numRows < 1:
        return
    components = {}
    attr_names = set(fixture_attrs.keys())
    for col in s.cols():
        if col[0].val in attr_names:
            scriptOp.appendCol(col)
        else:
            p = re.compile('(.*)\((\d)\)')
            match = re.match(p, col[0].val)
            if match:
                attr_name = match.group(1)
                if attr_name not in attr_names:
                    continue
                component_index = int(match.group(2))
                component_size = fixture_attrs[attr_name]['Components']
                if component_index > component_size - 1:
                    continue
                if not components.get(attr_name, None):
                    components[attr_name] = [None] * component_size
                    components[attr_name][component_index] =  [float(i.val) for i in col[1:]]
                else:
                    components[attr_name][component_index] =  [float(i.val) for i in col[1:]]
    for attr, comps in components.items():
        column = [attr] + list(zip(*comps))
        scriptOp.appendCol(column)







def onGetCookLevel(scriptOp: scriptDAT) -> CookLevel:
    """
 Sets the scriptOp's cook level, the conditions necessary to cause a cook.

 Return one of the following:
     CookLevel.AUTOMATIC - inputs changed and output being used. TD default
 behavior.
 CookLevel.ON_CHANGE - inputs changed, output used or not.
 CookLevel.WHEN_USED - every frame when output is being used
 CookLevel.ALWAYS - every frame
 """

    return CookLevel.AUTOMATIC
