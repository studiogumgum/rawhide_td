from TDStoreTools import StorageManager
import TDFunctions as TDF
import collections.abc
from copy import copy
class Scene:
    def __init__(self, name: str, data={}):
        self._name: str = name
        self._scenedata = data.get('scenedata', {})


    def update(self, state_dict, filter=None, merge='merge'):
        ''' update scene data from <state_dict> '''
        if merge == 'merge':
            self._scenedata = self._deepupdate(stored_scene, state_dict)

        elif merge == 'remove':
            _state = copy(state_dict)
            for id, data in state_dict.items():
                for attr in data.keys():
                    _state = self._del_attr_data(_state, id, attr)
            if len(_state[id].keys()) == 0:
                _state.pop(id)
            self._scenedata = _state

    def _del_attr_data(self, scenedata: dict, id: int, attr: str):
        ''' delete attribute data from fixture <id>, attribute <attr> '''

        #print(f'deleting attr {attr} from {id}')
        _scene = copy(scenedata)
        fixture_entry = _scene[id]
        attr_data = copy(fixture_entry)
        print(attr_data)
        attr_data.pop(attr, None)
        _scene[id] = attr_data
        return _scene

    def _deepupdate(self, d: dict, u: dict) -> dict:
        """ update a nested dict (d) with another nested dict (u) """
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self._deepupdate(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def filter(self, filter):
        ''' 
        delete attribute data from fixture <id>, attribute <attr> 

        scenedata = {
            <id>: {
                'FixtureID': <id>,
                'index': <pointindex>,
                'attributes': {
                    <attr>: value (float)
                }
            }
        }
        filter = {
            'attributes': <set of named attributes to keep>
            'fixtures': <set of fixture ids to keep>
        }
        first, filter by ids
        '''

            
        filter_attrs = filter.get('attributes', None)
        filter_ids = filter.get('fixtures', None)
        #print(f'deleting attr {attr} from {id}')
        sd = copy(self._scenedata)
        filtered_scene = {}
        if filter_ids:
            # iterate over dict filtered by fixture ids
            select_ids = {id:data for (id,data) in sd.items() if id in filter_ids}
            if filter_attrs:
                for id, data in select_ids.items():
                    # filter by attribute
                    data_filtered = copy(data)
                    attrs = {attr:val for 
                             (attr, val) in 
                             data['attributes'].items() if
                             attr in filter_attrs
                             }
                    data_filtered['attributes'] = attrs
                    filtered_scene[id] = data_filtered
            else:
                filtered_scene = select_ids

        return filtered_scene

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
             'property': True, 'dependable': False}
        ]

        self.stored = StorageManager(self, ownerComp, storedItems)

    def _deepupdate(self, d: dict, u: dict) -> dict:
        """ update a nested dict (d) with another nested dict (u) """
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self._deepupdate(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _del_attr_data(self, scenedata: dict, id: int, attr: str):
        ''' delete attribute data from fixture <id>, attribute <attr> '''

        #print(f'deleting attr {attr} from {id}')
        _scene = copy(scenedata)
        fixture_entry = _scene[id]
        attr_data = copy(fixture_entry)
        print(attr_data)
        attr_data.pop(attr, None)
        _scene[id] = attr_data
        return _scene

    def _filter_attr_data(self, scenedata: dict, filter):
        ''' 
        delete attribute data from fixture <id>, attribute <attr> 

        scenedata = {
            <id>: {
                'FixtureID': <id>,
                'index': <pointindex>,
                'attributes': {
                    <attr>: value (float)
                }
            }
        }
        filter = {
            'attributes': <set of named attributes to keep>
            'fixtures': <set of fixture ids to keep>
        }
        first, filter by ids
        '''

            
        filter_attrs = filter.get('attributes', None)
        filter_ids = filter.get('fixtures', None)
        #print(f'deleting attr {attr} from {id}')
        sd = copy(scenedata)
        filtered_scene = {}
        if filter_ids:
            # iterate over dict filtered by fixture ids
            select_ids = {id:data for (id,data) in sd.items() if id in filter_ids}
            if filter_attrs:
                for id, data in select_ids.items():
                    # filter by attribute
                    data_filtered = copy(data)
                    attrs = {attr:val for 
                             (attr, val) in 
                             data['attributes'].items() if
                             attr in filter_attrs
                             }
                    data_filtered['attributes'] = attrs
                    filtered_scene[id] = data_filtered
            else:
                filtered_scene = select_ids

        return filtered_scene

    def LoadScene(self, scene_name, fixture_comps=None, filter=None):
        scene_data = self.stored['Scenes'].get(scene_name, None)
        if not scene_data:
            debug(f'{scene_name} not found')
            return

        if not fixture_comps:
            fixture_comps = parent.Project.fetch('FixtureComps')

        if filter:
            scene_data = self._filter_attr_data(scene_data, filter)

        print(scene_data)

        return
        for f in fixture_comps:
            f.SceneManager.LoadScene(scene_data)

    def StoreScene(self, scene_name, fixture_comps=None, merge='merge', filter=None):

        if not fixture_comps:
            fixture_comps = parent.Project.fetch('FixtureComps')
        for f in fixture_comps:

            scene_data = f.opex('Scenes').GetCurrentState(filter=filter)
            stored_scene = self.stored['Scenes'].get(scene_name, None)
            if not stored_scene or merge == 'overwrite':
                self.stored['Scenes'][scene_name] = Scene(scene_data)
            else:
                self.stored['Scenes'][scene_name].update(merge=merge, filter=filter)
                if merge == 'merge':
                    stored_scene = self._deepupdate(stored_scene, scene_data)
                    self.stored['Scenes'][scene_name] = stored_scene

                elif merge == 'remove':
                    _scene = copy(self.stored['Scenes'][scene_name])
                    for id, data in scene_data.items():
                        for attr in data.keys():
                            _scene = self._del_attr_data(_scene, id, attr)
                    if len(_scene[id].keys()) == 0:
                        _scene.pop(id)
                    self.stored['Scenes'][scene_name] = _scene








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
