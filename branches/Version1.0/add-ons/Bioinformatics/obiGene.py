import os
import obiTaxonomy
import orngServerFiles

import time

default_database_path = orngServerFiles.localpath("NCBI_geneinfo")

class GeneInfo(object):
    """ An object representing the NCBI information for a gene.
    """

    NCBI_GENEINFO_TAGS = ("tax_id", "gene_id", "symbol", "locus_tag", "synonyms",
                          "dbXrefs", "chromosome", "map_location", "description", "type",
                          "symbol_from_nomenclature_authority", "full_name_from_nomenclature_authority",
                          "nomenclature_status", "other_designations", "modification_date")
    NCBI_MULTIPLE_CARDINALITY_TAGS = ("synonyms", "dbXrefs", "other_designations")
    
    __slots__ = NCBI_GENEINFO_TAGS
    def __init__(self, line):
        """ Construct the GeneInfo object from a line in the NCBI gene_info file
        """
        line = line.split("\t")
        for attr, value in zip(self.__slots__, line):
            if value == "-":
                value = None
            if attr in GeneInfo.NCBI_MULTIPLE_CARDINALITY_TAGS:
                value = value.split("|") if value != None else []
            setattr(self, attr, value)

    def __repr__(self):
        def format(value):
            if not value:
                return "-"
            elif type(value) == list:
                return "|".join(value)
            else:
                return value
        return "\t".join(format(getattr(self, slot)) for slot in self.__slots__)

    def __str__(self):
        return repr(self)

class NCBIGeneInfo(dict):
    
    _object_cache = {}    
    def __init__(self, organism, genematcher=None):
        """ An dictionary like object for accessing NCBI gene info
        Arguments::
                - *organism*    Organism id

        Example::
            >>> info = NCBIGeneInfo("Homo sapiens")
        """
        
        self.taxid = self.organism_name_search(organism)


        fname = orngServerFiles.localpath_download("NCBI_geneinfo", "gene_info.%s.db" % self.taxid)
        file = open(fname, "rb")
        self.update(dict([(line.split("\t", 3)[1], line) for line in file.read().split("\n") if line.strip() and not line.startswith("#")]))

        # following is a temporary fix before gene name matcher is complete (then, this code is to be replaced)
        # translate is a dictionary from aliases to target name (target names are real ids)a

        """
        self.translate = dict([(self[k].symbol, k) for k in self.keys()])
        for k in self.keys():
            self.translate.update([(s, k) for s in self[k].synonyms if s not in self.translate] + \
                                  ([(self[k].locus_tag, k)] if self[k].locus_tag else [] ))

        """

        # NOTE orig init time for gene matcher: 2.5s, new 4s: investigate the slowdown
        # NOTE matches are not the same because aliases are build a bit
        # differently (main name versus old aliases conflict!)

        self.matcher = genematcher
        if self.matcher == None:
            if self.taxid == '352472':
                self.matcher = matcher([[GMNCBI(self.taxid), GMDicty()]])
            else:
                self.matcher = matcher([GMNCBI(self.taxid)])

        #if this is done with a gene matcher, pool target names
        self.matcher.set_targets(self.keys())

    @classmethod
    def organism_version(cls, name):
        oname = cls.organism_name_search(name)
        #FIXME, dirty hack to ensure file id downloaded
        orngServerFiles.localpath_download("NCBI_geneinfo", "gene_info.%s.db" % oname) 
        return orngServerFiles.info("NCBI_geneinfo", "gene_info.%s.db" % oname)["datetime"]

    @classmethod
    def organism_name_search(cls, org):
        taxids = obiTaxonomy.to_taxid(org, mapTo=[obiTaxonomy.common_taxids()])
        if not taxids:
            taxids = set(obiTaxonomy.common_taxids()).intersection(obiTaxonomy.search(org, onlySpecies=False)) #onlySpecies=False needed to find correct dicty
        if len(taxids) == 0:
            raise obiTaxonomy.UnknownSpeciesIdentifier, org
        elif len(taxids) > 1:
            raise obiTaxonomy.MultipleSpeciesException, ", ".join(["%s: %s" % (id, obiTaxonomy.name(id)) for id in taxids])
        return taxids.pop()

    @classmethod    
    def load(cls, file):
        """ A class method that loads gene info from file
        """
        if type(file) in [str, unicode]:
            file = open(file, "rb")
        return cls((line.split("\t", 3)[1], line) for line in file.read().split("\n") if line.strip() and not line.startswith("#"))
        
    def get_info(self, gene_id, def_=None):
        """ Search and return the GeneInfo object for gene_id
        """
        try:
            return self(gene_id)
        except KeyError:
            return def_
        
    def __call__(self, name):
        """ Search and return the GeneInfo object for gene_id
        """
        #id = self.translate.get(name, name)
        #print self.matcher.umatch(name), self.matcher.match(name)
        id = self.matcher.umatch(name)
        return self[id]

    def __getitem__(self, key):
#        return self.get(gene_id, self.matcher[gene_id])
        return GeneInfo(dict.__getitem__(self, key))

    def __setitem__(self, key, value):
        if type(value) == str:
            dict.__setitem__(self, key, value)
        else:
            dict.__setitem__(self, key, repr(value))

    def get(self, key, def_=None):
        try:
            return self[key]
        except KeyError:
            return def_

    def itervalues(self):
        for val in dict.itervalues(self):
            yield GeneInfo(val)

    def iteritems(self):
        for key, val in zip(self.iterkeys(), self.itervalues()):
            yield key, val

    def values(self):
        return list(self.itervalues())
    
    def items(self):
        return list(self.iteritems())

    def search(self, string, exact=False):
        pass

    @staticmethod
    def get_geneinfo_from_ncbi(file, progressCallback=None):
        import urllib2, gzip, shutil, tempfile
        from cStringIO import StringIO
        if type(file) in [str, unicode]:
            file = open(file, "wb")
        
        stream = urllib2.urlopen("ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz")
        tmpfile = tempfile.TemporaryFile()
        shutil.copyfileobj(stream, tmpfile)
        tmpfile.seek(0)
        stream = gzip.GzipFile(None, "rb", fileobj=tmpfile)
        shutil.copyfileobj(stream, file)

"""
Gene matcher.

"Database" for each oranism is a list of sets of gene aliases.
"""

from collections import defaultdict
import os

gene_matcher_path = None

def ignore_case(gs):
    """ Transform names in sets in list to lower case """
    return [ set([a.lower() for a in g]) for g in gs ]

def create_mapping(groups, lower=False):
    """ 
    Returns mapping of aliases to the group index. If lower
    is True, lower case forms of gene aliases are mapped to indices.

    Unpickling the results of this function (binary format)
    is slower than running it.

    TIMING NOTES: 
    - lower() costs are neglible (< 10%)
    - building sets instead of lists also costs about 10 percent
    """
    togroup = defaultdict(set)

    # code duplicated because running a function in relatively expensive here.
    if lower: 
        for i,group in enumerate(groups):
            for alias in group:
                togroup[alias.lower()].add(i)
    else:
        for i,group in enumerate(groups):
            for alias in group:
                togroup[alias].add(i)

    return togroup

def join_sets(set1, set2, lower=False):
    """ 
    Joins two sets of gene set mappings. If lower is True, lower case
    forms of gene aliases are compared.

    A group g1 from set1 is joined to a group of aliases g2 from set2, 
    if the groups share at least one gene. 
    Returns all joined groups and groups that were not matched, which 
    remain unchanged.

    The operation both commutative and associative.
    """

    cur = [ set(a) for a in set1 ]
    currentmap = create_mapping(cur, lower=lower)

    new = [] #new groups

    #remember used to find unused
    set1used = set() 
    set2used = set()

    fn = lambda x: x
    if lower:
        fn = lambda x: x.lower()

    for i, group in enumerate(set2):

        #find groups of aliases (from set1)  intersecting with a current
        #group from set2
        cross = reduce(set.union, 
            [ currentmap[fn(alias)] for alias in group if fn(alias) in currentmap], set())

        for c in cross:
            #print c, group & set1[c], group, set1[c]
            set1used.add(c)
            set2used.add(i)
            new.append(group | set1[c]) #add a union

    #add groups without matches (from both sets)
    set1add = set(range(len(set1))) - set1used
    set2add = set(range(len(set2))) - set2used

    for a in set1add:
        new.append(set1[a])
    for a in set2add:
        new.append(set2[a])

    return new
 
def join_sets_l(lsets, lower=False):
    """
    Joins multiple gene set mappings using join_sets function.
    """
    current = lsets[0]
    for b in lsets[1:]:
        current = join_sets(current, b, lower=lower)
    return current

class Matcher(object):
    """
    Gene matcher tries to match an input gene to some target.
    """

    def set_targets(self, targets):
        """
        Set input list of gene names as targets. 
        Abstract function.
        """
        notImplemented()

    def match(self, gene):
        """Returns a list of matching target gene names."""
        notImplemented()

    def umatch(self, gene):
        """Returns an unique (only one matching target) target or None"""
        mat = self.match(gene)
        return mat[0] if len(mat) == 1 else None

    def explain(self, gene):
        """ 
        Returns an gene matches with explanations as lists of tuples. 
        Each tuple consists of a list of target genes in a set
        of aliases matched to input gene, returned as a second part
        of the tuple.
        """
        notImplemented()

def buffer_path():
    """ Returns buffer path from Orange's setting folder if not 
    defined differently (in gene_matcher_path). """
    if  gene_matcher_path == None:
        import orngEnviron
        pth = os.path.join(orngEnviron.directoryNames["bufferDir"], 
            "gene_matcher")
        try:
            os.makedirs(pth)
        except:
            pass
        return pth
    else:
        return gene_matcher_path

def auto_pickle(filename, version, func, *args, **kwargs):
    """
    Run function func with given arguments and save the results to
    a file named filename. If results for a given filename AND
    version were already saved, just read and return them.
    """

    import cPickle as pickle

    output = None
    outputOk = False

    try:
        f = open(filename,'rb')

        try:
            versionF = pickle.load(f)
            if versionF == version:
                outputOk = True
                output = pickle.load(f)
        except:
            pass
        finally:
            f.close()

    except:
        pass

    if not outputOk:
        output = func(*args, **kwargs)

        #save output before returning
        f = open(filename,'wb')
        pickle.dump(version, f, -1)
        pickle.dump(output, f, -1)
        f.close()

    return output

class MatcherAliases(Matcher):
    """
    Genes matcher based on a list of sets of given aliases.

    Target genes belonging to same sets of aliases as the input gene are 
    returned as matching genes.

    """
    def __init__(self, aliases, ignore_case=True):
        self.aliases = aliases
        self.ignore_case = ignore_case
        self.mdict = create_mapping(self.aliases, self.ignore_case)

    def to_ids(self, gene):
        """ Return ids of sets of aliases the gene belongs to. """
        if self.ignore_case:
            gene = gene.lower()
        return self.mdict[gene]

    def set_targets(self, targets):
        """
        A reverse dictionary is made accordint to each target's membership
        in the sets of aliases.
        """
        d = defaultdict(list)
        for target in targets:
            ids = self.to_ids(target)
            if ids != None:
                for id in ids:
                    d[id].append(target)
        self.to_targets = d

    def match(self, gene):
        """
        Input gene is first mapped to ids of sets of aliases which contain
        it. Target genes belonding to the same sets of aliases are returned
        as input's match.
        """
        inputgeneids = self.to_ids(gene)
        #return target genes with same ids
        return list(set( \
            reduce(lambda x,y:x+y, 
                [ self.to_targets[igid] for igid in inputgeneids ], [])))

    def explain(self, gene):
        inputgeneids = self.to_ids(gene)
        return [ (self.to_targets[igid], self.aliases[igid]) for igid in inputgeneids ]

class MatcherAliasesPickled(MatcherAliases):
    """
    Gene matchers based on sets of aliases supporting pickling should
    extend this class. Subclasses must define functions "filename", 
    "create_aliases_version" and "create_aliases". Those are crucial for
    pickling of gene aliases to work.

    Loading of gene aliases is done lazily: they are loaded when they are
    needed. Loading of aliases for components of joined matchers is often 
    unnecessary and is therefore avoided. 
    """
    
    def set_aliases(self, aliases):
        self.saved_aliases = aliases

    def get_aliases(self):
        if not self.saved_aliases: #loads aliases if not loaded
            self.aliases = self.load_aliases()
        #print "size of aliases ", len(self.saved_aliases)
        return self.saved_aliases

    aliases = property(get_aliases, set_aliases)

    def get_mdict(self):
        """ Creates mdict. Aliases are loaded if needed. """
        if not self.saved_mdict:
            self.saved_mdict = create_mapping(self.aliases, self.ignore_case)
        return self.saved_mdict

    def set_mdict(self, mdict):
        self.saved_mdict = mdict

    mdict = property(get_mdict, set_mdict)

    def set_targets(self, targets):
        MatcherAliases.set_targets(self, targets)

    def filename(self):
        """ Returns file name for saving aliases. """
        notImplemented()
        
    def create_aliases_version(self):
        """ Returns version of the source database state. """
        notImplemented()

    def create_aliases(self):
        """ Returns gene aliases. """
        notImplemented()

    def load_aliases(self):
        fn = self.filename()
        ver = self.create_aliases_version()
        if fn != None and ver != None: 
            filename = os.path.join(buffer_path(), fn)
            return auto_pickle(filename, ver, self.create_aliases)
        else:
            #if either file version of version is None, do not pickle
            return self.create_aliases()

    def __init__(self, ignore_case=True):
        self.aliases = []
        self.mdict = {}
        self.ignore_case = ignore_case
        self.filename() # test if valid filename can be built

class MatcherAliasesKEGG(MatcherAliasesPickled):

    def _organism_name(self, organism):
        import obiKEGG 
        return obiKEGG.organism_name_search(organism)

    def create_aliases(self):
        organism = self._organism_name(self.organism)
        import obiKEGG
        org = obiKEGG.KEGGOrganism(self.organism, genematcher=GMDirect())
        genes = org.genes
        osets = [ set([name]) | set(b.alt_names) for 
                name,b in genes.items() ]
        return osets

    def create_aliases_version(self):
        import obiKEGG
        obiKEGG.KEGGOrganism.organism_version(self.organism)

    def filename(self):
        return "kegg_" + self._organism_name(self.organism) 

    def __init__(self, organism, ignore_case=True):
        self.organism = organism
        MatcherAliasesPickled.__init__(self, ignore_case=ignore_case)

class MatcherAliasesGO(MatcherAliasesPickled):

    def _organism_name(self, organism):
        """ Returns internal GO organism name. Used to define file name. """
        import obiGO
        return obiGO.organism_name_search(self.organism)

    def create_aliases(self):
        import obiGO
        annotations = obiGO.Annotations(self.organism, genematcher=GMDirect())
        names = annotations.geneNamesDict
        return map(set, list(set([ \
            tuple(sorted(set([name]) | set(genes))) \
            for name,genes in names.items() ])))

    def filename(self):
        return "go_" + self._organism_name(self.organism)

    def create_aliases_version(self):
        import obiGO
        return "v2." + obiGO.Annotations.organism_version(self.organism)

    def __init__(self, organism, ignore_case=True):
        self.organism = organism
        MatcherAliasesPickled.__init__(self, ignore_case=ignore_case)

class MatcherAliasesDictyBase(MatcherAliasesPickled):

    def create_aliases(self):
        import obiDicty
        db = obiDicty.DictyBase()
        #db.info, db.mappings
        infoa = [ set([id,name]) | set(aliases) for id,(name,aliases,_) in db.info.items() ]
        mappingsa = [ set(filter(None, a)) for a in db.mappings ]
        joineda = join_sets(infoa, mappingsa, lower=True)
        return joineda

    def create_aliases_version(self):
        import obiDicty
        return "v1." + obiDicty.DictyBase.version()

    def filename(self):
        return "dictybase" 

    def __init__(self, ignore_case=True):
        MatcherAliasesPickled.__init__(self, ignore_case=ignore_case)

class MatcherAliasesNCBI(MatcherAliasesPickled):

    def _organism_name(self, organism):
        return NCBIGeneInfo.organism_name_search(organism)

    def create_aliases(self):
        ncbi = NCBIGeneInfo(self.organism, genematcher=GMDirect())
        out = []
        for k in ncbi.keys():
            out.append(set(filter(None, [k, ncbi[k].symbol, ncbi[k].locus_tag] + [ s for s in ncbi[k].synonyms ] )))
        return out

    def filename(self):
        return "ncbi_" + self._organism_name(self.organism)

    def create_aliases_version(self):
        return "v2." + NCBIGeneInfo.organism_version(self.organism)

    def __init__(self, organism, ignore_case=True):
        self.organism = organism
        MatcherAliasesPickled.__init__(self, ignore_case=ignore_case)

class MatcherAliasesPickledJoined(MatcherAliasesPickled):
    """
    Creates a new matcher by joining gene aliases from different data sets.
    Sets of aliases are joined if they contain common genes.

    The joined gene matcher can only be pickled if the source gene
    matchers are picklable.
    """

    def filename(self):
        # do not pickle if any is unpicklable
        try:
            filenames = [ mat.filename() for mat in self.matchers ]
            if self.ignore_case:
                filenames += [ "icj" ]
            return "__".join(filenames)
        except:
            return None

    def create_aliases(self):
        return join_sets_l([ mat.aliases for mat in self.matchers ], lower=self.ignore_case)

    def create_aliases_version(self):
        try:
            return "v4_" + "__".join([ mat.create_aliases_version() for mat in self.matchers ])
        except:
            return None

    def __init__(self, matchers):
        """ 
        Join matchers together. Groups of aliases are joined if
        they share a common name.

        If ignore_case is True, ignores case when joining gene aliases.
        """
        #FIXME: sorting of matchers to avoid multipying pickled files for
        #different orderings.
        self.matchers = matchers
        allic = set([ m.ignore_case for m in self.matchers ])
        if len(allic) > 1:
            notAllMatchersHaveEqualIgnoreCase()
        ignore_case = list(allic)[0]

        MatcherAliasesPickled.__init__(self, ignore_case=ignore_case)
        
class MatcherSequence(Matcher):
    """
    Chaining of gene matchers.
    
    User defines the order of gene matchers. Each gene is goes through
    sequence of gene matchers until a match is found.
    """
    
    def __init__(self, matchers):
        self.matchers = matchers

    def match(self, gene):
        for matcher in self.matchers:
            m = matcher.match(gene)
            if m: 
                return m
        return []

    def set_targets(self, targets):
        for matcher in self.matchers:
            matcher.set_targets(targets)

    def explain(self, gene):
        for matcher in self.matchers:
            m = matcher.match(gene)
            if m: 
                return matcher.explain(gene)
        return []

class MatcherDirect(Matcher):
    """
    Direct matching to targets.
    """

    def __init__(self, ignore_case=True):
        self.ignore_case = ignore_case

    def set_targets(self, targets):
        aliases = [ set([a]) for a in targets]
        self.am = MatcherAliases(aliases, ignore_case=self.ignore_case)
        self.am.set_targets(targets)

    def match(self, gene):
        return self.am.match(gene)
                
GMDirect = MatcherDirect
GMKEGG = MatcherAliasesKEGG
GMGO = MatcherAliasesGO
GMNCBI = MatcherAliasesNCBI
GMDicty = MatcherAliasesDictyBase

def issequencens(x):
    return hasattr(x, '__getitem__') and not isinstance(x, basestring)

def matcher(matchers, direct=True, ignore_case=True):
    """
    Build a matcher from a sequence of matchers. If a sequence element is a
    sequence, join matchers in the subsequence.

    direct - if True, add a direct matcher to targets
    ignore_case - if True, ignores case with optionally added direct matcher 
    """
    seqmat = []
    if direct:
        seqmat.append(MatcherDirect(ignore_case=ignore_case))
    for mat in matchers:
        if issequencens(mat):
            mat = MatcherAliasesPickledJoined(list(mat))
            seqmat.append(mat)
        else:
            seqmat.append(mat)
    return MatcherSequence(seqmat)

if __name__ == '__main__':

    #m1 = matcher([[GMNCBI('44689'), GMDicty()]])
    #print m1.matchers[1].aliases[:100]

    #m2 = GMNCBI('Dictyostelium discoideum')
    #print m2.aliases



    """
    gi = info(list(info)[0])
    print gi.tax_id, gi.synonyms, gi.dbXrefs, gi.symbol_from_nomenclature_authority, gi.full_name_from_nomenclature_authority
    """

    #dobim z joinom prave stvari?

    import time
    import obiGeneSets

    def testsets():
        return obiGeneSets.collections([":kegg:hsa", ":go:hsa"])

    def names1():
        import orange
        data = orange.ExampleTable("DLBCL.tab")
        return [ a.name for a in  data.domain.attributes ]

    def namesd():
        import orange
        data = orange.ExampleTable("dd_ge_biorep1.tab")
        names = [ ex["gene"].value for ex in data ]
        return names

    genesets = auto_pickle("testcol", "3", testsets)
    names = auto_pickle("testnames", "4", names1)
    names2 = auto_pickle("testnamesdicty", "4", namesd)

    info = NCBIGeneInfo('Dictyostelium discoideum')
    for a in names2:
        print a
        info.get_info(a)

    t = time.time()
    mat5 = matcher([[GMKEGG('human'),GMGO('human')]], direct=False, ignore_case=True)
    mat7 = GMDicty()
    mat8 = GMNCBI('Homo sapiens')
    print "initialized all", time.time()-t
    import obiGeneMatch as ogm
    mat6 = ogm.MatcherSequence([ogm.MatchKEGG([], 'hsa', caseSensitive=False)])

    print "using targets"

    mat5.set_targets(names)
    mat6.targets(names)
    mat7.set_targets(names)
    mat8.set_targets(names)

    print "before genes"
    genes = reduce(set.union, genesets.values()[:1000], set())
    genes = list(genes)
    print genes[:20]
    print len(genes)
    print "after genes"

    for g in sorted(genes):
        print "KGO ", g, mat5.match(g), mat5.explain(g)
        print "KEGG", g, mat6.match(g)
        print "DICT", g, mat7.match(g)
        print "NCBI", g, mat8.match(g)


