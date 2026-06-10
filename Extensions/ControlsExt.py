from TDStoreTools import StorageManager
import TDFunctions as TDF

class Controls:
    """
    Controls description
    """
    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp
        self._input_chop = ownerComp.opex('ui_input')

    def Update(self, msg: dict):
        self.ownerComp.store('changed',
                             {'chan': msg['channel'],
                              'val': msg['value']
                              })
        self._input_chop.cook(force=True)

    def GetControlValue(self, control_name):
        chan = self._input_chop.chan(control_name)
        if chan is None:
            return None

        return round(chan.eval(), 4)



    # def onDestroyTD(self):
    # 	"""
    # 	Called when the extension or component is being deleted. Use this
    # 	instead of __del__ for cleanup tasks.
    # 	"""
    # 	debug("onDestroyTD called")

    # def onInitTD(self):
    # 	"""
    # 	Called after the extension is fully initialized and attached to the 
    # 	component. Use this instead of __init__ for tasks that require other
    # 	components' extensions to be available, or that use promoted members.
    # 	"""
    # 	debug("onInitTD called")
