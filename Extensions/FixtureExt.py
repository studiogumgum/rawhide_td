
from TDStoreTools import StorageManager
from typing import Union, Optional
import dat_utils

class FixtureExt:
    """
    FixtureExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp
        self._prog_vals = ownerComp.opex('prog_vals_table')
        self._patch = ownerComp.opex('PatchFixtures/select_patch')
        self._scenecontrol = ownerComp.opex('Scenes')
        self._dmxout = ownerComp.opex('dmxfixture')
        self._attribute_table = ownerComp.opex('fixture_attributes')
        self._attributes_to_dict()


    def initProgrammer(self):
        t = self._prog_vals
        t.clear()
        t.appendRow(['FixtureID', 'index'] + list(self.fixture_attrs.keys()))
        for index, row in enumerate(self._patch.rows()[1:]):
            t.appendRow([row[0].val, index])

    @property
    def fixture_ids(self):
        return self._patch.col('Fixture ID', val=True)[1:]

    @property
    def FixtureList(self) -> list[tuple[int, int]]:
        ''' list of tuples (fixture_id, fixture_point_index) '''
        ids = [int(i) for i in self._patch.col('Fixture ID', val=True)[1:]]
        idxs = [int(i) for i in self._patch.col('index', val=True)[1:]]
        return list(zip(ids, idxs))

    @property
    def FixtureCount(self):
        return self._fixturecount

    def SetAttribute(self, attr: str, val: float, id=None):
        fixture_ids = self._patch.col('Fixture ID', val=True)[1:]
        if id:
            if isinstance(id, list):
                for i in id:
                    self.set_attr(i, attr, val)
            else:
                self.set_attr(id, attr, val)
        else:
            # no id given, set all fixtures' attribute
            for i in range(self._patch.numRows - 1):
                fixture_id = self.fixture_ids[i]
                self.set_attr(fixture_id, attr, val)



    def set_attr(self, id: int, attr: str, val: float):
        try:
            self._prog_vals[str(id), attr] = val
        except td.tdError as e:
            debug(f'{e}, index [{id}, {attr}]')


    @property
    def SceneActive(self):
        return self.ownerComp.fetch('SceneActive', False)

    @SceneActive.setter
    def SceneActive(self, state: bool):
        self.ownerComp.store('SceneActive', True)
        self.SceneAttributes = self.fixture_attrs



    # def onDestroyTD(self):
    #   """
    #   Called when the extension or component is being deleted. Use this
    #   instead of __del__ for cleanup tasks.
    #   """
    #   debug("onDestroyTD called")


    def _attributes_to_dict(self):
        key_col = 'Attribute Name'
        value_cells = self._attribute_table.row(0)[1:]
        self.fixture_attrs = {}
        for i in range(1, self._attribute_table.numRows):
            try:
                k = self._attribute_table[i, key_col].val
            except AttributeError:
                print(f'cell {i, key_col} not found')
            self.fixture_attrs[k] = {}
            for c in value_cells:
                subkey = self._attribute_table[0, c.col].val
                self.fixture_attrs[k][c.val] = dat_utils.cast_cell(
                    self._attribute_table[i, subkey]
                )

    def onInitTD(self):
        self._fixturecount = self._dmxout.numPrims(delayed=True) - 1
        stored_items = [{'name': 'FixtureAttributes',
                        'default': {},
                         'property': True,
                         'dependable': True,
                         'readonly': True}]
        self.stored = StorageManager(self, self.ownerComp, stored_items)
        self.stored['FixtureAttributes'] = self.fixture_attrs
        self.initProgrammer()
