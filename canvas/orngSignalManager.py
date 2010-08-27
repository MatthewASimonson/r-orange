# Author: Gregor Leban (gregor.leban@fri.uni-lj.si) modifications by Kyle R Covington and Anup Parikh
# Description:
#    manager, that handles correct processing of widget signals
#

import sys, time, OWGUI, os, redREnviron
from orngCanvasItems import MyCanvasText
from PyQt4.QtCore import *
from PyQt4.QtGui import *
Single = 2
Multiple = 4

Default = 8
NonDefault = 16

class InputSignal:
    def __init__(self, name, signalType, handler, parameters = Single + NonDefault, oldParam = 0, forceAllow = 0):
        self.name = name
        self.type = signalType
        self.handler = handler
        self.forceAllow = forceAllow

        if type(parameters) == str: parameters = eval(parameters)   # parameters are stored as strings
        # if we have the old definition of parameters then transform them
        if parameters in [0,1]:
            self.single = parameters
            self.default = not oldParam
            return

        if not (parameters & Single or parameters & Multiple): parameters += Single
        if not (parameters & Default or parameters & NonDefault): parameters += NonDefault
        self.single = parameters & Single
        self.default = parameters & Default

class OutputSignal:
    def __init__(self, name, signalType, parameters = NonDefault, forceAllow = 0):
        self.name = name
        self.type = signalType
        self.forceAllow = forceAllow

        if type(parameters) == str: parameters = eval(parameters)
        if parameters in [0,1]: # old definition of parameters
            self.default = not parameters
            return

        if not (parameters & Default or parameters & NonDefault): parameters += NonDefault
        self.default = parameters & Default


# class that allows to process only one signal at a time
class SignalWrapper:
    def __init__(self, widget, method):
        self.widget = widget
        self.method = method

    def __call__(self, *k):
        manager = self.widget.signalManager
        if not manager:
            manager = signalManager

        manager.signalProcessingInProgress += 1
        try:
            self.method(*k)
        finally:
            manager.signalProcessingInProgress -= 1
            if not manager.signalProcessingInProgress:
                manager.processNewSignals(self.widget)



class SignalManager:
    widgets = []    # topologically sorted list of widgets
    links = {}      # dicionary. keys: widgetFrom, values: (widgetTo1, signalNameFrom1, signalNameTo1, enabled1), (widgetTo2, signalNameFrom2, signalNameTo2, enabled2)
    freezing = 0            # do we want to process new signal immediately
    signalProcessingInProgress = 0 # this is set to 1 when manager is propagating new signal values
    # loadSavedSession = False
    def __init__(self, *args):
        self.debugFile = None
        self.verbosity = 1 #orngDebugging.orngVerbosity
        self.stderr = sys.stderr
        
        self._seenExceptions = {}

    def setDebugMode(self, debugMode = 0, debugFileName = "signalManagerOutput.txt", verbosity = 1):
        self.verbosity = verbosity
        if self.debugFile:
            sys.stderr = self.stderr
            #sys.stdout = self.stdout
            self.debugFile.close()
            self.debugFile = None
        if debugMode:
            self.debugFile = open(debugFileName, "wt", 0)
            sys.excepthook = self.exceptionHandler
            sys.stderr = self.debugFile
            #sys.stdout = self.debugFile
    # ----------------------------------------------------------
    # ----------------------------------------------------------
    # DEBUGGING FUNCTION
    def closeDebugFile(self):
        if self.debugFile:
            self.debugFile.close()
            self.debugFile = None
        sys.stderr = self.stderr
        #sys.stdout = self.stdout

    def addEvent(self, strValue, object = None, eventVerbosity = 1):
        if not self.debugFile: return
        if self.verbosity < eventVerbosity: return

        self.debugFile.write(str(strValue))
        # if isinstance(object, orange.ExampleTable):
            # name = " " + getattr(object, "name", "")
            # self.debugFile.write(". Token type = ExampleTable" + name + ". len = " + str(len(object)))
        if type(object) == list:
            self.debugFile.write(". Token type = %s. Value = %s" % (str(type(object)), str(object[:10])))
        elif object != None:
            self.debugFile.write(". Token type = %s. Value = %s" % (str(type(object)), str(object)[:100]))
        self.debugFile.write("\n")
        self.debugFile.flush()
    def exceptionSeen(self, type, value, tracebackInfo):
        import traceback, os
        shortEStr = "".join(traceback.format_exception(type, value, tracebackInfo))[-2:]
        return self._seenExceptions.has_key(shortEStr)
    def exceptionHandler(self, type, value, tracebackInfo):
        import traceback, os
        if not self.debugFile: return

        # every exception show only once
        shortEStr = "".join(traceback.format_exception(type, value, tracebackInfo))[-2:]
        if self._seenExceptions.has_key(shortEStr): return
        self._seenExceptions[shortEStr] = 1
        
        list = traceback.extract_tb(tracebackInfo, 10)
        space = "\t"
        totalSpace = space
        self.debugFile.write("Unhandled exception of type %s\n" % ( str(type)))
        self.debugFile.write("Traceback:\n")

        for i, (file, line, funct, code) in enumerate(list):
            if not code: continue
            self.debugFile.write(totalSpace + "File: " + os.path.split(file)[1] + " in line %4d\n" %(line))
            self.debugFile.write(totalSpace + "Function name: %s\n" % (funct))
            self.debugFile.write(totalSpace + "Code: " + code + "\n")
            totalSpace += space

        self.debugFile.write(totalSpace[:-1] + "Exception type: " + str(type) + "\n")
        self.debugFile.write(totalSpace[:-1] + "Exception value: " + str(value)+ "\n")
        self.debugFile.flush()
    # ----------------------------------------------------------
    # ----------------------------------------------------------
    # freeze/unfreeze signal processing. If freeze=1 no signal will be processed until freeze is set back to 0
    def setFreeze(self, freeze, startWidget = None):
        self.freezing = freeze
        if not freeze and self.widgets != []:
            if startWidget: self.processNewSignals(startWidget)
            else: self.processNewSignals(self.widgets[0])

    # add widget to list, ## should be removed and use the universal widget list
    def addWidget(self, widget):
        if self.verbosity >= 2:
            self.addEvent("added widget ", eventVerbosity = 2)

        if widget not in self.widgets:
            #self.widgets.insert(0, widget)
            self.widgets.append(widget)

    # remove widget from list ## should ref the universal widget list
    def removeWidget(self, widget):
        if self.verbosity >= 2:
            self.addEvent("remove widget ", eventVerbosity = 2)
        if widget in self.widgets:
            self.widgets.remove(widget)


    # send list of widgets, that send their signal to widget's signalName
    def getLinkWidgetsIn(self, widget, signalName):
        widgets = []
        for key in self.links.keys():
            links = self.links[key]
            for (widgetTo, signalFrom, signalTo, enabled) in links:
                if widget == widgetTo and signalName == signalTo: widgets.append(key)
        return widgets

    # send list of widgets, that widget "widget" sends his signal "signalName"
    def getLinkWidgetsOut(self, widget, signalName):
        widgets = []
        if not self.links.has_key(widget): return widgets
        links = self.links[widget]
        for (widgetTo, signalFrom, signalTo, enabled) in links:
            if signalName == signalFrom: widgets.append(widgetTo)
        return widgets

    # can there be a connection between the widgets (modifications by Kyle R Covington)
    def canConnect(self, widgetFrom, widgetTo):
        ## goals; to indicate if two widgets are allowed to connect.  There are a few things that we need to think about.
        """
            1) do the widgets share input types?
                a) if both single input (majority of connections) is the output of widgetFrom a child of the input of widgetTo?  If yes then allow connection.
                b) if the widgetTo has multiple input types for a single socket is the widgetFrom signal type a child of this (can use the tuple feature of isinstance.
                c) if the widgetFrom has the 'All' signal then it should send to all connections.  This rewrite will override that as we will check the class of the value that was actually sent and allow those connections (perhaps) though we should use the outputs as a guide.
        """
        if self.existsPath(widgetTo, widgetFrom): 
            print 'Circular Connection'
            return []  ## can't have circular connections so we don't worry past this if true
        ## get some info
        fromInstace = widgetFrom.instance
        toInstance = widgetTo.instance
        fromInfo = widgetFrom.widgetInfo
        toInfo = widgetTo.widgetInfo
        #print fromInstace, toInstance, fromInfo, toInfo
        ## collect the input and output signal classes (the classes not the object)
        inputs = [signal for signal in toInfo.inputs]
        outputs = [signal for signal in fromInfo.outputs]
        #print 'In/Out puts', inputs, outputs
        return toInstance.inputs.matchConnections(fromInstace.outputs)##  return a match between the inputs of one signal and the outputs of another ##self.matchConnections(outputs, inputs, fromInstace, toInstance)  ## returns a list of possible links, may be empty if no links can be found.
    def matchConnections(self, outputs, inputs, fromInstace, toInstance):  ## get the connections based on a list of outputs and inputs.
        for outS in fromInstace.outputs.getSignalIDs():  # gives the names of the output keys
            outType = fromInstace.outputs[outS]['signalClass']
            if outType == None:     #print "Unable to find signal type for signal %s. Check the definition of the widget." % (outS.name)
                continue
            for inS in toInstance.inputs.keys():
                inType = toInstance.inputs[inS]['signalClass']
                #print outType, inType
                #print issubclass(outType, inType)
                #print '######', inS.name, outS.name
                if inType == None:
                    print "Unable to find signal type for signal %s. Check the definition of the widget." % (inS.name)
                    return False
                if outType == 'All' or inType == 'All':  # if this is the special 'All' signal we need to let this pass
                    possibleLinks.append((outS.name, inS.name))
                    return True  
                    
                if type(inType) not in [list, tuple]:
                    # if issubclass(outType, inType):
                        # return True
                    # elif 'convertFromList' in dir(inType) and (outType in inType.convertFromList):
                        # return True
                    if type(outType) == type(inType):
                        return True
                    elif 'convertToList' in dir(outType) and (inType in outType.convertToList):
                        return True
                else:
                    for i in inType:
                        # if issubclass(outType, i):
                            # return True
                        # elif 
                        
                        if 'convertToList' in dir(outType) and i in outType.convertToList:
                            return True
        #print possibleLinks
        return False    
    def getConnections(self, widgetFrom, widgetTo):
        ## goals; to indicate if two widgets are allowed to connect.  There are a few things that we need to think about.
        """
            1) do the widgets share input types?
                a) if both single input (majority of connections) is the output of widgetFrom a child of the input of widgetTo?  If yes then allow connection.
                b) if the widgetTo has multiple input types for a single socket is the widgetFrom signal type a child of this (can use the tuple feature of isinstance.
                c) if the widgetFrom has the 'All' signal then it should send to all connections.  This rewrite will override that as we will check the class of the value that was actually sent and allow those connections (perhaps) though we should use the outputs as a guide.
        """
        if self.existsPath(widgetTo, widgetFrom): 
            print 'Circular Connection'
            return []  ## can't have circular connections so we don't worry past this if true
        ## get some info
        fromInstace = widgetFrom.instance
        toInstance = widgetTo.instance
        fromInfo = widgetFrom.widgetInfo
        toInfo = widgetTo.widgetInfo
        #print fromInstace, toInstance, fromInfo, toInfo
        ## collect the input and output signal classes (the classes not the object)
        inputs = [signal for signal in toInfo.inputs]
        outputs = [signal for signal in fromInfo.outputs]
        #print 'In/Out puts', inputs, outputs
        return toInstance.inputs.getPossibleConnections(fromInstace.outputs)#  returns a list of possible connections from the outInstance's outputs class.  ###self.getPossibleConnections(outputs, inputs, fromInstace, toInstance)
    def getPossibleConnections(self, outputs, inputs, fromInstace, toInstance):  ## get the connections based on a list of outputs and inputs.
        #print 'getPossibleConnections'
        if 'outputs' not in dir(fromInstace) or 'inputs' not in dir(toInstance):
            print 'Connection not possible between %s and %s' % (fromInstace.widgetID, toInstance.widgetID)
            return []  ## somehow a widget was asked to connect with no inputs or outputs and we returned false because no connections can be made.
        
        possibleLinks = []
        for outS in fromInstace.outputs.keys():  # gives the names of the output keys
            outType = fromInstace.outputs[outS]['signalClass']
            if outType == None:     #print "Unable to find signal type for signal %s. Check the definition of the widget." % (outS.name)
                continue
            for inS in toInstance.inputs.keys():
                inType = toInstance.inputs[inS]['signalClass']
                #print outType, inType
                #print issubclass(outType, inType)
                #print '######', inS.name, outS.name
                if inType == None:
                    print "Unable to find signal type for signal %s. Check the definition of the widget." % (inS.name)
                    continue
                if outType == 'All' or inType == 'All':  # if this is the special 'All' signal we need to let this pass
                    possibleLinks.append((outS, inS))
                    continue
                    
                if type(inType) not in [list, tuple]:
                    # if issubclass(outType, inType):
                        # possibleLinks.append((outS.name, inS.name))
                        #print 'Signal appended', outS.name, inS.name
                        # continue
                    if type(outType) == type(inType):
                        possibleLinks.append((outS, inS))
                        continue
                    elif 'convertToList' in dir(outType) and (inType in outType.convertToList):
                        possibleLinks.append((outS, inS))
                        continue
                    
                else:
                    for i in inType:
                        # if issubclass(outType, i):
                            
                            # possibleLinks.append((outS.name, inS.name))
                            # continue
                        if 'convertToList' in dir(outType) and i in outType.convertToList:
                            possibleLinks.append((outS, inS))
                            #print 'Signal appended', outS.name, inS.name
                            continue
        #print possibleLinks
        return possibleLinks
    def addLink(self, widgetFrom, widgetTo, signalNameFrom, signalNameTo, enabled):
        ## adds a link between two widgets.  This will also make the connection between the signalNameFrom and signalNameTo
        
        if not widgetTo.inputs.connectSignal(widgetFrom.outputs.getSignal(signalNameFrom), signalNameTo, enabled = enabled):
            return 0
        if self.links.has_key(widgetFrom.instance):  ## if the widget already has a link in the links dict
            for (widget, signalFrom, signalTo, Enabled) in self.links[widgetFrom.instance]:
                if widget == widgetTo.instance and signalNameFrom == signalFrom and signalNameTo == signalTo:
                    print "connection ", widgetFrom.instance, " to ", widgetTo.instance, " alread exists. Error!!"
                    return 0
        
        ## append to the links dict
        self.links[widgetFrom.instance] = self.links.get(widgetFrom.instance, []) + [(widgetTo.instance, signalNameFrom, signalNameTo, enabled)]

        ## let the widgets know a connection was made
        widgetTo.instance.addInputConnection(widgetFrom.instance, signalNameTo)
        widgetFrom.instance.addOutputConnection(widgetTo.instance, signalNameFrom)
        
        # if there is no key for the signalNameFrom, create it and set its id=None and data = None
        if not widgetFrom.instance.linksOut.has_key(signalNameFrom):
            widgetFrom.instance.linksOut[signalNameFrom] = {None:None}

        # if channel is enabled, send data through it
        if enabled:
            for key in widgetFrom.instance.linksOut[signalNameFrom].keys():
                widgetTo.instance.updateNewSignalData(widgetFrom.instance, signalNameTo, widgetFrom.instance.linksOut[signalNameFrom][key], key, signalNameFrom)
        return 1

    # fix position of descendants of widget so that the order of widgets in self.widgets is consistent with the schema
    def fixPositionOfDescendants(self, widget):

        for link in self.links.get(widget, []):
            widgetTo = link[0]
            self.widgets.remove(widgetTo)
            self.widgets.append(widgetTo)
            self.fixPositionOfDescendants(widgetTo)

    
    def getChildern(self,theWidget):
        children = []
        # print 'getChildern\n'*5
        # print 'theWidget', theWidget
        # print self.links.keys()
        # print self.links.get(theWidget, [])
        for (widget, signalNameFrom, signalNameTo, enabled) in self.links.get(theWidget, []):
            # print 'widget',widget
            children.append(widget)
            children.extend(self.getChildern(widget))
        return children

    def getParents(self,theWidget):
        parents = []
        for k, v in self.links.items():
            for (widget, signalNameFrom, signalNameTo, enabled) in v:
                if widget == theWidget:
                    parents.append(k)
                    parents.extend(self.getParents(k))
        return parents
         
         
    # return list of signals that are connected from widgetFrom to widgetTo
    def findSignals(self, widgetFrom, widgetTo):
        signals = []
        for (widget, signalNameFrom, signalNameTo, enabled) in self.links.get(widgetFrom, []):
            if widget == widgetTo:
                signals.append((signalNameFrom, signalNameTo))
        return signals

    # is signal from widgetFrom to widgetTo with name signalName enabled?
    def isSignalEnabled(self, widgetFrom, widgetTo, signalNameFrom, signalNameTo):
        for (widget, signalFrom, signalTo, enabled) in self.links[widgetFrom]:
            if widget == widgetTo and signalFrom == signalNameFrom and signalTo == signalNameTo:
                return enabled
        return 0

    def removeLink(self, widgetFrom, widgetTo, signalNameFrom, signalNameTo):
        if self.verbosity >= 2:
            self.addEvent("remove link", eventVerbosity = 2)
        # no need to update topology, just remove the link
        
        if self.links.has_key(widgetFrom):
            for (widget, signalFrom, signalTo, enabled) in self.links[widgetFrom]:
                if widget == widgetTo and signalFrom == signalNameFrom and signalTo == signalNameTo:
                    for key in widgetFrom.linksOut[signalFrom].keys():
                        widgetTo.updateNewSignalData(widgetFrom, signalNameTo, None, key, signalNameFrom)
                        print 'updating signal data'
                    self.links[widgetFrom].remove((widget, signalFrom, signalTo, enabled))
                    if not self.freezing and not self.signalProcessingInProgress: 
                        self.processNewSignals(widgetFrom)
                        #print 'processing signals'
        
        widgetTo.removeInputConnection(widgetFrom, signalNameTo)


    # ############################################
    # ENABLE OR DISABLE LINK CONNECTION

    def setLinkEnabled(self, widgetFrom, widgetTo, enabled, justSend = False):
        links = self.links[widgetFrom]
        for i in range(len(links)):
            (widget, nameFrom, nameTo, e) = links[i]
            if widget == widgetTo:
                if not justSend:
                    links[i] = (widget, nameFrom, nameTo, enabled)
                if enabled:
                    for key in widgetFrom.linksOut[nameFrom].keys():
                        widgetTo.updateNewSignalData(widgetFrom, nameTo, widgetFrom.linksOut[nameFrom][key], key, nameFrom)

        if enabled: self.processNewSignals(widgetTo)


    def getLinkEnabled(self, widgetFrom, widgetTo):
        for (widget, nameFrom, nameTo, enabled) in self.links[widgetFrom]:      # it is enough that we find one signal connected from widgetFrom to widgetTo
            if widget == widgetTo:                                  # that we know wheather the whole link (all signals) is enabled or not
                return enabled


    # widget widgetFrom sends signal with name signalName and value value
    def send(self, widgetFrom, signalNameFrom, value, id):
        # add all target widgets new value and mark them as dirty
        # if not freezed -> process dirty widgets
        if self.verbosity >= 2:
            self.addEvent("send data", value, eventVerbosity = 2)
        #print 'Load saved session is set to '+str(self.loadSavedSession)

        if not self.links.has_key(widgetFrom): return
        for (widgetTo, signalFrom, signalTo, enabled) in self.links[widgetFrom]:
            if signalFrom == signalNameFrom and enabled == 1:
                #print "signal from ", widgetFrom, " to ", widgetTo, " signal: ", signalNameFrom, " value: ", value, " id: ", id
                widgetTo.updateNewSignalData(widgetFrom, signalTo, value, id, signalNameFrom)
                print 'freezing: %s, signal processing in progress:%s' % (self.freezing, self.signalProcessingInProgress)
                


        if not self.freezing and not self.signalProcessingInProgress:
            #print "processing new signals"
            self.processNewSignals(widgetFrom)

    # when a new link is created, we have to
    def sendOnNewLink(self, widgetFrom, widgetTo, signals):
        for (outName, inName) in signals:
            for key in widgetFrom.linksOut[outName].keys():
                widgetTo.updateNewSignalData(widgetFrom, inName, widgetFrom.linksOut[outName][key], key, outName)


    def setNeedAttention(self,firstWidget) :
        #index = self.widgets.index(firstWidget)
        # print 'setNeedAttention\n'*5
        # print 'firstWidget', firstWidget
        children = self.getChildern(firstWidget)
        children.append(firstWidget)
        # print children
        #for i in range(index, len(self.widgets)):
        for i in children:
            # print 'propagating', i.windowTitle(), i#, index
            if i.outputs != None and len(i.outputs) !=0 and not i.loadSavedSession:
                i.setInformation(id = 'attention', text = 'Widget needs attention.')
    
    
    def processNewSignals(self, firstWidget):
        print 'processNewSignals'
        if len(self.widgets) == 0: 
            print 'No widgets', self.widgets
            return
        if self.signalProcessingInProgress: 
            print 'processing in progress'
            return

        if firstWidget not in self.widgets:
            firstWidget = self.widgets[0]   # if some window that is not a widget started some processing we have to process new signals from the first widget
        
        # start propagating
        self.signalProcessingInProgress = 1
        
        # index = self.widgets.index(firstWidget)
        print 'self.getParents', self.getParents(firstWidget)
        children = self.getChildern(firstWidget)
        children.append(firstWidget)

        print 'children', children
        for i in children:
            if i.needProcessing:
                print 'needs processing', i
                try:
                    i.processSignals()  ## call process signals in the widgetSignals function.
                except:
                    type, val, traceback = sys.exc_info()
                    sys.excepthook(type, val, traceback)  # we pretend that we handled the exception, so that it doesn't crash canvas

        # we finished propagating
        self.signalProcessingInProgress = 0


    def existsPath(self, widgetFrom, widgetTo):
        # is there a direct link
        if not self.links.has_key(widgetFrom): return 0

        for (widget, signalFrom, signalTo, enabled) in self.links[widgetFrom]:
            if widget == widgetTo: return 1

        # is there a nondirect link
        for (widget, signalFrom, signalTo, enabled) in self.links[widgetFrom]:
            if self.existsPath(widget, widgetTo): return 1

        # there is no link...
        return 0
    def refresh(self):
        for widget in self.widgets:
            widget.refresh()

# create a global instance of signal manager
globalSignalManager = SignalManager()


# #######################################
# # Signal dialog - let the user select active signals between two widgets, this is called when the connections are ambiguous.
# #######################################
class SignalDialog(QDialog):
    def __init__(self, canvasDlg, *args):
        #apply(QDialog.__init__,(self,) + args)
        QDialog.__init__(self,canvasDlg)
        self.canvasDlg = canvasDlg

        self.signals = []
        self._links = []
        self.allSignalsTaken = 0

        # GUI    ### canvas dialog that is shown when there are multiple possible connections.
        self.setWindowTitle('Connect Signals')
        self.setLayout(QVBoxLayout())

        self.canvasGroup = OWGUI.widgetBox(self, 1)
        self.canvas = QGraphicsScene(0,0,1000,1000)
        self.canvasView = SignalCanvasView(self, self.canvasDlg, self.canvas, self.canvasGroup)
        self.canvasGroup.layout().addWidget(self.canvasView)

        buttons = OWGUI.widgetBox(self, orientation = "horizontal", sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.buttonHelp = OWGUI.button(buttons, self, "&Help")
        buttons.layout().addStretch(1)
        self.buttonClearAll = OWGUI.button(buttons, self, "Clear &All", callback = self.clearAll)
        self.buttonOk = OWGUI.button(buttons, self, "&OK", callback = self.accept)
        self.buttonOk.setAutoDefault(1)
        self.buttonOk.setDefault(1)
        self.buttonCancel = OWGUI.button(buttons, self, "&Cancel", callback = self.reject)

    def clearAll(self):
        while self._links != []:
            self.removeLink(self._links[0][0], self._links[0][1])

    def setOutInWidgets(self, outWidget, inWidget):
        self.outWidget = outWidget
        self.inWidget = inWidget
        (width, height) = self.canvasView.addSignalList(outWidget, inWidget)
        self.canvas.setSceneRect(0, 0, width, height)
        self.resize(width+50, height+80)
        
        ## process the signals so that active connections are show.
        links = outWidget.instance.outputs.getSignalLinks(inWidget.instance)
        for (outName, inName) in links:
            self.addLink(outName, inName)
        print 'Output Handler Returned the following links', links

    def countCompatibleConnections(self, outputs, inputs, outInstance, inInstance, outType, inType):
        count = 0
        for outS in outputs:
            if outInstance.getOutputType(outS.name) == None: continue  # ignore if some signals don't exist any more, since we will report error somewhere else
            if outInstance.getOutputType(outS.name) == 'All': pass
            elif not issubclass(outInstance.getOutputType(outS.name), outType): continue
            for inS in inputs:
                if inInstance.getOutputType(inS.name) == None: continue  # ignore if some signals don't exist any more, since we will report error somewhere else
                if inInstance.getOutputType(inS.name) == 'All': 
                    count += 1
                    continue
                if type(inInstance.getOutputType(inS.name)) not in [list]:
                    if not issubclass(inType, inInstance.getInputType(inS.name)): continue
                    if issubclass(outInstance.getOutputType(outS.name), inInstance.getInputType(inS.name)): count+= 1
                else:
                    for i in type(inInstance.getOutputType(inS.name)):
                        if not issubclass(inType, i): continue
                        if issubclass(outInstance.getOutputType(outS.name), i): count+= 1
        return count

    def addLink(self, outName, inName):
        if (outName, inName) in self._links: return 1
        print outName, inName, 'Names'
        # check if correct types
        outType = self.outWidget.instance.outputs.getSignal(outName)['signalClass']
        inType = self.inWidget.instance.inputs.getSignal(inName)['signalClass']
        if not outType or not inType:
            raise Exception, 'None sent as signal type'
            
            
        if not self.inWidget.instance.inputs.doesSignalMatch(inName, outType): return 0
        inSignal = None
        inputs = self.inWidget.instance.inputs.getAllInputs()
        for id, signal in inputs.items():
            if id == inName: inSignal = id

        # if inName is a single signal and connection already exists -> delete it
        for (outN, inN) in self._links:
            if inN == inName and inSignal.single:
                self.removeLink(outN, inN)

        self._links.append((outName, inName))
        self.canvasView.addLink(outName, inName)
        return 1


    def removeLink(self, outName, inName): #removes from the list of instances
        res = QMessageBox.question(self.canvasView, 'Red-R Connections', 'Are you sure you want to remove that signal?\n\nThe downstream widget will recieve empty data.', QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.outWidget.instance.outputs.removeSignal(self.inWidget.instance.inputs.getSignal(inName), outName)
            self.canvasView.removeLink(outName, inName)

    def getLinks(self):
        return self._links
# this class is needed by signalDialog to show widgets and lines
class SignalCanvasView(QGraphicsView):
    def __init__(self, dlg, canvasDlg, *args):
        apply(QGraphicsView.__init__,(self,) + args)
        self.dlg = dlg
        self.canvasDlg = canvasDlg
        self.bMouseDown = False
        self.tempLine = None
        self.inWidget = None
        self.outWidget = None
        self.inWidgetIcon = None
        self.outWidgetIcon = None
        self.lines = []
        self.outBoxes = []
        self.inBoxes = []
        self.texts = []
        self.ensureVisible(0,0,1,1)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setRenderHint(QPainter.Antialiasing)

    def addSignalList(self, outWidget, inWidget):
        self.scene().clear()
        outputs, inputs = outWidget.instance.outputs.getAllOutputs(), inWidget.instance.inputs.getAllInputs()
        outIcon, inIcon = self.canvasDlg.getWidgetIcon(outWidget.widgetInfo), self.canvasDlg.getWidgetIcon(inWidget.widgetInfo)
        self.lines = []
        self.outBoxes = []
        self.inBoxes = []
        self.texts = []
        xSpaceBetweenWidgets = 100  # space between widgets
        xWidgetOff = 10             # offset for widget position
        yWidgetOffTop = 10          # offset for widget position
        yWidgetOffBottom = 30       # offset for widget position
        ySignalOff = 10             # space between the top of the widget and first signal
        ySignalSpace = 50           # space between two neighbouring signals
        ySignalSize = 20            # height of the signal box
        xSignalSize = 20            # width of the signal box
        xIconOff = 10
        iconSize = 48

        count = max(len(inputs), len(outputs))
        height = max ((count)*ySignalSpace, 70)

        # calculate needed sizes of boxes to show text
        maxLeft = 0
        for i in inputs.keys():
            maxLeft = max(maxLeft, self.getTextWidth("("+inputs[i]['name']+")", 1))
            maxLeft = max(maxLeft, self.getTextWidth(str([str(a).split('.')[-1] for a in inputs[i]['signalClass']])))

        maxRight = 0
        for i in outputs.keys():
            maxRight = max(maxRight, self.getTextWidth("("+outputs[i]['name']+")", 1))
            maxRight = max(maxRight, self.getTextWidth(str(outputs[i]['signalClass']).split('.')[-1]))

        width = max(maxLeft, maxRight) + 70 # we add 70 to show icons beside signal names

        # show boxes
        brush = QBrush(QColor(60,150,255))
        self.outWidget = QGraphicsRectItem(xWidgetOff, yWidgetOffTop, width, height, None, self.dlg.canvas)
        self.outWidget.setBrush(brush)
        self.outWidget.setZValue(-100)

        self.inWidget = QGraphicsRectItem(xWidgetOff + width + xSpaceBetweenWidgets, yWidgetOffTop, width, height, None, self.dlg.canvas)
        self.inWidget.setBrush(brush)
        self.inWidget.setZValue(-100)
        
        canvasPicsDir  = os.path.join(redREnviron.directoryNames['canvasDir'], "icons")
        if os.path.exists(os.path.join(canvasPicsDir, "frame.png")):
            widgetBack = QPixmap(os.path.join(canvasPicsDir, "frame.png"))
        else:
            widgetBack = outWidget.imageFrame

        # if icons -> show them
        if outIcon:
            frame = QGraphicsPixmapItem(widgetBack, None, self.dlg.canvas)
            frame.setPos(xWidgetOff + xIconOff, yWidgetOffTop + height/2.0 - frame.pixmap().width()/2.0)
            self.outWidgetIcon = QGraphicsPixmapItem(outIcon.pixmap(iconSize, iconSize), None, self.dlg.canvas)
            self.outWidgetIcon.setPos(xWidgetOff + xIconOff, yWidgetOffTop + height/2.0 - self.outWidgetIcon.pixmap().width()/2.0)
        
        if inIcon:
            frame = QGraphicsPixmapItem(widgetBack, None, self.dlg.canvas)
            frame.setPos(xWidgetOff + xSpaceBetweenWidgets + 2*width - xIconOff - frame.pixmap().width(), yWidgetOffTop + height/2.0 - frame.pixmap().width()/2.0)
            self.inWidgetIcon = QGraphicsPixmapItem(inIcon.pixmap(iconSize, iconSize), None, self.dlg.canvas)
            self.inWidgetIcon.setPos(xWidgetOff + xSpaceBetweenWidgets + 2*width - xIconOff - self.inWidgetIcon.pixmap().width(), yWidgetOffTop + height/2.0 - self.inWidgetIcon.pixmap().width()/2.0)

        # show signal boxes and text labels
        #signalSpace = (count)*ySignalSpace
        signalSpace = height
        j = 0
        for i in outputs.keys():
            y = yWidgetOffTop + ((j+1)*signalSpace)/float(len(outputs)+1)
            box = QGraphicsRectItem(xWidgetOff + width, y - ySignalSize/2.0, xSignalSize, ySignalSize, None, self.dlg.canvas)
            box.setBrush(QBrush(QColor(0,0,255)))
            box.setZValue(200)
            self.outBoxes.append((outputs[i]['name'], box, i))

            self.texts.append(MyCanvasText(self.dlg.canvas, outputs[i]['name'], xWidgetOff + width - 5, y - 7, Qt.AlignRight | Qt.AlignVCenter, bold =1, show=1))
            self.texts.append(MyCanvasText(self.dlg.canvas, str(outputs[i]['signalClass']).split('.')[-1], xWidgetOff + width - 5, y + 7, Qt.AlignRight | Qt.AlignVCenter, bold =0, show=1))
            j += 1
        j = 0
        for i in inputs.keys():
            y = yWidgetOffTop + ((j+1)*signalSpace)/float(len(inputs)+1)
            box = QGraphicsRectItem(xWidgetOff + width + xSpaceBetweenWidgets - xSignalSize, y - ySignalSize/2.0, xSignalSize, ySignalSize, None, self.dlg.canvas)
            box.setBrush(QBrush(QColor(0,0,255)))
            box.setZValue(200)
            self.inBoxes.append((inputs[i]['name'], box, i))

            self.texts.append(MyCanvasText(self.dlg.canvas, inputs[i]['name'], xWidgetOff + width + xSpaceBetweenWidgets + 5, y - 7, Qt.AlignLeft | Qt.AlignVCenter, bold =1, show=1))
            self.texts.append(MyCanvasText(self.dlg.canvas, str([str(a).split('.')[-1] for a in inputs[i]['signalClass']]), xWidgetOff + width + xSpaceBetweenWidgets + 5, y + 7, Qt.AlignLeft | Qt.AlignVCenter, bold =0, show=1))
            j += 1
        self.texts.append(MyCanvasText(self.dlg.canvas, outWidget.caption, xWidgetOff + width/2.0, yWidgetOffTop + height + 5, Qt.AlignHCenter | Qt.AlignTop, bold =1, show=1))
        self.texts.append(MyCanvasText(self.dlg.canvas, inWidget.caption, xWidgetOff + width* 1.5 + xSpaceBetweenWidgets, yWidgetOffTop + height + 5, Qt.AlignHCenter | Qt.AlignTop, bold =1, show=1))

        return (2*xWidgetOff + 2*width + xSpaceBetweenWidgets, yWidgetOffTop + height + yWidgetOffBottom)

    def getTextWidth(self, text, bold = 0):
        temp = QGraphicsSimpleTextItem(text, None, self.dlg.canvas)
        if bold:
            font = temp.font()
            font.setBold(1)
            temp.setFont(font)
        temp.hide()
        return temp.boundingRect().width()

    # ###################################################################
    # mouse button was pressed
    def mousePressEvent(self, ev):
        #print ' SignalCanvasView mousePressEvent'
        self.bMouseDown = 1
        point = self.mapToScene(ev.pos())
        activeItem = self.scene().itemAt(QPointF(ev.pos()))
        if type(activeItem) == QGraphicsRectItem and activeItem not in [self.outWidget, self.inWidget]:
            self.tempLine = QGraphicsLineItem(None, self.dlg.canvas)
            self.tempLine.setLine(point.x(), point.y(), point.x(), point.y())
            self.tempLine.setPen(QPen(QColor(0,255,0), 1))
            self.tempLine.setZValue(-300)
            
        elif type(activeItem) == QGraphicsLineItem:
            for (line, outName, inName, outBox, inBox) in self.lines:
                if line == activeItem:
                    self.dlg.removeLink(outName, inName)
                    return

    # ###################################################################
    # mouse button was released #########################################
    def mouseMoveEvent(self, ev):
        if self.tempLine:
            curr = self.mapToScene(ev.pos())
            start = self.tempLine.line().p1()
            self.tempLine.setLine(start.x(), start.y(), curr.x(), curr.y())
            self.scene().update()

    # ###################################################################
    # mouse button was released #########################################
    def mouseReleaseEvent(self, ev):
        if self.tempLine:  ## a line is on
            activeItem = self.scene().itemAt(QPointF(ev.pos()))  # what is the item at the active position??
            if type(activeItem) == QGraphicsRectItem:
                activeItem2 = self.scene().itemAt(self.tempLine.line().p1()) ## active item 2 is the item at the beginning of the line.
                if activeItem.x() < activeItem2.x(): outBox = activeItem; inBox = activeItem2
                else:                                outBox = activeItem2; inBox = activeItem
                outName = None; inName = None
                for (name, box, id) in self.outBoxes:
                    if box == outBox: outName = id
                for (name, box, id) in self.inBoxes:
                    if box == inBox: inName = id
                if outName != None and inName != None:
                    self.dlg.addLink(outName, inName)

            self.tempLine.hide()
            self.tempLine = None
            self.scene().update()


    def addLink(self, outName, inName):  ## makes the line that goes from one widget to the other on the canvas, outName and inName are the id's for the links
        print 'Adding link in the canvas', outName, inName
        outBox = None; inBox = None
        for (name, box, id) in self.outBoxes:
            if id == outName: outBox = box
        for (name, box, id) in self.inBoxes:
            if id == inName : inBox  = box
        if outBox == None or inBox == None:
            print "error adding link. Data = ", outName, inName
            return
        line = QGraphicsLineItem(None, self.dlg.canvas)
        outRect = outBox.rect()
        inRect = inBox.rect()
        line.setLine(outRect.x() + outRect.width()-2, outRect.y() + outRect.height()/2.0, inRect.x()+2, inRect.y() + inRect.height()/2.0)
        line.setPen(QPen(QColor(0,255,0), 6))
        line.setZValue(100)
        self.scene().update()
        self.lines.append((line, outName, inName, outBox, inBox))


    def removeLink(self, outName, inName):  # removes the line on the canvas
        # res = QMessageBox.question(None, 'Red-R Connections', 'Are you sure you want to remove that link?\nThe downmtream widget will recieve No data.', QMessageBox.Yes, QMessageBox.No)
        
        # if res == QMessageBox.Yes:
            # self.dlg.
        for (line, outN, inN, outBox, inBox) in self.lines:
            if outN == outName and inN == inName:
                line.hide()
                self.lines.remove((line, outN, inN, outBox, inBox))
                self.scene().update()
                return



