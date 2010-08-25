"""
<name>View Data Table</name>
<description>Shows data in a spreadsheet.</description>
<tags>View Data</tags>
<RFunctions>base:data.frame,base:matrix</RFunctions>
<icon>datatable.png</icon>
<author>Red-R Core Development Team</author>
"""

from OWRpy import *
import OWGUI, redRGUI
import math
import globalData
import libraries.base.signalClasses.RDataFrame as rdf
##############################################################################


class RDataTable(OWRpy):
    globalSettingsList = ['linkListBox','currentLinks']
    def __init__(self, parent=None, signalManager = None):
        OWRpy.__init__(self, wantGUIDialog = 1)
        
        self.inputs = [("Rectangular Data", rdf.RDataFrame, self.dataset)]
        self.outputs = []

        self.data = {}          # dict containing the table infromation
        self.showMetas = {}     # key: id, value: (True/False, columnList)
        self.showMeta = 1
        self.showAttributeLabels = 1
        self.showDistributions = 1
        self.distColorRgb = (220,220,220, 255)
        self.distColor = QColor(*self.distColorRgb)
        self.locale = QLocale()
        self.currentLinks = {}
        #R modifications
        
        self.currentData = None
        self.dataTableIndex = {}
        self.supressTabClick = False
        self.mylink = ''
        self.link = {}
        #The settings
        self.advancedOptions = redRGUI.widgetBox(self.GUIDialog)
        self.GUIDialog.layout().setAlignment(self.advancedOptions,Qt.AlignTop)
        
        
        self.infoBox = redRGUI.groupBox(self.advancedOptions, label="Data Information")
        self.infoBox.setHidden(True)

        self.rowColCount = redRGUI.widgetLabel(self.infoBox)
        #saveTab = self.tabWidgeta.createTabPage('Save Data')
        saveTab = redRGUI.groupBox(self.advancedOptions,label='Save Data',orientation='horizontal')
        #redRGUI.widgetLabel(saveTab, label="Saves the current table to a file.")
        #redRGUI.button(saveTab, label="Set File", callback = self.chooseDirectory)
        #self.fileName = redRGUI.widgetLabel(saveTab, label="")
        self.separator = redRGUI.comboBox(saveTab, label = 'Seperator:', 
        items = ['Tab', 'Space', 'Comma'], orientation = 'horizontal')
        save = redRGUI.button(saveTab, label="Save As File", callback=self.writeFile,
        toolTip = "Write the table to a text file.")
        saveTab.layout().setAlignment(save,Qt.AlignRight)

        #links:
        linksTab = redRGUI.groupBox(self.advancedOptions, 'Links to Websites')        
        self.linkListBox = redRGUI.listBox(linksTab)
        self.linkListBox.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.customLink = redRGUI.lineEdit(linksTab, label = 'Add Link:')
        b = redRGUI.button(linksTab, label = 'Add', toolTip = 'Adds a link to the link section for interactive data exploration.\nThe link must have a marker for the row information in the form\n{column number}\n\nFor example:http://www.google.com/#q={2}, would do a search Google(TM) for whatever was in column 2 of the row of the cell you clicked.\nYou can test this if you want using the example.', callback=self.addCustomLink)
        linksTab.layout().setAlignment(b,Qt.AlignRight)
        redRGUI.widgetLabel(linksTab,label ="""
Creating new links:
http://www.ncbi.nlm.nih.gov/gene/{gene_id}
- Here {gene_id} is a place holder and should be 
  the column name in your table. 
- The value in that column and selected row will 
  replace the place holder. 
          """)
        

        #The table
        self.tableBox = redRGUI.groupBox(self.controlArea, label = 'Data Table')
        self.tableBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #boxSettings = redRGUI.groupBox(self.advancedOptions, label = "Settings")

        
        # self.table = redRGUI.Rtable(self.tableBox,sortable=True,Rdata='data')
        
        self.table = redRGUI.filterTable(self.tableBox,sortable=True,
        filterable=True,selectionMode = QAbstractItemView.SingleSelection, callback=self.itemClicked)
        
        
    def dataset(self, dataset):
        """Generates a new table and puts it in the table section.  If no table is present the table section remains hidden."""
        if not dataset:
            return
        #print dataset
        self.supressTabClick = True
        #self.table.show()
        self.data = dataset.getData()
        
            
        if dataset.optionalDataExists('links'):
            linksData = dataset.getOptionalData('links')['data']
            self.linksListBox.update(linksData.keys())
            self.currentLinks.update(linksData)
        
        #self.currentData = dataset.getData()
        dim = dataset.getDims_data()#self.R('dim(' + dataset['data'] + ')')
        self.rowColCount.setText('# Row: ' + str(dim[0]) + "\n# Columns: " + str(dim[1]))
        self.infoBox.setHidden(False)
        self.table.setRTable(self.data)

        self.supressTabClick = False
            
    def itemClicked(self, val):
        print 'item clicked'
        print self.data
        RclickedRow = int(val.row())+1
        
        for item in self.linkListBox.selectedItems():
            #print item.text()
            #print str(self.currentLinks)
            url = self.currentLinks[str(item.text())]
            col = url[url.find('{')+1:url.find('}')]
            print 'col', col, type(col)
            if col == 0 or col == 'row': #special cases for looking into rownames
                #cellVal = self.data.getData()['row_names'][val.row()]  
                cellVal = self.R('rownames('+self.data+')['+str(RclickedRow)+']')
            else:
                
                #cellVal = self.data.getData()[col][val.row()]  
                cellVal = self.R(self.data+'['+str(RclickedRow)+',"'+col+'"]')
            url = url.replace('{'+col+'}', str(cellVal))
            #print url
            import webbrowser
            webbrowser.open_new_tab(url)

    def addCustomLink(self):
        url = str(self.customLink.text())
        self.linkListBox.addItem(url)
        self.currentLinks[url] = url
        self.customLink.clear()
        self.saveGlobalSettings()
        
    def writeFile(self):
        
        if not self.data: 
            self.status.setText('Data does not exist.')
            return
        name = QFileDialog.getSaveFileName(self, "Save File", os.path.abspath('/'),
        "Text file (*.txt *.csv *.tab);; All Files (*.*)")
        if name.isEmpty(): return

        if self.separator.currentText() == 'Tab': #'tab'
            sep = '\t'
        elif self.separator.currentText() == 'Space':
            sep = ' '
        elif self.separator.currentText() == 'Comma':
            sep = ','
        #use the R function if the parent of the dict is an R object.
        if isinstance(self.data.getDataParent(), rdf.RDataFrame):  
            self.R('write.table('+self.data.getDataParent().getData()+',file="'+str(name)+'", quote = FALSE, sep="'+sep+'")')
        elif isinstance(self.data, rdf.RDataFrame):
            self.R('write.table('+self.data.getData()+',file="'+str(name)+'", quote = FALSE, sep="'+sep+'")')
        else:  # We write the file ourselves
            string = ''
            for key in self.data.getData().keys():
                string += str(key)+sep
            string += '\n'
            for i in range(self.data.getItem('length')):
                for key in self.data.getData().keys():
                    string += self.data.getData()[key][i]+sep
                string += '\n'
            
            f = open(str(name), 'w')
            f.write(string)
            f.close()
            
    def changeColor(self):
        color = QColorDialog.getColor(self.distColor, self)
        if color.isValid():
            self.distColorRgb = color.getRgb()
            self.updateColor()

    def updateColor(self):
        self.distColor = QColor(*self.distColorRgb)
        w = self.colButton.width()-8
        h = self.colButton.height()-8
        pixmap = QPixmap(w, h)
        painter = QPainter()
        painter.begin(pixmap)
        painter.fillRect(0,0,w,h, QBrush(self.distColor))
        painter.end()
        self.colButton.setIcon(QIcon(pixmap))


    def RWidgetReload(self):
        print 'on load data table'
        self.processSignals()
   

       
    def getReportText(self, fileDir):
        return 'See the Red-R .rrs file or an output of the table to see the data.\n\n'

class TableItemDelegate(QItemDelegate):
    def __init__(self, widget = None, table = None):
        QItemDelegate.__init__(self, widget)
        self.table = table
        self.widget = widget

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value, ok = index.data(Qt.DisplayRole).toDouble()

        if ok:        # in case we get "?" it is not ok
            if self.widget.showDistributions:
                col = index.column()
                if col < len(self.table.dist) and self.table.dist[col]:        # meta attributes and discrete attributes don't have a key
                    dist = self.table.dist[col]
                    smallerWidth = option.rect.width() * (dist.max - value) / (dist.max-dist.min or 1)
                    painter.fillRect(option.rect.adjusted(0,0,-smallerWidth,0), self.widget.distColor)
##            text = self.widget.locale.toString(value)    # we need this to convert doubles like 1.39999999909909 into 1.4
##        else:
        text = index.data(Qt.DisplayRole).toString()
        ##text = index.data(OrangeValueRole).toString()

        self.drawDisplay(painter, option, option.rect, text)
        painter.restore()




