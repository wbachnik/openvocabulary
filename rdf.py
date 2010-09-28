import re
import uuid

from django.db import models
from django.db.models.query import QuerySet

"""
Namespaces recognized by this package
"""
NAMESPACES = {
    'ibuk'      : 'http://v.ibookfactory.com/',
    'rdf'       : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs'      : 'http://www.w3.org/2000/01/rdf-schema#',
    'dc'        : 'http://purl.org/dc/terms/', 	#All DCMI properties, classes and encoding schemes (unless indicated below)
    'dctype'    : 'http://purl.org/dc/dcmitype/',	#Classes in the DCMI Type Vocabulary
    'dcam'      : 'http://purl.org/dc/dcam/',	#Terms used in the DCMI Abstract Model
    'dcel'      : 'http://purl.org/dc/elements/1.1/',
    'skos'      : 'http://www.w3.org/2004/02/skos/core#',
    'foaf'      : 'http://xmlns.com/foaf/0.1/',
    'vcard'     : 'http://www.w3.org/2006/vcard/ns#',
    'gvocab'    : 'http://rdf.data-vocabulary.org/#', #from Google rich snippets: Person, Product, Organization, etc
    'gr'        : 'http://purl.org/goodrelations/v1#', #Good Relations ontology
    'bibo'      : 'http://purl.org/ontology/bibo/', #bibliographic ontology
    'frbr'      : 'http://purl.org/vocab/frbr/core#', 
    'cc'        : 'http://creativecommons.org/ns#', #copyrights ontology
    'wcc'       : 'http://web.resource.org/cc/',
    'bibtex'    : 'http://purl.oclc.org/NET/nknouf/ns/bibtex#', 
    'dbpediap'  : 'http://dbpedia.org/property/',
    'xsd'       : 'http://www.w3.org/2001/XMLSchema#',
    'nfo'       : 'http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#',
    'v'         : 'http://rdf.data-vocabulary.org/#', # google rich snippets
    'ov'        : 'http://www.openvocabulary.info/ontology/', #open vocabulary
}

INV_NAMESPACE = dict([[v,k] for k,v in NAMESPACES.items()])

DEF_VOCAB_NAMESPACE = "http://id.ibookfactory.com/vocab#"
DEF_INSTANCE_NAMESPACE = "http://id.ibookfactory.com/"

TURTLE_NS_HEAD = "@prefix %s: <%s>.\n"

"""
Use this model to get additional features from the RDF data model
"""
class RdfConcept(object):
    def __init__(self, uri=None, rdf_types=[]):
        _uri = uri
        _rdf_types = rdf_types
    
    """
    Returns RDF (Turtle) representation of this object
    """
    def to_rdf(self):
        rdf = self.__head__()
        rdf += "\n%s\n" % self.to_uri(self.get_uri())
        #
        rdf += "\ta %s" % self.object_to_string(self.get_rdf_types())
        #
        # -- for each defined property --
        rdfMeta = self.rdfMeta()
        for prop in rdfMeta:
            property_uri, rval = self.get_property_uris(prop, rdfMeta)
            for puri in property_uri:
                rdf += ";\n\t%s %s" % (self.to_uri(puri), rval)
        #        
        rdf += ".\n"
        return rdf

    """
    Returns list with property uris of given prop type
    """
    def get_property_uris(self, prop, rdfMeta=None):
        if not rdfMeta:
            rdfMeta = self.rdfMeta()
        rdfprops = rdfMeta[prop]
        # -- get the value of this property
        dbval = getattr(self, rdfprops["property"]) if "property" in rdfprops else getattr(self, prop)
        # --- if this is a relation type of property
        if hasattr(dbval, 'all') and callable(dbval.all):
            rval = self.objects_as_rdf_list(dbval.all())
        # --- if this is a literal ?
        else:
            rval = self.property_to_string(prop)
        # -- property
        property_uri = rdfMeta[prop]["uri"]
        # -- repack
#        result_prop_uri = []
        if isinstance(property_uri, (list, tuple, QuerySet)):
            result_prop_uri = property_uri
#            for puri in property_uri:
#                result_prop_uri += puri
        else:
            result_prop_uri = [ property_uri ]
        # -- return
        return result_prop_uri, rval
        
    """
    Allows to retrieve literal type of given property
    
    TODO: should be delivered by data not model in the future
    """
    def get_literal_type(self, prop, rdfMeta=None):
        if not rdfMeta:
            rdfMeta = self.rdfMeta()
        if prop in rdfMeta:
            rdfprops = rdfMeta[prop]
            if "xsd" in rdfprops:
                return rdfprops["xsd"]    
        return None
    
    """
    Allows to retrive literal lang tag of given property
    
    TODO: should be delivered by data not model in the future
    """
    def get_literal_lang(self, prop, rdfMeta=None):
        if not rdfMeta:
            rdfMeta = self.rdfMeta()
        if prop in rdfMeta:
            rdfprops = rdfMeta[prop]
            if "lang" in rdfprops:
                return rdfprops["lang"]    
        return None
     
    """
    Creates generic head in the RDF turtle format.
    """
    def __head__(self):
        head = ""
        for key, value in NAMESPACES.items():
            head += TURTLE_NS_HEAD % (key, value)
        return head
        
    """
    Returns URI of this object.
    Creates a new one based on the instance namespace and UUID if none given so far
    """
    def get_uri(self):
        if not hasattr(self, "_uri"):
            _uri = DEF_INSTANCE_NAMESPACE + str(uuid.uuid1())
        return _uri
   
    """
    Returns list of rdf:type URIs
    Creates a new one based on the vocabulary namespace and name of the Python class if none given so far
    """
    def get_rdf_types(self):
        if not hasattr(self, "_rdf_types"):
            _rdf_types = [ DEF_VOCAB_NAMESPACE + self.get_class_name() ]
        return _rdf_types
    
    """
    Returns the (Python) class of this object
    """    
    def get_class(self):
        return self.__class__
        
    """
    Return the name of the (Python) class of this object
    """
    def get_class_name(self):
        return self.__class__.__name__
   
    """
    Converts an array of objects to a list compatible with RDF
    """
    def objects_as_rdf_list(self, objects):
        n = len(objects)
        if n == 0:
            raise ValueError("Cannot list empty array or non-array")
        elif n == 1:
            return self.object_to_string(objects[0])
        else: 
            return ", ".join("%s" % self.object_to_string(v) for v in objects ) # -- I love the power of Python :)

    """
    Convert arbitrary object to RDF compatible representation "literal", <resource>
    """
    def object_to_string(self, obj):
        if hasattr(obj, "get_uri"):
            return self.to_uri(obj.get_uri())
        elif isinstance(obj, (list, tuple, QuerySet)):
            return self.objects_as_rdf_list(obj)
        else:
            return '"%s"' % str(obj)
    
    """
    Converts to string information based on the property information
    """        
    def property_to_string(self, prop):
        rdfMeta = self.rdfMeta()
        rdfprops = rdfMeta[prop]
        dbval = getattr(self, rdfprops["property"]) if "property" in rdfprops else getattr(self, prop)
        #-- check if if conversion for value is given
        if 'value' in rdfprops:
            if 'dict' in rdfprops:
                dbval = rdfprops['dict'][dbval]
            dbval = eval(rdfprops["value"] % dbval)
        elif 'attribute' in rdfprops:
            dbval = getattr(dbval, rdfprops['attribute'])
        #-- then check if we are about to create a URI after all
        if 'uri_pattern' in rdfprops:
            return self.to_uri(rdfprops["uri_pattern"] % dbval)
        elif 'literal_pattern' in rdfprops:
            return rdfprops["literal_pattern"] % dbval
        else:
            return self.object_to_string(dbval)
            
    """
    Generates appropriate URI form <http://full/uri> or short:uri
    """        
    def to_uri(self, value):
        if hasattr(value, "get_uri"):
            return self.to_uri(value.get_uri())
        else:
            ns = value.split(":")[0]
            if ns in NAMESPACES:
                return value
            else:
                return "<%s>" % value
    
    """
    Empty specification of concepts
    """
    def rdfMeta(self):
        return {}
    
"""
RDF Class
"""        
class RdfClass(RdfConcept):
    properties = {}
    
    def makeStringLiteral(self, attr, spec):
        properties[attr] = CharLiteralRdfProperty(self)
        setattr(self, attr, spec)
        
    class Meta:
        abstract = True      
    
"""
RDF Property
"""
class RdfProperty(RdfConcept):
    pass
    
class CharLiteralRdfProperty(RdfProperty):
    description = "rdf:Literal string representation" 
    
    def __init__(self, klass):
        _klass = klass
    
"""
URI Class
"""
class URI(object):
    def __init__(self, uri):
        self._uri = uri
        
    def get_uri(self):
        return self._uri
