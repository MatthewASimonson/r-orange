"""
<name>Data Explorer</name>
<description>Shows data in a spreadsheet.  The data can be subset and passed to other widgets.</description>
<tags>Data Exploration and Visualization, Table Subsetting</tags>
<RFunctions>base:data.frame,base:matrix</RFunctions>
<icon>icons/datatable.png</icon>
<priority>1010</priority>
<author>Kyle R Covington and Anup Parikh</author>
"""

from OWRpy import *
import OWGUI, redRGUI
import OWGUIEx
import math, sip

class DataExplorer(OWRpy):
    settingsList = []
    def __init__(self, parent=None, signalManager = None):
        OWRpy.__init__(self, parent, signalManager, "Data Explorer", wantMainArea = 0)
        
        self.data = ''
        self.orriginalData = '' # a holder for data that we get from a connection
        self.currentDataTransformation = '' # holder for data transformations ex: ((data[1:5,])[,1:3])[1:2,]
        self.dataParent = {}
        
        self.currentRow = 0
        self.currentColumn = 0
        self.rowNameSelectionCriteria = ''
        self.criteriaList = []
        
        self.setRvariableNames(['dataExplorer'])
        self.loadSettings()
        self.criteriaDialogList = []
        self.inputs = [('Data Table', RvarClasses.RDataFrame, self.processData), ('Row Subset Vector', RvarClasses.RVector, self.setRowSelectVector)]
        self.outputs = [('Data Subset', RvarClasses.RDataFrame)]
        
        # a special section that sets when the shift key is heald or not 
        #self.shiftPressed = QKeyEvent(QEvent.KeyPress, Qt.Key_Shift, Qt.NoModifier)
        ######## GUI ############
        
        self.tableArea = redRGUI.widgetBox(self.controlArea)
        self.table = redRGUI.table(self.tableArea)
        redRGUI.button(self.bottomAreaRight, "Commit Subsetting", callback = self.commitSubset)
        self.dimsInfoArea = redRGUI.widgetLabel(self.bottomAreaCenter, '')
        
        ######## Row Column Dialog ########
        self.rowcolDialog = QDialog()
        self.rowcolDialog.setBaseSize(350, 500)
        self.rowcolDialog.setLayout(QVBoxLayout())
        self.rowcolDialog.setWindowTitle('Row Column Dialog')
        rowcolBoxArea = redRGUI.widgetBox(self.rowcolDialog, orientation = 'horizontal')
        rowArea = redRGUI.widgetBox(rowcolBoxArea, orientation = 'vertical')
        colArea = redRGUI.widgetBox(rowcolBoxArea, orientation = 'vertical')
        
        self.selectRowsOnAttachedButton = redRGUI.button(rowArea, "Select on Attached", callback = self.selectRowsOnAttached)
        self.selectRowsOnAttachedButton.setEnabled(False)
        
        self.rowListBox = redRGUI.listBox(rowArea)
        self.rowListBox.setSelectionMode(QAbstractItemView.MultiSelection) # set them to accept multiple selections
        self.rowListHint = OWGUIEx.lineEditHint(rowArea, None, None, callback = self.rowListCallback) # hints that will hold the data for the row and column names, these should be searchable and allow the user to pick subsets of rows and cols to show in the data.  Ideally these will be subset from either another vector of names or will be short enough that the user can type them individually into the line hint
        
        subOnSelectButton = redRGUI.button(self.rowcolDialog, "Subset on Selected", callback = self.commitCriteriaDialog)
        subOnSelectButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        clearButton = redRGUI.button(self.rowcolDialog, "Clear", callback = self.clearRowColDialogSelection)
    def clearRowColDialogSelection(self):
        items = self.rowListBox.selectedItems()
        for item in items:
            item.setSelected(False)
        self.rowNameSelectionCriteria = ''
    def showRowColumnDialog(self):
        self.rowcolDialog.show()
    def selectRowsOnAttached(self): pass
    def rowListCallback(self): 
        # select the rowname in the list
        item = self.rowListBox.findItems(str(self.rowListHint.text()), Qt.MatchExactly)[0]
        item.setSelected(True)
        self.rowListBox.scrollToItem(item, QAbstractItemView.PositionAtCenter) # scroll to the item so the user know's it has been selected
        
    def setRowSelectVector(self): pass
    def subsetOnSelected(self):
        items = self.rowListBox.selectedItems()
        cg = []
        for item in items:
            cg.append(str(item.text()))
        if len(cg) == 0: 
            self.rowNameSelectionCriteria = ''
            return
        self.rowNameSelectionCriteria = 'rownames('+self.orriginalData+') %in% c(\''+'\',\''.join(cg)+'\')'
    def processData(self, data, newData = True):
        if data:
            self.data = ''
            self.currentDataTransformation = '' # holder for data transformations ex: ((data[1:5,])[,1:3])[1:2,]
            
            self.table.hide()
            self.table = redRGUI.table(self.tableArea)
            self.data = data['data']
            self.rownames = self.R('rownames('+self.data+')')
            if type(self.rownames) == str:
                self.rownames = [self.rownames]
            self.colnames = self.R('colnames('+self.data+')')
            if type(self.colnames) == str:
                self.colnames = [self.colnames]
            #print self.data
            #print self.rownames
            #print self.colnames
            if newData == True:
                self.orriginalData = data['data']
                self.criteriaDialogList = []
                self.criteriaList = []
                self.orriginalRowNames = self.rownames
                self.orriginalColumnNames = self.colnames
                print 'Colnames are '+str(self.orriginalColumnNames)
                self.dataParent = data.copy()
                # first get some info about the table so we can put that into the current table.
                dims = self.R('dim('+self.data+')')
                self.dimsInfoArea.setText('Data Table with '+str(dims[1])+' columns, and '+str(dims[0])+'rows.')
                ##### Block to set the currentDataTransformation #######
                if (int(dims[0]) == 0) or (int(dims[1]) == 0):
                    # there aren't any dims to show so we are in trouble we should tell the user and quit
                    self.status.setText('There is a problem with your dataset, please check that it has at least one column and one row.')
                    return
                
                elif (int(dims[0]) < 500) and (int(dims[1]) < 500): # don't let the dims get too high or too low
                    self.currentDataTransformation = self.data # there isn't any transformation to apply
                elif not (int(dims[0]) < 500) and not (int(dims[1]) < 500): # they are both over 500
                    self.currentDataTransformation = self.data+'[1:500, 1:500]' # we only show the first 500 rows and cols.  This will need to be subset later and we should show the row and column names in a separate dialog
                elif not (int(dims[0]) < 500): # made it this far so there must be fewer columns than 500 but more than 500 rows
                    self.currentDataTransformation = self.data+'[1:500,]'
                elif not (int(dims[1]) < 500):
                    self.currentDataTransformation = self.data+'[,1:500]'
                    
                ######## End Block ##########
                self.rowListBox.addRItems(self.rownames)
                self.rowListHint.setItems(self.rownames)
                ### Set the dialogs for row subsetting ###
                # orriginalData_matrix = self.R('as.matrix('+self.orriginalData+')')
                # orriginalData_matrix = numpy.array(orriginalData_matrix)
                for j in range(1, len(self.colnames)+1):
                    thisClass = self.R('class('+self.orriginalData+'[,'+str(j)+'])', silent = True)
                        
                        # append the information into a series of dialogs that reside in a list, these will be searched when a button is pressed on the table.
                    print thisClass
                    if thisClass in ['character']: # we want to show the element but not add it to the criteria
                        # the jth selection criteria needs to be a character selection
                        self.criteriaDialogList.insert(j-1, {'dialog':QDialog()})
                        self.criteriaDialogList[j-1]['colname'] = self.orriginalColumnNames[j-1]
                        self.criteriaDialogList[j-1]['dialog'].hide()
                        self.criteriaDialogList[j-1]['dialog'].setLayout(QVBoxLayout())
                        self.criteriaDialogList[j-1]['dialog'].setWindowTitle(self.captionTitle+' '+self.colnames[j-1]+' Seleciton')
                        self.criteriaDialogList[j-1]['cw'] = OWGUIEx.lineEditHint(self.criteriaDialogList[j-1]['dialog'], None, None
                        #, callback = lambda i = i, j = j: self.columnLineEditHintAccepted(i, j))
                        )
                        self.criteriaDialogList[j-1]['cw'].minTextLength = 3
                        cBox = redRGUI.widgetBox(self.criteriaDialogList[j-1]['dialog'], orientation = 'horizontal')
                        lBox = redRGUI.widgetBox(self.criteriaDialogList[j-1]['dialog'], orientation = 'horizontal')
                        redRGUI.button(cBox, "&Commit", callback = lambda k = j-1: self.commitCriteriaDialog(k), tooltip = 'Commit the criteria to the table and repopulate') # commit the seleciton criteria to the criteriaList
                        self.criteriaDialogList[j-1]['add'] = redRGUI.button(cBox, "&Add", callback = lambda k = j-1, logic = '': self.insertTextCriteriaAdd(k, logic), tooltip = 'Adds the selection criteria to the dialog.\nPress Commit to commit to the table.')
                        self.criteriaDialogList[j-1]['and'] = redRGUI.button(lBox, "An&d", callback = lambda k = j-1: self.insertCriteriaAnd(k))
                        self.criteriaDialogList[j-1]['and'].setEnabled(False)
                        self.criteriaDialogList[j-1]['or'] = redRGUI.button(lBox, "&Or", callback = lambda k = j-1: self.insertCriteriaOr(k))
                        self.criteriaDialogList[j-1]['or'].setEnabled(False)
                        self.criteriaDialogList[j-1]['not'] = redRGUI.button(cBox, "&Not", callback = lambda k = j-1, logic = '!': self.insertTextCriteriaAdd(k, logic), tooltip = 'Sets the opposite of the criteria to the dialog.\nPress Commit to commit to the table.')
                        
                        redRGUI.button(cBox, "Clear", callback = lambda k = j-1: self.clearCriteriaDialog(k), tooltip = 'Clear the dialog and all of the selection contents, you must press commit\nafter this to commit the changes and repopulate the widget') # funciton for clearing the selection criteria of the dialog
                        self.criteriaDialogList[j-1]['widgetLabel'] = redRGUI.textEdit(self.criteriaDialogList[j-1]['dialog'], '')
                        self.criteriaDialogList[j-1]['criteriaCollection'] = ''
                        #cw.setItems(self.R('as.vector('+self.currentDataTransformation+'[,'+str(j-1)+'])'))
                        self.criteriaDialogList[j-1]['cw'].setItems(self.R(self.orriginalData+'[,'+str(j)+']'))
                        self.criteriaDialogList[j-1]['cw'].setToolTip('Moves to the selected text, but does not subset')
                        
                    elif thisClass in ['numeric', 'logical', 'integer']:
                        self.criteriaDialogList.insert(j-1, {'dialog':QDialog()})
                        self.criteriaDialogList[j-1]['colname'] = self.orriginalColumnNames[j-1]
                        self.criteriaDialogList[j-1]['dialog'].hide()
                        self.criteriaDialogList[j-1]['dialog'].setLayout(QVBoxLayout())
                        self.criteriaDialogList[j-1]['dialog'].setWindowTitle(self.captionTitle+' '+self.colnames[j-1]+' Seleciton')
                        self.criteriaDialogList[j-1]['cw'] = redRGUI.lineEdit(self.criteriaDialogList[j-1]['dialog'], toolTip = 'Subsets based on the criteria that you input, ex. > 50 gives rows where this column is greater than 50, == 50 gives all rows where this column is equal to 50.\nNote, you must use two equal (=) signs, ex. ==.')
                        
                        cBox = redRGUI.widgetBox(self.criteriaDialogList[j-1]['dialog'], orientation = 'horizontal')
                        lBox = redRGUI.widgetBox(self.criteriaDialogList[j-1]['dialog'], orientation = 'horizontal')
                        redRGUI.button(cBox, "&Commit"
                        , callback = lambda k = j-1: self.commitCriteriaDialog(k)
                        , tooltip = 'Commit the criteria to the table and repopulate') # commit the seleciton criteria to the criteriaList
                        
                        self.criteriaDialogList[j-1]['add'] = redRGUI.button(cBox, "&Add", callback = lambda k = j-1, logic = '': self.insertNumericCriteriaAdd(k, logic), tooltip = 'Adds the selection criteria to the dialog.\nPress Commit to commit to the table.')
                        
                        self.criteriaDialogList[j-1]['and'] = redRGUI.button(lBox, "An&d", callback = lambda k = j-1: self.insertCriteriaAnd(k))
                        self.criteriaDialogList[j-1]['and'].setEnabled(False)
                        self.criteriaDialogList[j-1]['or'] = redRGUI.button(lBox, "&Or", callback = lambda k = j-1: self.insertCriteriaOr(k))
                        self.criteriaDialogList[j-1]['or'].setEnabled(False)
                        self.criteriaDialogList[j-1]['not'] = redRGUI.button(cBox, "&Not", callback = lambda k = j-1, logic = '!': self.insertNumericCriteriaAdd(k, logic), tooltip = 'Sets the opposite of the criteria to the dialog.\nPress Commit to commit to the table.')
                        
                        redRGUI.button(cBox, "Clear", callback = lambda k = j-1: self.clearCriteriaDialog(k), tooltip = 'Clear the dialog and all of the selection contents, you must press commit\nafter this to commit the changes and repopulate the widget') # funciton for clearing the selection criteria of the dialog
                        self.criteriaDialogList[j-1]['widgetLabel'] = redRGUI.textEdit(self.criteriaDialogList[j-1]['dialog'], '')
                        #self.criteriaDialogList[j-1]['widgetLabel'].setText(oldcriteriaList[j-1])
                        self.criteriaDialogList[j-1]['criteriaCollection'] = ''
                        
                    elif thisClass in ['factor']:
                        self.criteriaDialogList.insert(j-1, {'dialog':QDialog()})               
                        self.criteriaDialogList[j-1]['colname'] = self.orriginalColumnNames[j-1]
                        self.criteriaDialogList[j-1]['dialog'].hide()
                        self.criteriaDialogList[j-1]['dialog'].setLayout(QVBoxLayout())
                        self.criteriaDialogList[j-1]['dialog'].setWindowTitle(self.captionTitle+' '+self.colnames[j-1]+' Seleciton')
                        self.criteriaDialogList[j-1]['cw'] = OWGUIEx.lineEditHint(self.criteriaDialogList[j-1]['dialog'], None, None
                        #, callback = lambda i = i, j = j: self.columnFactorCriteriaAccepted(i, j))
                        )
                        self.criteriaDialogList[j-1]['cw'].minTextLength = 3
                        self.criteriaDialogList[j-1]['cw'].setToolTip('Subsets based on the elements from a factor column.  These columns contain repeating elements such as "apple", "apple", "banana", "banana".')
                        #print self.R('levels('+self.currentDataTransformation+'[,'+str(j-1)+'])')
                        self.criteriaDialogList[j-1]['cw'].setItems(self.R('levels('+self.orriginalData+'[,'+str(j)+'])'))
                        cBox = redRGUI.widgetBox(self.criteriaDialogList[j-1]['dialog'], orientation = 'horizontal')
                        lBox = redRGUI.widgetBox(self.criteriaDialogList[j-1]['dialog'], orientation = 'horizontal')
                        redRGUI.button(cBox, "&Commit", callback = lambda k = j-1: self.commitCriteriaDialog(k), tooltip = 'Commit the criteria to the table and repopulate') # commit the seleciton criteria to the criteriaList
                        self.criteriaDialogList[j-1]['add'] = redRGUI.button(cBox, "&Add", callback = lambda k = j-1, logic = '': self.insertTextCriteriaAdd(k, logic), tooltip = 'Adds the selection criteria to the dialog.\nPress Commit to commit to the table.')
                        self.criteriaDialogList[j-1]['and'] = redRGUI.button(lBox, "An&d", callback = lambda k = j-1: self.insertCriteriaAnd(k))
                        self.criteriaDialogList[j-1]['and'].setEnabled(False)
                        self.criteriaDialogList[j-1]['or'] = redRGUI.button(lBox, "&Or", callback = lambda k = j-1: self.insertCriteriaOr(k))
                        self.criteriaDialogList[j-1]['or'].setEnabled(False)
                        self.criteriaDialogList[j-1]['not'] = redRGUI.button(cBox, "&Not", callback = lambda k = j-1, logic = '!': self.insertTextCriteriaAdd(k, logic), tooltip = 'Sets the opposite of the criteria to the dialog.\nPress Commit to commit to the table.')
                        
                        redRGUI.button(cBox, "Clear", callback = lambda k = j-1: self.clearCriteriaDialog(k), tooltip = 'Clear the dialog and all of the selection contents, you must press commit\nafter this to commit the changes and repopulate the widget') # funciton for clearing the selection criteria of the dialog
                        self.criteriaDialogList[j-1]['widgetLabel'] = redRGUI.textEdit(self.criteriaDialogList[j-1]['dialog'], '')
                        #self.criteriaDialogList[j-1]['widgetLabel'].insertHtml(oldcriteriaList[j-1])
                        self.criteriaDialogList[j-1]['criteriaCollection'] = ''
                        
            else:
                dims = self.R('dim('+self.data+')')
                self.dimsInfoArea.setText('Data Table with '+str(dims[1])+' columns, and '+str(dims[0])+'rows.')
                if int(dims[0]) > 500 and int(dims[1]) > 500:
                    self.currentDataTransformation = self.data+'[1:500, 1:500]'
                elif int(dims[0]) > 500:
                    self.currentDataTransformation = self.data+'[1:500,]'
                elif int(dims[1]) > 500:
                    self.currentDataTransformation = self.data+'[,1:500]'
                else:
                    self.currentDataTransformation = self.data
                ######## Set the table for the data ######
            self.setDataTable()
        else: # clear all of the data and move on
            self.data = ''
            self.currentDataTransformation = ''
            self.dataParent = {}
        
    def setDataTable(self):
        ### want to set the table with the data in the currentDataTransformation object
        
        # a set of recurring cellWidgets that we will use for the column settings
        #
        # get the dims to set the data
        dims = self.R('dim('+self.currentDataTransformation+')') 
        
        # set the row and column count
        self.table.setRowCount(min([int(dims[0]), 500])+2) # set up the row and column counts of the table
        self.table.setColumnCount(min([int(dims[1]), 500])+1)
        tableData = self.R('as.matrix('+self.currentDataTransformation+')') # collect all of the table data into an objec
        tableData = numpy.array(tableData) # make the conversion to a numpy object for subsetting
        #print tableData
        colClasses = []
        for i in range(0, dims[1]):
            colClasses.append(self.R('class('+self.currentDataTransformation+')', silent = True))
            
        # start to fill the table from top to bottom, left to right.
        for j in range(0, min([int(dims[1]), 500])+1):# the columns
            for i in range(0, min([int(dims[0]), 500])+2): # the rows
            
                if j == 0 and i == 0: # the data selector for the rownames
                    cb = redRGUI.button(self, "Subset Rownames", callback = self.rowcolDialog.show)
                    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
                    
                    self.table.setCellWidget(i, j, cb)
                    
                elif j == 0 and i == 1:
                    ci = QTableWidgetItem('Rownames')
                    self.table.setItem(i, j, ci)
                    
                elif j == 0 and i > 1: # the rownames
                    # we should set the text of this cell to be the rowname of the data.frame 
                    ci = QTableWidgetItem(str(self.rownames[i-2]))
                    ci.setBackgroundColor(Qt.red)
                    self.table.setItem(i, j, ci)
                     #commented out for testing
                elif j > 0 and i == 0: # setting the line edits for looking through the columns
                
                    cb = redRGUI.button(self, self.colnames[j-1]+'Criteria', width = -1, callback = lambda k = j-1: self.showDialog(k))
                    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    self.table.setCellWidget(i, j, cb)
                    
                elif j > 0 and i == 1: # set the colnames
                    ci = QTableWidgetItem(self.colnames[j-1])
                    ci.setBackgroundColor(Qt.red)
                    self.table.setItem(i, j, ci)
                elif j > 0 and i> 1:
                    if dims[0] == 1: # there is only one row
                        ci = QTableWidgetItem(str(tableData[j-1]))
                    elif dims[1] == 1:
                        ci = QTableWidgetItem(str(tableData[i-2]))
                    else:
                        ci = QTableWidgetItem(str(tableData[i-2, j-1])) # need to catch the case that there might not be multiple rows or columns
                    self.table.setItem(i, j, ci)
        self.table.resizeColumnsToContents()
    def showDialog(self, k):
        self.criteriaDialogList[k]['dialog'].show()
    def insertTextCriteriaAdd(self, k, logic):
        # clear the criteria from the lineEdit, add that criteria to the criteriaList, update the widgetLabel to reflect the current selection criteria, the criteris list tryes to do it'e best but it isn't infallable.
        cw = self.criteriaDialogList[k]['cw']
        text = str(cw.text())
        colName = str(self.table.item(1, k+1).text())
        self.criteriaDialogList[k]['criteriaCollection'] += logic+'('+self.dataParent['parent']+'[,\"'+colName+'\"] == \''+text+'\')'
        
        self.criteriaDialogList[k]['widgetLabel'].setHtml('<pre>'+self.criteriaDialogList[k]['criteriaCollection']+'</pre>')
        self.setDialogState(k, 0)
    def insertNumericCriteriaAdd(self, k, logic):
        cw = self.criteriaDialogList[k]['cw']
        text = str(cw.text())
        if '==' not in text and '>' not in text and '<' not in text:
            # the person didn't put in a logical opperation even though we asked them to
            self.status.setText('Please make a logical statement beginning with either \'==\', \'>\', or \'<\'')
            return
        colName = str(self.table.item(1, k+1).text())
        self.criteriaDialogList[k]['criteriaCollection'] += logic+'('+self.dataParent['parent']+'[,\''+colName+'\']'+text+')'
        
        self.criteriaDialogList[k]['widgetLabel'].setHtml('<pre>'+self.criteriaDialogList[k]['criteriaCollection']+'</pre>')
        self.setDialogState(k, 0)
    def insertCriteriaAnd(self, k):
        self.criteriaDialogList[k]['criteriaCollection'] += ' & '
        
        self.criteriaDialogList[k]['widgetLabel'].setHtml('<pre>'+self.criteriaDialogList[k]['criteriaCollection']+'</pre>')
        self.setDialogState(k, 1)
    
    def insertCriteriaOr(self, k):
        self.criteriaDialogList[k]['criteriaCollection'] += ' | ' 
        
        self.criteriaDialogList[k]['widgetLabel'].setHtml('<pre>'+self.criteriaDialogList[k]['criteriaCollection']+'</pre>')
        self.setDialogState(k, 1)
        
    def clearCriteriaDialog(self, k):
        self.criteriaDialogList[k]['criteriaCollection'] = ''
        self.criteriaDialogList[k]['widgetLabel'].setHtml('<pre>'+self.criteriaDialogList[k]['criteriaCollection']+'</pre>')
        self.setDialogState(k, 1)
    def setDialogState(self, k, state):
        self.criteriaDialogList[k]['add'].setEnabled(state)
        self.criteriaDialogList[k]['and'].setEnabled(not state)
        self.criteriaDialogList[k]['or'].setEnabled(not state)
        self.criteriaDialogList[k]['not'].setEnabled(state)
    def commitCriteriaDialog(self, k = 0):
        # collect all of the criteria from the criteriaDialogList , remove those that are blank '', commit the new selection criteria   
        # collect all of the criteria
        self.subsetOnSelected()
        self.criteriaList = []
        if self.rowNameSelectionCriteria != '':
            self.criteriaList.append(self.rowNameSelectionCriteria)
        for item in self.criteriaDialogList:
            if item['criteriaCollection'] != '':
                self.criteriaList.append(item['criteriaCollection'])
                #criteria.append('!is.na('+self.orriginalData+'[,\''+item['colname']+'\'])')
        # join these together into a single call across the columns
        print self.criteriaList
        newData = {'data':self.orriginalData+'['+'&'.join(self.criteriaList)+',]'} # reprocess the table
        self.processData(newData, False)
    
    def commitSubset(self):
        # commit the table as a new data frame
        self.subsetOnSelected()
        self.criteriaList = []
        if self.rowNameSelectionCriteria != '':
            self.criteriaList.append(self.rowNameSelectionCriteria)
        for item in self.criteriaDialogList:
            if item['criteriaCollection'] != '':
                self.criteriaList.append(item['criteriaCollection'])
                #self.criteriaList.append('!is.na('+self.orriginalData+'[,\''+item['colname']+'\'])')
        # join these together into a single call across the columns
        newData = {'data':self.orriginalData+'['+'&'.join(self.criteriaList)+',]'} # reprocess the table
        print self.criteriaList
        if 'cm' in self.dataParent:
            if len(self.criteriaList) > 0:
                self.R(self.dataParent['cm']+'$'+self.Rvariables['dataExplorer']+'<-'+'&'.join(self.criteriaList))
                newData = self.dataParent.copy()
                newData['data'] = self.orriginalData+'['+self.dataParent['cm']+'$'+self.Rvariables['dataExplorer']+' == 1,]'
                self.rSend('Data Subset', newData)
            else:
                self.rSend('Data Subset', self.dataParent.copy())
            self.status.setText('Data Sent')
        else:
            if len(self.criteriaList) > 0:
                newData = self.dataParent.copy()
                newData['data'] = self.orriginalData+'['+'&'.join(self.criteriaList)+',]'
                self.rSend('Data Subset', newData)
            else:
                self.rSend('Data Subset', self.dataParent.copy())
            self.status.setText('Data Sent')
        self.sendRefresh()
    def loadCustomSettings(self,settings=None):
        # custom function for reloading the widget
        
        # process the data again
        self.processData(self.dataParent) # this sets the criteriaDialogList and the widget
       
        for i in range(0, len(self.criteriaList)):
            print 'Set Criteria '+str(i)+' to '+str(self.criteriaList[i])
            self.criteriaDialogList[i]['widgetLabel'].setHtml('<pre>'+self.criteriaList[i]+'</pre>')
            self.criteriaDialogList[i]['criteriaCollection'] = self.criteriaList[i]
        self.commitCriteriaDialog()
        print 'Previously Committed data has been displayed.'
        
    def customCloseEvent(self):
        qApp.setOverrideCursor(Qt.WaitCursor)
        for item in self.criteriaDialogList:
            item['dialog'].hide()
            item['dialog'].accept()
            item['dialog'].close()
        self.rowcolDialog.hide()
        self.rowcolDialog.accept()
        self.rowcolDialog.close()
        qApp.restoreOverrideCursor()
    def deleteWidget(self):
        self.rowcolDialog.close()