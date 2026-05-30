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
class Scene:
    def __init__(self, data: dict):
        self._name: str = data.get('name', {})
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

    def _del_attr_data(self, state, id: int, attr: str):
        ''' delete attribute data from fixture <id>, attribute <attr> '''

        fixture_entry = state[id]
        attr_data = copy(fixture_entry)
        attr_data.pop(attr, None)
        state[id] = attr_data
        
        return state

    def _deepupdate(self, d: dict, u: dict) -> dict:
        """ update a nested dict (d) with another nested dict (u) """
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self._deepupdate(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def __dict__(self):
        return self._scenedata
    
    
    def filter(self, filter):
        ''' 
        return a filtered copy of this Scene

        filter = {
            'attributes': <set of named attributes to keep>
            'fixtures': <set of fixture ids to keep>
        }
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
