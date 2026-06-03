from TDStoreTools import StorageManager
import TDFunctions as TDF

class Views:
	"""
	Views description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self._view_list = ownerComp.opex('table_views')

	@property
	def ViewList(self):
		return self._view_list

	def GetView(self, view_name):
		views = set(self._view_list.col('name', val=True)[1:])
		if view_name not in views:
			if self.ownerComp.op(view_name) is None:
				parent.WebUI.Error(f'View {view_name} not found', source='Views')
				return None
			else:
				return self.ownerComp.opex(view_name)
		return self.ownerComp.opex(view_name)

	def GetViewState(self, view_name):
		def cell(table, row, col):
			c = table[row, col]
			return c.val.strip() if c is not None else None

		view_comp = self.GetView(view_name)
		config_table = view_comp.opex('table_config')
		state = {}

		for r in range(1, config_table.numRows):
			chan = cell(config_table, r, "channel")
			widget_type = cell(config_table, r, 'type')

			if widget_type == 'colorpicker' and chan:
				for suffix in ('r', 'g', 'b'):
					sub_channel = f'{chan}/{suffix}'
					cv = parent.WebUI.Controls.GetControlValue(sub_channel)
					if cv is not None:
						state[sub_channel] = cv

			elif widget_type == 'xypad' and chan:
				chan_x = config_table[r, "channel_x"].val
				chan_y = config_table[r, "channel_y"].val
				cvx = parent.WebUI.Controls.GetControlValue(chan_x)
				cvy = parent.WebUI.Controls.GetControlValue(chan_y)
				if cvx is not None:
					state[chan_x] = cvx
				if cvy is not None:
					state[chan_y] = cvy

			elif chan:
				cv = parent.WebUI.Controls.GetControlValue(chan)
				if cv is not None:
					state[chan] = cv

		return state

		


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
