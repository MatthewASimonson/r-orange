"""Parse a .py file to extract tags to generate a widget meta file.

Tags are as follows:
~~~~~~~~~~~~~~~~~~~~

#. ``:Name:, The name of the widget``
#. ``:Icon:, The icon file for this widget.  Must appear in the icons dir.``
#. ``:Authors:, Comma delimited list of authors and contact info.  In the form: Kyle R. Covington (kyle@red-r.org), ...``
#. ``:Summary:, A brief summary of the widget.``
#. ``:Details:, A longer description of the widget.``

Several new "directives" are defined as follows:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. ``.. rrvnames::, Either a blank line, in which case the R variable names come from the .py file, or a tagged list of name descriptor pairs in the form: :name: varName :description: varName generated by a call to makeVarName.``
#. ``.. signals::, Either a blank line, in which case the signals are taken from the .py file, or a taggel list of the signal names and classes in the form: :name: Signal name :class: package.signalClass```
#. ``.. rrgui::, Either a blank line, in which case the GUI parameters are taken from the .py file, or a tagged entry of the class, label and description in the form: :class: package.qtWidget, :label: Label name, :description: This is a gui entry that should be used for something.``

"""

import re
import xml.dom.minidom
doc = None
document = None
        
    
def _getXMLDirective(string):
    """Returns an rst directive or None in the form \.\.\ (?P<directive>.*?)::"""
    match = re.search('<.*?/>', string)
    if not match: return None
    else: return match.group(0)

def _insertXMLTree(main, new):
    for n in new.childNodes:
        """Iterate over the child nodes"""
        try:
            print n.tagName
            newMain = makeNode(main, n.tagName)
            #print 'attributes', n.attributes
            if n.attributes:
                print n.attributes
                for i in range(n.attributes.length):
                    attNode = n.attributes.item(i)
                    newMain.setAttribute(attNode.name, attNode.value)
            #or att in n.
            _insertXMLTree(newMain, n)
        except AttributeError:
            """We hit a text node so we insert the text node into the xml"""
            print n.nodeValue
            addTextNode(main, n.nodeValue)
            
def _getDirectiveNodes(string):
    """Returns a tag name and value depending on if the string contains any strings of the form :(?P<tag>.*?): (?P<value>.*)(\"\"\")|$ """
    global documentation
    global doc
    match = re.search(re.compile(r'<.+?/>\s*?(?P<xmlModel><.*>)', re.DOTALL), string)
    if match:
        nstring = '<header>%s</header>' % match.groupdict()['xmlModel']
        #print nstring
        tempdoc = xml.dom.minidom.parseString(nstring)
        
        first = tempdoc.firstChild
        ## now we have to do the job of moving through the xml and making new nodes from the parent doc
        #newMain = document
        #doc.appendChild(newMain)
        new = _insertXMLTree(documentation, first)
        #print documentation.toprettyxml()
    else: return None
    
def _getRvariableNames(string):
    """Matches the names of R variables in the setRvariableNames declaration.  Returns a a list of names"""
    #print 'R Var names string %s' % string
    rvarnames = doc.createElement('RVarNames')
    
    for m in re.finditer(r'''['"](?P<name>.+?)['"]''', string):
        if m.group('name') in ['\'', '\"', '']: continue ## protect from inserting quotes
        name = doc.createElement('Name')
        rvarnames.appendChild(name)
        name.appendChild(doc.createTextNode(m.group('name')))
    #print rvarnames.toprettyxml()
    return rvarnames

def _getRRSignals(string):
    """Parses from a call to addOutput or addInput the name and class(s) of an input or output signal, returns a tuple of signaltype [input/output], name, and """
    print string
    typeMatch = re.search(re.compile(r'self\.(?P<type>.*?)s.add', re.DOTALL), string)
    if typeMatch:
        myType = doc.createElement(typeMatch.groupdict()['type'])
        ## now get the function call
        call = re.search(re.compile(r'''\(['"](?P<id>.+?)['"]\s*,.*?['"](?P<name>.*?)['"].*?,'''), string)
        print call
        if call:
            myid = doc.createElement('id')
            myType.appendChild(myid)
            myid.appendChild(doc.createTextNode(str(call.groupdict()['id'])))
            myName = doc.createElement('name')
            myType.appendChild(myName)
            myName.appendChild(doc.createTextNode(str(call.groupdict()['name'])))
            for sc in re.finditer(r'''signals\.(?P<sc>.+?)[\],\)]''', string):
                sigclass = doc.createElement('signalClass')
                myType.appendChild(sigclass)
                sigclass.appendChild(doc.createTextNode(sc.group('sc')))
            description = re.search(r'''<description>(?P<desc>.+?)</description>''', string)
            if description:
                desc = doc.createElement('description')
                myType.appendChild(desc)
                desc.appendChild(doc.createTextNode(description.groupdict()['desc']))
    #print myType.toprettyxml()
    return myType



def _getRRGUISettings(string):
    """Parses an rrgui setting and returns a tuple of class, label or None"""
    guiElement = doc.createElement('GUIElement')
    
    match = re.search(re.compile(r'''redRGUI\.(?P<class>.*?)\(.*?label *=.*['"](?P<label>.*?)['"]''', re.DOTALL), string)
    if match:
        cla = makeNode(guiElement, 'class')
        addTextNode(cla, match.group('class'))
        label = makeNode(guiElement, 'lable')
        addTextNode(label, match.group('label'))
        description = makeNode(guiElement, 'description')
        desc = re.search(r'''<description>(?P<desc>.+?)</description>''', string)
        if desc:
            addTextNode(description, desc.group('desc'))
    
    return guiElement
     
def makeNode(parent, text):
    newNode = doc.createElement(str(text))
    parent.appendChild(newNode)
    return newNode
    
def addTextNode(parent, text):
    global doc
    parent.appendChild(doc.createTextNode(str(text)))


def _parsefile(myFile, doc):
    global documentation
    documentation = doc.createElement('documentation')
    doc.appendChild(documentation)
    guiElements = makeNode(documentation, 'GUIElements')
    for m in  re.finditer(re.compile(r'(?P<spacestring>.*?)(\n\s*\n)', re.DOTALL | re.MULTILINE), myFile.replace('\r', '')):
        """ m is a spacestring so m is any set separated by a whitespace line.  Data is processed in blocks of these."""
        #print m.groupdict()
        if not re.search(re.compile(r'""".*"""', re.DOTALL), m.group()): continue #"""There are no strings to process.  Note that the docstring must be the 
        if not re.search(re.compile(r'\s*"""', re.DOTALL), m.group().split('\n')[0]): continue # """The docstring must be at the beginning of the block"""
        
        gDict = m.group()
        """if the gDict contains a directiv we should find out what the directive is and then how to handle it."""
        directive = _getXMLDirective(gDict)
        if directive != None:
            print directive
            if directive in ['<rrvnames/>', '<signals/>', '<rrgui/>', '<header/>']:  # it's one of ours!!
                """if there are other options in the docstring then they belong to this directive, we try to get them"""
                if directive == '<header/>':
                    """The header can only be xml so we just get the xml structure from the tag"""
                    headerXML = _getDirectiveNodes(gDict)
                    #print headerXML
                    if headerXML:
                        for n in headerXML.childNodes:
                            print 'node xml', n.toprettyxml()
                            documentation.appendChild(n)
                    #print '##########'
                    #print doc.toprettyxml()
                    #print '##########'
                elif directive == '<rrvnames/>':
                    """rvarnames can only be a list of names so we parse that from the string"""
                    documentation.appendChild(_getRvariableNames(gDict))
                elif directive == '<signals/>':
                    """Signals may contain a description after the signal these are parsed line by line."""
                    signals = doc.createElement('signals')
                    documentation.appendChild(signals)
                    for s in gDict.split(r'\n'):
                        signals.appendChild(_getRRSignals(s))
                elif directive == '<rrgui/>':
                    guiElements.appendChild(_getRRGUISettings(gDict))
                
        elif _getRSTTag(gDict) != None: # at least there are some tags so perhaps we can set these things if they are accepted.
            optionTags.update(_getRSTTag(gDict))
        else: continue
    #print 'optionTags: %s' % str(optionTags)
    
    #"""So now we need to put all of the data into an xml file"""
    #documentation = doc.createElement('documentation')
    #doc.appendChild(documentation)
    
    #"""The name tag"""
    #name = doc.createElement('name')
    #documentation.appendChild(name)
    #name.appendChild(doc.createTextNode(optionTags.get('Name', '')))
    #"""The icon tag"""
    #icon = doc.createElement('icon')
    #documentation.appendChild(icon)
    #icon.appendChild(doc.createTextNode(optionTags.get('Icon', '')))
    #"""The summary tag"""
    #summary = doc.createElement('summary')
    #documentation.appendChild(summary)
    #summary.appendChild(doc.createTextNode(optionTags.get('Summary', '')))
    #"""The details tag"""
    #details = doc.createElement('details')
    #documentation.appendChild(details)
    #details.appendChild(doc.createTextNode(optionTags.get('Details', '')))
    #"""The tags tag"""
    #tags = doc.createElement('tags')
    #documentation.appendChild(tags)
    #for t in [s.strip() for s in optionTags.get('Tags', '').split(',')]:
        #tag = doc.createElement('tag')
        #tags.appendChild(tag)
        #tag.appendChild(doc.createTextNode(t))
    #"""The signals tag"""
    #sig = doc.createElement('signals')
    #documentation.appendChild(sig)
    #for s in [si for si in signals if si != None]:
        #if s.get('type', None) == 'input':
            #input = doc.createElement('input')
            #sig.appendChild(input)
            #signalClass = doc.createElement('signalClass')
            #input.appendChild(signalClass)
            #signalClass.appendChild(doc.createTextNode(s.get('class', '')))
            #name = doc.createElement('name')
            #input.appendChild(name)
            #name.appendChild(doc.createTextNode(s.get('name', '')))
            #description = doc.createElement('description')
            #input.appendChild(description)
            #description.appendChild(doc.createTextNode(s.get('description', '')))
        #elif s.get('type', None) == 'output':
            #output = doc.createElement('output')
            #sig.appendChild(output)
            #signalClass = doc.createElement('signalClass')
            #output.appendChild(signalClass)
            #signalClass.appendChild(doc.createTextNode(s.get('class', '')))
            #name = doc.createElement('name')
            #output.appendChild(name)
            #name.appendChild(doc.createTextNode(s.get('name', '')))
            #description = doc.createElement('description')
            #output.appendChild(description)
            #description.appendChild(doc.createTextNode(s.get('description', '')))
    #"""The GUIElements tag"""
    #GUIElements = doc.createElement('GUIElements')
    #documentation.appendChild(GUIElements)
    #for g in [g for g in rrgui if g != None]:
        #print g
        #display = doc.createElement('display')
        #GUIElements.appendChild(display)
        #name = doc.createElement('name')
        #display.appendChild(name)
        #name.appendChild(doc.createTextNode(g.get('label', '')))
        #cla = doc.createElement('class')
        #display.appendChild(cla)
        #cla.appendChild(doc.createTextNode(g.get('class', '')))
        #description = doc.createElement('description')
        #display.appendChild(description)
        #description.appendChild(doc.createTextNode(g.get('description', '')))
    #"""The citation tag"""
    #citation = doc.createElement('citation')
    #documentation.appendChild(citation)
    #author = doc.createElement('author')
    #citation.appendChild(author)
    #author.appendChild(doc.createTextNode(optionTags.get('Author', '')))
    
    #print 'The document'
    #print doc.toprettyxml()
    
def parseFile(filename, output):
    """Reads a file and parses out the relevant widget xml settings, writes to the file output an xml document representing the parsed data.  Prints success message on success."""
    global doc
    fileStrings = []
    with open(filename, 'r') as f:
        myFile = f.read()

    """Pass the list of strings to the parser to extract the relevant structure"""
    import xml.dom.minidom
    doc = xml.dom.minidom.Document()
    _parsefile(myFile, doc)
    with open(output, 'w') as f:
        f.write(doc.toprettyxml())
    print 'Success for %s' % filename
    
def test(path):
    parseFile(path, 'output.xml')
    
import sys
test(sys.argv[1])