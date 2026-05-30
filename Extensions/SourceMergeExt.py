
from TDStoreTools import StorageManager
import TDFunctions as TDF

class SourceMerge:
    """
    PopDmxAttrs description
    """
    LIVE_SOURCE_INDEX = 0
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self._valid_config = False
        self._fixturegroup = None
        self._sourceindex = ownerComp.opex('value_sources')
        self._livesource = ownerComp.opex('popto_live')


    def UpdateFixtureGroup(self):
        ''' attempt to retrieve the fixture attributes dict from the parent fixture group'''
        fg: td.containerComp = self.ownerComp.par.Fixturegroup.eval()
        if fg:
            try:
                self.stored['FixtureAttributes'] = fg.FixtureAttributes
            except tdAttributeError as e:
                debug(f'Fixture group {fg.name} does not have the property FixtureAttributes')
                return
        else:
            debug(f'No Fixture Group comp provided')
        debug(f'Pulled fixture attributes from {fg.name}')
        self._fixturegroup = fg
        self._valid_config = True

    def UpdateSourceIndex(self):
        '''Update source index table to align with fixture patch'''
        if not self._valid_config:
            return
        t = self._sourceindex
        t.clear()
        t.appendRow(['Fixture ID', 'index'])
        
        for id, index in self.fixturelist:
            t.appendRow([id, index])
        for attr in self.FixtureAttributes.keys():
            attrcol = [str(self.LIVE_SOURCE_INDEX)] * (t.numRows -1)
            attrcol = [attr] + attrcol
            print(attrcol)
            t.appendCol(attrcol)

    @property
    def fixturelist(self) -> list[tuple[int, int]]:
        ''' return a list of tuples (fixture_id, fixture_point_index) '''
        ids = [int(i.val) for i in self._livesource.col('FixtureID')[1:]]
        indexs = [int(i.val) for i in self._livesource.col('index')[1:]]
        return list(zip(ids, indexs))


    def onInitTD(self):
        storedItems = [
                # Only 'name' is required...
                {'name': 'FixtureAttributes', 'default': {}, 'readOnly': False,
                 'property': True, 'dependable': False},
                ]
        self.stored = StorageManager(self, self.ownerComp, storedItems)
        self.UpdateFixtureGroup()
        self.UpdateSourceIndex()

