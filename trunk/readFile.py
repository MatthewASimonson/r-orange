"""
<name>Read Files</name>
<description>Read files</description>
<icon>icons/readcel.png</icons>
<priority>10</priority>
"""

from OWRpy import *
from OWWidget import *
import OWGUI

class readFile(OWWidget,OWRpy):
	
	def __init__(self, parent=None, signalManager=None):
		OWWidget.__init__(self, parent, signalManager, "File", wantMainArea = 0, resizingEnabled = 1)
		OWRpy.__init__(self)
		self.inputs = None
        
		self.outputs = [("data.frame", orange.Variable),("Examples", ExampleTable)]
		box = OWGUI.widgetBox(self.controlArea, "Data File", addSpace = True, orientation=0)
		self.filecombo = QComboBox(box)
		self.filecombo.setMinimumWidth(150)
		box.layout().addWidget(self.filecombo)
		button = OWGUI.button(box, self, '...', callback = self.browseFile, width = 25, disabled=0)
		box = OWGUI.widgetBox(self.controlArea, "Info", addSpace = True)
		self.infoa = OWGUI.widgetLabel(box, 'No data loaded.')
		self.infob = OWGUI.widgetLabel(box, 'file_suffix: ' + self.variable_suffix)
		self.warnings = OWGUI.widgetLabel(box, ' ')
	
	
	def browseFile(self): #should open a dialog to choose a file that will be parsed to set the wd
		#something to handle the conversion
		r('filename' + self.variable_suffix + ' <- choose.files()')
		#self.infob.setText(r['filename' + self.variable_suffix])
		if r.length(r['filename' + self.variable_suffix]) == 0:
			return
		
		r('data' + self.variable_suffix + '= read.delim(filename' + self.variable_suffix + ',na.strings="?")')
		self.infoa.setText("data loaded")
		self.infob.setText("Number of rows: " + str(r.nrow(r['data' + self.variable_suffix])))
		self.warnings.setText("")

		self.send("data.frame", 'data' + self.variable_suffix)
		self.send("Examples", self.convertDataframeToExampleTable('data' + self.variable_suffix))