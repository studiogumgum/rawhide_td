from scene import Scene
from TDStoreTools import StorageManager
import TDFunctions as TDF

class SceneExt:
    """
    SceneExt description
    """
    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp
        self._scene_output = ownerComp.opex('null_scene_output')


    def GetCurrentState(self, filter=None):
        """
        Convert the current fixture attributes state into a dict for storing
        in global scene storage
        """
        data = {}
        s = self._scene_output
        for row in range(1, s.numRows):
            key = s[row, 'FixtureID'].val
            data[key] = {}
            for heading in s.row(0):
                if heading.val != "FixtureID":
                    data[key][heading.val] = mod.dat_utils.cast_cell(s[row, heading.col])
            if filter:
                return Scene(data).filter(filter)

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
