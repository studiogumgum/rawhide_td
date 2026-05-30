from typing import Self, Any, Optional
from copy import copy
"""
Scene data format
scenedata = {
    <id>: {
        'FixtureID': <id>,
        'index': <pointindex>,
        'attributes': {
            <attr>: value (float)
        }
    }
}
"""
Filter = dict[str, set]
SceneData = dict[int, dict[str, Any]]
class Scene:
    def __init__(self, data: dict):
        self._name: str = data.get('name', '')
        self._scenedata: SceneData = data.get('scenedata', {})


    def update(self, scene, filter: Optional[Filter]=None, merge: str='merge'):
        ''' update this scene's data from input scene '''
        if filter:
            scene = scene.filtered(filter)
        if merge == 'merge':
            self.merge(scene)

        elif merge == 'remove':
            _state = copy(self._scenedata)
            for id, data in self._scenedata.items():
                for attr in data.keys():
                    _state = self._del_attr_data(_state, id, attr)
            if len(_state[id].keys()) == 0:
                _state.pop(id)
            self._scenedata = _state

    @property
    def data(self) -> dict:
        return self._scenedata


    def filtered(self, filter: Filter) -> 'Scene':
        ''' 
            return a filtered copy of this Scene
        '''


        filter_attrs = filter.get('attributes', None)
        filter_ids = filter.get('fixtures', None)
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
                    filtered_scene: SceneData = select_ids

        return Scene(filtered_scene)

    def merge(self, scene: Self) -> None:
        """ merge the data of <scene> with this scene's data """

        def _deepupdate(d: SceneData, u: SceneData) -> SceneData:
            for k, v in u.items():
                if isinstance(v, collections.abc.Mapping):
                    d[k] = _deepupdate(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        datacopy = copy(self._scenedata)
        merged = _deepupdate(datacopy, scene.data)
        self._scenedata = merged

    def _del_attr_data(self, state, id: int, attr: str):
        ''' delete attribute data from fixture <id>, attribute <attr> '''

        fixture_entry = state[id]
        attr_data = copy(fixture_entry)
        attr_data.pop(attr, None)
        state[id] = attr_data

        return state
