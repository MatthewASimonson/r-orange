"""
<name>Melt DF</name>
<author>Generated using Widget Maker written by Kyle R. Covington</author>
<tags>Data Manipulation</tags>
<icon>icons/RExecutor.png</icon>
<priority>2060</priority>
"""
from OWRpy import * 
import OWGUI 
class Melt_DF(OWRpy): 
    settingsList = ['RFunctionParam_data']
    def __init__(self, parent=None, signalManager=None):
        OWRpy.__init__(self, parent, signalManager, "File", wantMainArea = 0, resizingEnabled = 1)
        self.setRvariableNames(["melt.data.frame"])
        self.RFunctionParam_na_rm = 0
        self.RFunctionParam_measure_var = ""
        self.RFunctionParam_variable_name = "variable"
        self.RFunctionParam_id_var = ""
        self.RFunctionParam_data = ''
        self.loadSettings()
        self.inputs = [("data", RvarClasses.RDataFrame, self.processdata)]
        self.outputs = [("melt.data.frame Output", RvarClasses.RDataFrame)]
        
        box = OWGUI.widgetBox(self.controlArea, "Widget Box")
        OWGUI.comboBox(box, self, "RFunctionParam_na_rm", label = "Remove NA:", items = ['Yes', 'No'])
        OWGUI.lineEdit(box, self, "RFunctionParam_measure_var", label = "measure_var:")
        OWGUI.lineEdit(box, self, "RFunctionParam_variable_name", label = "variable_name:") 
        OWGUI.lineEdit(box, self, "RFunctionParam_id_var", label = "id_var:")
        OWGUI.button(box, self, "Commit", callback = self.commitFunction)
    def RWidgetReload(self):
        self.commitFunction()
    def processdata(self, data):
        if data:
            self.require_librarys(['reshape'])
            self.RFunctionParam_data=data["data"]
            self.commitFunction()
    def commitFunction(self):
        self.require_librarys(['reshape'])
        if self.RFunctionParam_na_rm == 0: pna = 'TRUE'
        else: pna = 'FALSE'
        if self.RFunctionParam_data == '': return
        self.R(self.Rvariables['melt.data.frame']+'<-melt.data.frame(data='+str(self.RFunctionParam_data)+',na.rm='+str(pna)+',measure.var='+str(self.RFunctionParam_measure_var)+',variable.name="'+str(self.RFunctionParam_variable_name)+'",id.var='+str(self.RFunctionParam_id_var)+')')
        self.rSend("melt.data.frame Output", {"data":self.Rvariables["melt.data.frame"]})
