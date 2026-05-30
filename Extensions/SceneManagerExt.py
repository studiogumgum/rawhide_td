import collections.abc
from copy import copy

import TDFunctions as TDF
from TDStoreTools import StorageManager
from scene import Scene


class SceneManagerExt:
    """
    SceneManagerExt description
    """
    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        storedItems = [
            # Only 'name' is required...
            {'name': 'Scenes', 'default': {}, 'readOnly': False,
             'property': False, 'dependable': False}
        ]

        self.stored = StorageManager(self, ownerComp, storedItems)

    def LoadScene(self, scene_name, fixture_comps=None, filter=None):
        scene = self.stored['Scenes'].get(scene_name, None)
        if not scene:
            debug(f'{scene_name} not found')
            return

        if not fixture_comps:
            fixture_comps = parent.Project.fetch('FixtureComps')


        if filter:
            for f in fixture_comps:
                f.SceneManager.LoadScene(scene.filtered(filter))
        else:
            for f in fixture_comps:
                f.SceneManager.LoadScene(scene)

    def StoreScene(self, scene_name, fixture_comps=None, merge='merge', filter=None):

        if not fixture_comps:
            fixture_comps = parent.Project.fetch('FixtureComps')
        for f in fixture_comps:
            print(type(f))

            scene: Scene = f.opex('Scenes').GetCurrentState(filter=filter)
            stored_scene = self.stored['Scenes'].get(scene_name, None)
            if not stored_scene or merge == 'overwrite':
                self.stored['Scenes'][scene_name] = scene
            else:
                self.stored['Scenes'][scene_name].update(scene, merge=merge, filter=filter)

        # def onDestroyTD(self):
            # 	"""
        # 	Called when the extension or component is being deleted. Use this
        # 	instead of __del__ for cleanup tasks.
        # 	"""
        # 	debug("onDestroyTD called")

    def _update_scene_objs(self):
        """ 
        whenever we change the Scene class, TD complains about the objects
        no longer being the same type. The nasty workaround is to re-create
        all the scenes with an up-to-date reference every time we re-initialize
        """
        _stored_scenes = copy(self.stored['Scenes'])
        for name, scene in self.stored['Scenes'].items():
            s = Scene(scene.data)
            _stored_scenes[name] = s

        self.stored['Scenes'] = _stored_scenes

    def onInitTD(self):
        self._update_scene_objs()









