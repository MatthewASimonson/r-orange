"""
<name>scale</name>
<tags>Prototypes</tags>
"""
from OWRpy import * 
import redRGUI 
from libraries.base.signalClasses.RMatrix import RMatrix as redRRMatrix
from libraries.base.qtWidgets.button import button
from libraries.base.qtWidgets.radioButtons import radioButtons
class RedRscale(OWRpy): 
    settingsList = []
    def __init__(self, parent=None, signalManager=None):
        OWRpy.__init__(self)
        self.setRvariableNames(["scale"])
        self.data = {}
        self.RFunctionParam_x = ''
        self.inputs.addInput('id0', 'x', redRRMatrix, self.processx)

        self.outputs.addOutput('id0', 'scale Output', redRRMatrix)

        
        
        self.RFunctionParamscale_radioButtons =  radioButtons(self.controlArea,  label = "Scale:", buttons = ['Yes', 'No'], setChecked = 'No', orientation = 'horizontal')
        self.RFunctionParamcenter_radioButtons =  radioButtons(self.controlArea,  label = "Center:", buttons = ['Yes', 'No'], setChecked = 'No', orientation = 'horizontal')
        redRCommitButton(self.bottomAreaRight, "Commit", callback = self.commitFunction)
    def processx(self, data):
        if not self.require_librarys(["base"]):
            self.status.setText('R Libraries Not Loaded.')
            return
        if data:
            self.RFunctionParam_x=data.getData()
            #self.data = data
            self.commitFunction()
        else:
            self.RFunctionParam_x=''
    def commitFunction(self):
        if unicode(self.RFunctionParam_x) == '': return
        injection = []
        if unicode(self.RFunctionParamscale_radioButtons.getChecked()) == 'Yes':
            string = 'scale = TRUE'
            injection.append(string)
        else:
            string = 'scale = FALSE'
            injection.append(string)
        if unicode(self.RFunctionParamcenter_radioButtons.getChecked()) != 'Yes':
            string = 'center = TRUE'
            injection.append(string)
        else:
            string = 'center = FALSE'
            injection.append(string)
        inj = ','.join(injection)
        self.R(self.Rvariables['scale']+'<-scale(x='+unicode(self.RFunctionParam_x)+','+inj+')', wantType = 'NoConversion')
        self.R('row.names('+self.Rvariables['scale']+')<-row.names('+self.RFunctionParam_x+')', wantType = 'NoConversion')
        newData = redRRMatrix(data = self.Rvariables["scale"]) # moment of variable creation, no preexisting data set.  To pass forward the data that was received in the input uncomment the next line.
        #newData.copyAllOptinoalData(self.data)  ## note, if you plan to uncomment this please uncomment the call to set self.data in the process statemtn of the data whose attributes you plan to send forward.
        self.rSend("id0", newData)
    def getReportText(self, fileDir):
        text = 'Data was centered: %s \n\n' % (unicode(self.RFunctionParamcenter_radioButtons.getChecked()))
        text += 'Data was scaled: %s \n\n' % (unicode(self.RFunctionParamscale_radioButtons.getChecked()))
        return text
