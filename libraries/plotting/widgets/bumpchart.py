"""
<name>bumpchart</name>
<author>Generated using Widget Maker written by Kyle R. Covington</author>
<RFunctions>plotrix:bumpchart</RFunctions>
<tags>Plotting</tags>
<icon>plot.png</icon>
"""
from OWRpy import * 
import redRGUI 
from libraries.base.signalClasses.RDataFrame import RDataFrame as redRRDataFrame
from libraries.base.qtWidgets.lineEdit import lineEdit
from libraries.base.qtWidgets.tabWidget import tabWidget
from libraries.base.qtWidgets.button import button
class bumpchart(OWRpy): 
    settingsList = []
    def __init__(self, parent=None, signalManager=None):
        OWRpy.__init__(self)
        self.RFunctionParam_y = ''
        self.inputs.addInput('id0', 'y', redRRDataFrame, self.processy)

        
        box = tabWidget(self.controlArea)
        self.standardTab = box.createTabPage(name = "Standard")
        self.advancedTab = box.createTabPage(name = "Advanced")
        self.RFunctionParammar_lineEdit =  lineEdit(self.standardTab,  label = "mar:", text = 'c(2,8,5,8)')
        self.RFunctionParamlty_lineEdit =  lineEdit(self.standardTab,  label = "lty:", text = '1')
        self.RFunctionParamlabels_lineEdit =  lineEdit(self.standardTab,  label = "labels:", text = 'rownames(y)')
        self.RFunctionParamrank_lineEdit =  lineEdit(self.standardTab,  label = "rank:", text = 'TRUE')
        self.RFunctionParampch_lineEdit =  lineEdit(self.standardTab,  label = "pch:", text = '19')
        self.RFunctionParamtop_labels_lineEdit =  lineEdit(self.standardTab,  label = "top_labels:", text = 'colnames(y)')
        self.RFunctionParamcol_lineEdit =  lineEdit(self.standardTab,  label = "col:", text = 'par("fg")')
        self.RFunctionParamlwd_lineEdit =  lineEdit(self.standardTab,  label = "lwd:", text = '1')
        redRCommitButton(self.bottomAreaRight, "Commit", callback = self.commitFunction)
    def processy(self, data):
        if not self.require_librarys(["plotrix"]):
            self.status.setText('R Libraries Not Loaded.')
            return
        if data:
            self.RFunctionParam_y=data.getData()
            #self.data = data
            self.commitFunction()
        else:
            self.RFunctionParam_y=''
    def commitFunction(self):
        if str(self.RFunctionParam_y) == '': return
        injection = []
        if str(self.RFunctionParammar_lineEdit.text()) != '':
            string = 'mar='+str(self.RFunctionParammar_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamlty_lineEdit.text()) != '':
            string = 'lty='+str(self.RFunctionParamlty_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamlabels_lineEdit.text()) != '':
            string = 'labels='+str(self.RFunctionParamlabels_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamrank_lineEdit.text()) != '':
            string = 'rank='+str(self.RFunctionParamrank_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParampch_lineEdit.text()) != '':
            string = 'pch='+str(self.RFunctionParampch_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamtop_labels_lineEdit.text()) != '':
            string = 'top.labels='+str(self.RFunctionParamtop_labels_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamcol_lineEdit.text()) != '':
            string = 'col='+str(self.RFunctionParamcol_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamlwd_lineEdit.text()) != '':
            string = 'lwd='+str(self.RFunctionParamlwd_lineEdit.text())+''
            injection.append(string)
        inj = ','.join(injection)
        self.R('y<-'+str(self.RFunctionParam_y), wantType = 'NoConversion')
        self.R('bumpchart(y='+str(self.RFunctionParam_y)+','+inj+')', wantType = 'NoConversion')
    def getReportText(self, fileDir):
        if str(self.RFunctionParam_y) == '': return 'Nothing to plot from this widget'
        
        self.R('png(file="'+fileDir+'/plot'+str(self.widgetID)+'.png")', wantType = 'NoConversion')
            
        injection = []
        if str(self.RFunctionParammar_lineEdit.text()) != '':
            string = 'mar='+str(self.RFunctionParammar_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamlty_lineEdit.text()) != '':
            string = 'lty='+str(self.RFunctionParamlty_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamlabels_lineEdit.text()) != '':
            string = 'labels='+str(self.RFunctionParamlabels_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamrank_lineEdit.text()) != '':
            string = 'rank='+str(self.RFunctionParamrank_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParampch_lineEdit.text()) != '':
            string = 'pch='+str(self.RFunctionParampch_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamtop_labels_lineEdit.text()) != '':
            string = 'top.labels='+str(self.RFunctionParamtop_labels_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamcol_lineEdit.text()) != '':
            string = 'col='+str(self.RFunctionParamcol_lineEdit.text())+''
            injection.append(string)
        if str(self.RFunctionParamlwd_lineEdit.text()) != '':
            string = 'lwd='+str(self.RFunctionParamlwd_lineEdit.text())+''
            injection.append(string)
        inj = ','.join(injection)
        self.R('y<-'+str(self.RFunctionParam_y), wantType = 'NoConversion')
        self.R('bumpchart(y='+str(self.RFunctionParam_y)+','+inj+')', wantType = 'NoConversion')
        self.R('dev.off()', wantType = 'NoConversion')
        text = 'The following plot was generated:\n\n'
        #text += '<img src="plot'+str(self.widgetID)+'.png" alt="Red-R R Plot" style="align:center"/></br>'
        text += '.. image:: '+fileDir+'/plot'+str(self.widgetID)+'.png\n    :scale: 505%\n\n'
            
        return text
