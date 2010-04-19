""" Modified by Kyle R. Covington and Anup Parikh """
import os, sys, user

def __getDirectoryNames():
    """Return a dictionary with Orange directories."""
    try:
        orangeDir = os.path.split(os.path.split(os.path.abspath(sys.argv[0]))[0])[0]
        #print orangeDir
    except:
        # import orange
        # orangeDir = os.path.split(os.path.abspath(orange.__file__))[0]
        pass

    try:
        orangeVer = orangeDir.split(os.path.sep)[-1]
    except:
        orangeVer = "orange"

    canvasDir = os.path.join(orangeDir, "OrangeCanvas")
    RDir = os.path.join(os.path.split(orangeDir)[0], "R")
    widgetDir = os.path.join(orangeDir, "OrangeWidgets")
    tagsDir = os.path.join(orangeDir, "tagsSystem")
    picsDir = os.path.join(widgetDir, "icons")
    addOnsDir = os.path.join(orangeDir, "add-ons")

    if not os.path.isdir(widgetDir) or not os.path.isdir(widgetDir):
        canvasDir = None
        widgetDir = None
    if not os.path.isdir(picsDir):
        picsDir = ""
    
    # home = user.home
    # if home[-1] == ":":
        # home += "\\"
    # if os.name == "nt":
        # applicationDir = os.path.join(home, "Application Data")
        # if not os.path.isdir(applicationDir):
            # try: os.makedirs(applicationDir)
            # except: pass
        # outputDir = os.path.join(applicationDir, orangeVer)                  # directory for saving settings and stuff
        # reportsDir = os.path.join(home, "My Documents", "Orange Reports")
    # elif sys.platform == "darwin":
        # applicationDir = os.path.join(home, "Library", "Application Support")
        # if not os.path.isdir(applicationDir):
            # try: os.makedirs(applicationDir)
            # except: pass
        # outputDir = os.path.join(applicationDir, orangeVer)
        # reportsDir = os.path.join(home, "Library/Application Support/orange/Reports")
    # else:
        # outputDir = os.path.join(home, "."+orangeVer)                  # directory for saving settings and stuff
        # reportsDir = os.path.join(home, "orange-reports")

    # orangeSettingsDir = outputDir
    # if sys.platform == "darwin":
        # bufferDir = os.path.join(home, "Library")
        # bufferDir = os.path.join(bufferDir, "Caches")
        # bufferDir = os.path.join(bufferDir, orangeVer)
    # else:
        # bufferDir = os.path.join(outputDir, "buffer")


    orangeSettingsDir = os.path.join(os.environ['APPDATA'],'red-r','settings')
        
    orangeSettingsDir = os.path.join(os.environ['APPDATA'],'red-r','settings')
    
    reportsDir = os.path.join(orangeSettingsDir, "orange-reports")
    bufferDir = os.path.join(orangeSettingsDir, "buffer")
    canvasSettingsDir = os.path.join(orangeSettingsDir, "OrangeCanvasQt4") 
    widgetSettingsDir = os.path.join(orangeSettingsDir, "widgetSettingsQt4")

    for dname in [orangeSettingsDir, bufferDir, widgetSettingsDir, canvasSettingsDir, reportsDir]:
        if dname <> None and not os.path.isdir(dname):
            try: os.makedirs(dname)        # Vista has roaming profiles that will say that this folder does not exist and will then fail to create it, because it exists...
            except: pass

    return dict([(name, vars()[name]) for name in ["orangeDir", "canvasDir", "RDir", "widgetDir", "tagsDir", "picsDir", "addOnsDir", "reportsDir", "orangeSettingsDir", "widgetSettingsDir", "canvasSettingsDir", "bufferDir"]])

def samepath(path1, path2):
    return os.path.normcase(os.path.normpath(path1)) == os.path.normcase(os.path.normpath(path2))

def addOrangeDirectoriesToPath():
    """Add orange directory paths to Python path."""
    pathsToAdd = [orangeDir]

    if canvasDir <> None:
        pathsToAdd.append(canvasDir)

    if widgetDir <> None and os.path.isdir(widgetDir):
        pathsToAdd.append(widgetDir)
        defaultWidgetsDirs = [os.path.join(widgetDir, x) for x in os.listdir(widgetDir) if os.path.isdir(os.path.join(widgetDir, x))]
        pathsToAdd.extend(defaultWidgetsDirs)

    for path in pathsToAdd:
        if os.path.isdir(path) and not any([samepath(path, x) for x in sys.path]):
            sys.path.insert(0, path)

def __readAddOnsList():
    addonsFile = os.path.join(orangeSettingsDir, "add-ons.txt")
    if os.path.isfile(addonsFile):
        return [tuple([x.strip() for x in lne.split("\t")]) for lne in file(addonsFile, "rt")]
    else:
        return []

def __writeAddOnsList(addons):
    file(os.path.join(orangeSettingsDir, "add-ons.txt"), "wt").write("\n".join(["\t".join(l) for l in addons]))

def registerAddOn(name, path, add = True):
    if os.path.isfile(path):
        path = os.path.dirname(path)
    __writeAddOnsList([x for x in __readAddOnsList() if x[0] != name and x[1] != path] + (add and [(name, path)] or []))

    addOns = __getAddOns()
    globals().update(addOns)
    addAddOnsDirectoriesToPath()

def __getAddOns():
    defaultAddOns = [(name, os.path.join(addOnsDir, name)) for name in os.listdir(addOnsDir)] if os.path.isdir(addOnsDir) else []
    registeredAddOns = __readAddOnsList()
    return {'addOns': defaultAddOns + registeredAddOns}

# def addAddOnsDirectoriesToPath():
    # for (name, path) in addOns:
        # for p in [path, os.path.join(path, "widgets"), os.path.join(path, "widgets", "prototypes")]:
            # if os.path.isdir(p) and not any([samepath(p, x) for x in sys.path]):
                # sys.path.insert(0, p)

directoryNames = __getDirectoryNames()
globals().update(directoryNames)

addOns = __getAddOns()
globals().update(addOns)

addOrangeDirectoriesToPath()
# addAddOnsDirectoriesToPath()