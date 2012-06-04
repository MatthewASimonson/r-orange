"""
<name>Generic ANOVA</name>
<description>Performed ANOVA on any model or data received.  This can result in errors if inappropriate models are supplied.</description>
<tags>Advanced Stats</tags>
<icon>stats.png</icon>
"""
from OWRpy import * 
import redRGUI, signals
import redRGUI

class anova(OWRpy): 
    globalSettingsList = ['commit']
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.RFunctionParam_object = ''
        self.saveSettingsList.extend(['RFunctionParam_object'])
        self.inputs.addInput('id0', 'object', 'All', self.processobject)

        
        box = redRGUI.base.groupBox(self.controlArea, "Output")
        self.commit = redRGUI.base.commitButton(self.bottomAreaRight, "Commit", callback = self.commitFunction,
        processOnInput=True)
        self.RoutputWindow = redRGUI.base.textEdit(box,label='R Output', displayLabel=False)
        
    def onLoadSavedSession(self):
        self.commitFunction()
        
    def processobject(self, data):
        if data:
            self.RFunctionParam_object=data.getData()
            if self.commit.processOnInput():
                self.commitFunction()
        else: self.RFunctionParam_object = ''
    def commitFunction(self):
        if self.RFunctionParam_object == '': return
        self.R('txt<-capture.output('+'anova(object='+unicode(self.RFunctionParam_object)+'))')
        self.RoutputWindow.clear()
        tmp = self.R('paste(txt, collapse ="\n")')
        self.RoutputWindow.insertPlainText(tmp)
