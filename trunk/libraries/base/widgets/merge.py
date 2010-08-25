"""
<name>Merge2</name>
<description>Merges or subsets two datasets depending on options.</description>
<tags>Data Manipulation</tags>
<author>Anup Parikh (anup@red-r.org) and Kyle R Covington (kyle@red-r.org)</author>
<RFunctions>base:match,base:merge</RFunctions>
<icon>merge2.png</icon>
"""

from OWRpy import *
import redRGUI
import libraries.base.signalClasses.RDataFrame as rdf

from libraries.base.qtWidgets.radioButtons import radioButtons
from libraries.base.qtWidgets.button import button
from libraries.base.qtWidgets.checkBox import checkBox
from libraries.base.qtWidgets.listBox import listBox
from libraries.base.qtWidgets.widgetBox import widgetBox
class merge(OWRpy):
    globalSettingsList = ['mergeLikeThis']

    def __init__(self, parent=None, signalManager=None):
        OWRpy.__init__(self)
        
        self.dataParentA = {}
        self.dataParentB = {}
        self.dataA = ''
        self.dataB = ''
        
        
        self.inputs = [("Dataset A", rdf.RDataFrame, self.processA), ("Dataset B", rdf.RDataFrame, self.processB)]
        self.outputs = [("Merged", rdf.RDataFrame)]

        #default values        
        self.colAsel = None
        self.colBsel = None
        #self.forceMergeAll = 0 #checkbox value for forcing merger on all data, default is to remove instances from the rows or cols.
        
        #set R variable names
        self.setRvariableNames(['merged'])
                
        #GUI
        mainArea = widgetBox(self.controlArea,orientation='horizontal')
        self.colA = listBox(mainArea,label='From Dataset A Merge On Column:', callback = self.setcolA)
        self.colB = listBox(mainArea,label='From Dataset B Merge On Column:', callback = self.setcolB)

        self.sortOption = checkBox(self.bottomAreaLeft, buttons = ['Sort by Selected Column'], 
        toolTips = ['logical. Should the results be sorted on the by columns?'])
        self.bottomAreaLeft.layout().setAlignment(self.sortOption, Qt.AlignLeft)
        self.mergeOptions = radioButtons(self.bottomAreaCenter,buttons=['A+B','B+A','AB'],setChecked='A+B',
        orientation='horizontal')
        self.bottomAreaCenter.layout().setAlignment(self.mergeOptions, Qt.AlignCenter)
        self.mergeLikeThis = checkBox(self.bottomAreaRight, buttons = ['Merge on Connect'], 
        toolTips = ['Whenever this widget gets data it should try to merge as was done here'])
        button(self.bottomAreaRight, 'Commit', callback = self.run)
        
    def processA(self, data):
        #print 'processA'
        if not data:
            self.colA.update([])
            return 
        self.dataA = str(data.getData())
        self.dataParentA = data
        colsA = self.R('colnames('+self.dataA+')') #collect the sample names to make the differential matrix
        
        if type(colsA) is str:
            colsA = [colsA]
        colsA.insert(0, 'Rownames')
        self.colA.update(colsA)

        if 'Merge on Connect' in self.mergeLikeThis.getChecked():
            self.run()
        
    def processB(self, data):
        #print 'processB'
        if not data:
            self.colB.update([])
            return 
        self.dataB = str(data.getData())
        self.dataParentB = data
        colsB = self.R('colnames('+self.dataB+')') #collect the sample names to make the differential matrix
        if type(colsB) is str:
            colsB = [colsB]
        colsB.insert(0, 'Rownames')
        self.colB.update(colsB)
                
        if 'Merge on Connect' in self.mergeLikeThis.getChecked():
            self.run()
    
    def run(self):
        if self.dataA != '' and self.dataB != '':
            h = self.R('intersect(colnames('+self.dataA+'), colnames('+self.dataB+'))')
        else: h = None
        
        # make a temp variable that is the combination of the parent frame and the cm for the parent.
        if self.mergeOptions.getChecked() =='A+B':
            options = 'all.x=T'
        elif self.mergeOptions.getChecked() =='B+A':
            options = 'all.y=T'
        else:
            options = '' #'all.y=T, all.x=T'
        if 'Sort by Selected Column' in self.sortOption.getChecked():
            options += ', sort=TRUE'
            
        if self.colAsel == None and self.colBsel == None and type(h) is str: 
            self.colA.setCurrentRow( self.R('which(colnames('+self.dataA+') == "' + h + '")-1'))
            self.colB.setCurrentRow( self.R('which(colnames('+self.dataB+') == "' + h + '")-1'))
            
            self.R(self.Rvariables['merged']+'<-merge('+self.dataA+', '+self.dataB+','+options+')')
            self.sendMe()
        elif self.colAsel and self.colBsel:
            if self.colAsel == 'Rownames': cas = '0'
            else: cas = self.colAsel
            if self.colBsel == 'Rownames': cbs = '0'
            else: cbs = self.colBsel
            
            self.R(self.Rvariables['merged']+'<-merge('+self.dataA+', '+self.dataB+', by.x='+cas+', by.y='+cbs+','+options+')')
            self.sendMe()

    def sendMe(self,kill=False):
            newDataAll = rdf.RDataFrame(data = self.Rvariables['merged'])
            newDataAll.dictAttrs = self.dataParentB.dictAttrs.copy()
            newDataAll.dictAttrs.update(self.dataParentA.dictAttrs)
            self.rSend("Merged", newDataAll)
    
    def setcolA(self):
        try:
            self.colAsel = '\''+str(self.colA.selectedItems()[0].text())+'\''
            if self.colAsel == '\'Rownames\'':
                self.colAsel = '0'
        except: return
    def setcolB(self):
        try:
            self.colBsel = '\''+str(self.colB.selectedItems()[0].text())+'\''
            if self.colBsel == '\'Rownames\'':
                self.colBsel = '0'
        except: return
    def getReportText(self, fileDir):
        return 'Data from %s was merged with data from %s using the %s column in the first table and %s in the second.\n\n' % (self.dataA, self.dataB, self.colAsel, self.colBsel)
    
