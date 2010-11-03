"""
<name>Heatmap</name>
<tags>Plotting</tags>
<icon>heatmap.png</icon>
"""

from OWRpy import *
from libraries.base.signalClasses.RDataFrame import RDataFrame as redRRDataFrame
from libraries.base.signalClasses.RList import RList as redRRList
import libraries.base.signalClasses.RModelFit as rmf
from libraries.base.signalClasses.RVector import RVector as redRRVector
from libraries.base.qtWidgets.checkBox import checkBox
from libraries.base.qtWidgets.comboBox import comboBox
from libraries.base.qtWidgets.button import button
from libraries.base.qtWidgets.spinBox import spinBox
from libraries.base.qtWidgets.groupBox import groupBox
from libraries.base.qtWidgets.widgetLabel import widgetLabel
from libraries.base.qtWidgets.graphicsView import graphicsView
from libraries.base.qtWidgets.radioButtons import radioButtons
from libraries.base.qtWidgets.commitButton import commitButton as redRCommitButton

class Heatmap(OWRpy):
    globalSettingsList = ['commit']
    def __init__(self, parent=None, signalManager=None):
        OWRpy.__init__(self)
        
        self.setRvariableNames(['heatsubset', 'hclust', 'heatvect'])
        self.plotOnConnect = 0
        self.plotdata = ''
        self.rowvChoice = None
        self.colvChoice = None
        
        self.inputs.addInput('id0', 'Expression Matrix', redRRDataFrame, self.processMatrix)
        self.inputs.addInput('id1', 'Classes Data', redRRVector, self.processClasses)

        #self.outputs.addOutput('id0', 'Cluster Subset List', redRRVector)
        self.outputs.addOutput('id1', 'Cluster Classes', redRRVector)

        

        
        #GUI
        infobox = groupBox(self.controlArea, label = "Options")
        
        self.commit = redRCommitButton(self.bottomAreaRight, label = "Replot", 
        callback=self.makePlot, width=200, processOnInput=True)
        
        button(infobox, label = 'Identify', callback = self.identify, width=200)
        self.groupOrHeight = radioButtons(infobox, label = 'Identify by:', buttons = ['Groups' , 'Height'], setChecked = 'Groups', orientation = 'horizontal')
        self.groupOrHeightSpin = spinBox(infobox, label = 'Identify Value:', min = 1, value = 5)
        self.startSaturation = spinBox(infobox, label = 'Starting Saturation:', min = 0, max = 100)
        self.endSaturation = spinBox(infobox, label = 'Ending Saturation:', min = 0, max = 100)
        self.endSaturation.setValue(30)
        self.colorTypeCombo = comboBox(infobox, label = 'Color Type:', 
        items = ['rainbow', 'heat.colors', 'terrain.colors', 'topo.colors', 'cm.colors'])
        #self.classesDropdown = comboBox(infobox, label = 'Classes:', toolTip = 'If classes data is connected you may select columns in the data to represent classes of your columns in the plotted data')
        
        self.rowDendrogram = checkBox(infobox, label='Dendrogram Options', displayLabel=False,
        buttons = ['Plot Row Dendrogram', 'Plot Column Dendrogram'], 
        setChecked = ['Plot Row Dendrogram', 'Plot Column Dendrogram'])
        
        self.showClasses = checkBox(infobox, label='Show Classes', displayLabel=False,
        buttons = ['Show Classes'])
        self.showClasses.setEnabled(False)
        #OWGUI.checkBox(infobox, self, )
        self.infoa = widgetLabel(infobox, label = "Nothing to report")
        self.gview1 = graphicsView(self.controlArea,label='Heatmap', displayLabel=False)
        self.gview1.image = 'heatmap1_'+self.widgetID
        self.gview2 = graphicsView(self.controlArea,label='Legend', displayLabel=False)
        self.gview2.image = 'heatmap2_'+self.widgetID
        
    def onLoadSavedSession(self):
        print 'load heatmap'
        self.processSignals()
    def processMatrix(self, data =None):
        
        if data:
            self.plotdata = data.getData()
            if data.optionalDataExists('classes'):
                self.classes = data.getOptionalData('classes')
                self.showClasses.setEnabled(True)
            else:
                self.classes = 'rep(0, length('+self.plotdata+'[1,]))'
            if self.R('class('+self.plotdata+')') == "data.frame":
                self.plotdata = 'data.matrix('+self.plotdata+')'
            self.rowvChoiceprocess()
            if not self.R('is.numeric('+self.plotdata+')'):
                self.status.setText('Data connected was not numeric')
                self.plotdata = ''
            if self.commit.processOnInput():
                self.makePlot()
        else: 
            self.plotdata = ''
    def processClasses(self, data):
        if data:
            self.classesData = data.getData()
            #self.classesDropdown.update(self.R('colnames('+data.data+')', wantType = 'list'))
            self.showClasses.setEnabled(True)
        else:
            #self.classesDropdown.clear()
            self.classesData = ''
    def makePlot(self):
        if self.plotdata == '': return
        self.status.setText("You are plotting "+self.plotdata)
        # if str(self.classesDropdown.currentText()) != '':
            # self.classes = self.classesData+'[,\''+str(self.classesDropdown.currentText()) + '\']'
        if 'Show Classes' in self.showClasses.getChecked():
            colClasses = ', ColSideColors=' + self.classesData + ''
        else:
            colClasses = ''
        colorType = str(self.colorTypeCombo.currentText())
        if colorType == 'rainbow':
            start = float(float(self.startSaturation.value())/100)
            end = float(float(self.endSaturation.value())/100)
            print start, end
            col = 'rev(rainbow(50, start = '+str(start)+', end = '+str(end)+'))'
        else:
            col = colorType+'(50)'
        if 'Plot Row Dendrogram' in self.rowDendrogram.getChecked():
            self.rowvChoice = 'NULL'
        else:
            self.rowvChoice = 'NA'
        if 'Plot Column Dendrogram' in self.rowDendrogram.getChecked():
            self.colvChoice = 'NULL'
        else:
            self.colvChoice = 'NA'
        self.gview1.plot(function = 'heatmap', query = self.plotdata+', Rowv='+self.rowvChoice+', Colv = '+self.colvChoice+', col= '+col+ colClasses+'')
        # for making the pie plot
        if colorType == 'rainbow':
            start = float(float(self.startSaturation.value())/100)
            end = float(float(self.endSaturation.value())/100)
            print start, end
            col = 'rev(rainbow(10, start = '+str(start)+', end = '+str(end)+'))'
        else:
            col = colorType+'(10)'
        #self.R('dev.new()')
        self.gview2.plot(query = 'rep(1, 10), labels = c(\'Low\', 2:9, \'High\'), col = '+col+'', function = 'pie')
        
    def rowvChoiceprocess(self):
        if self.plotdata:
            rowlen = self.R('length(rownames('+self.plotdata+'))')
            if rowlen > 1000:
                self.rowvChoice = 'NA'
            else:
                self.rowvChoice = 'NULL'
                
    def identify(self, kill = True):
        if self.plotdata == '': return
        ## needs to be rewritten for Red-R 1.85 which uses rpy3.  no interactivity with graphics.
        
        self.R(self.Rvariables['hclust']+'<-hclust(dist(t('+self.plotdata+')))')
        
        
        ## now there is a plot the user must select the number of groups or the height at which to make the slices.
        print str(self.groupOrHeight.getChecked())
        if str(self.groupOrHeight.getChecked()) == 'Groups':
            inj = 'k = ' + str(self.groupOrHeightSpin.value())
        else:
            inj = 'h = ' + str(self.groupOrHeightSpin.value())
        self.R(self.Rvariables['heatsubset']+'<-cutree('+self.Rvariables['hclust']+', '+inj+')')       
        self.gview1.plotMultiple(query = self.Rvariables['hclust']+',col = %s' % self.Rvariables['heatsubset'], layers = ['rect.hclust(%s, %s, cluster = %s, which = 1:%s, border = 2:(%s + 1))' % (self.Rvariables['hclust'], inj, self.Rvariables['heatsubset'], self.groupOrHeightSpin.value(), self.groupOrHeightSpin.value())])
        newData = redRRVector(data = 'as.vector('+self.Rvariables['heatsubset']+')', parent = self.Rvariables['heatsubset'])
        self.rSend("id1", newData)
        
        
    def getReportText(self, fileDir):
        ## print the plot to the fileDir and then send a text for an image of the plot
        if self.plotdata != '':
            self.R('png(file="'+fileDir+'/heatmap'+str(self.widgetID)+'.png")')
            if str(self.classesDropdown.currentText()) != '':
                self.classes = self.classesData+'$'+str(self.classesDropdown.currentText())
            if self.classes and ('Show Classes' in self.showClasses.getChecked()):
                colClasses = ', ColSideColors=rgb(t(col2rgb(' + self.classes + ' +2)))'
            else:
                colClasses = ''
            colorType = str(self.colorTypeCombo.currentText())
            if colorType == 'rainbow':
                start = float(float(self.startSaturation.value())/100)
                end = float(float(self.endSaturation.value())/100)
                print start, end
                col = 'rev(rainbow(50, start = '+str(start)+', end = '+str(end)+'))'
            else:
                col = colorType+'(50)'
            self.R('heatmap('+self.plotdata+', Rowv='+self.rowvChoice+', col= '+col+ colClasses+')')
            self.R('dev.off()')
            # for making the pie plot
            self.R('png(file="'+fileDir+'/pie'+str(self.widgetID)+'.png")')
            if colorType == 'rainbow':
                start = float(float(self.startSaturation.value())/100)
                end = float(float(self.endSaturation.value())/100)
                print start, end
                col = 'rev(rainbow(10, start = '+str(start)+', end = '+str(end)+'))'
            else:
                col = colorType+'(10)'
            self.R('pie(rep(1, 10), labels = c(\'Low\', 2:9, \'High\'), col = '+col+')')
            self.R('dev.off()')
            self.R('png(file="'+fileDir+'/identify'+str(self.widgetID)+'.png")')
            self.R('plot(hclust(dist(t('+self.plotdata+'))))')
            self.R('dev.off()')
            text = 'The following plot was generated in the Heatmap Widget:\n\n'
            text += '.. image:: '+fileDir+'/heatmap'+str(self.widgetID)+'.png\n     :scale: 50%%\n\n'
            #text += '<strong>Figure Heatmap:</strong> A heatmap of the incoming data.  Columns are along the X axis and rows along the right</br>'
            text += '.. image:: '+fileDir+'/pie'+str(self.widgetID)+'.png\n     :scale: 30%%\n\n'
            text += '**Intensity Chart:** Intensity levels are shown in this pie chart from low values to high.\n\n'
            text += '.. image:: '+fileDir+'/identify'+str(self.widgetID)+'.png\n   :scale: 50%%\n\n\n'
            text += '**Clustering:** A cluster dendrogram of the column data.\n\n'
        else:
            text = 'Nothing to plot from this widget'
            
        return text
