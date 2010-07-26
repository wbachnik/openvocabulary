from django.db import models
from django.contrib import admin
from django.template import RequestContext
from ov_django.rdf import *
from ov_django.settings import BASE_URL_PATH

# --------------------- context -----------------------------    
    
CONTEXT_TYPE = (
    ('tax', 'taxonomy'),
    ('tez', 'thesaurus'),
    ('tag', 'tagging')
)    
    
class ContextManager(models.Manager):
    def search(self, key):
        results = [] #Publisher.objects.filter(name__icontains=key) | Publisher.objects.filter(address__icontains=key)
        print "Found %d results for %s" % (len(results), key)
        return results

    """
    Lookup manifests by isbn
    """   
    def lookup(self, value):
        try:
            result = Context.objects.get(uri=value)
        except Exception:
            result = None
        return result
    
"""
Represents the dictionary
"""    
class Context(models.Model):
    label = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    uri = models.URLField(verify_exists=False)
    ns = models.CharField(max_length=10)
    type = models.CharField(max_length=3, choices=CONTEXT_TYPE, default='tag')
    lang = models.CharField(max_length=10, default='en') 
    term_uri_pattern = models.CharField(max_length=255, blank=True, null=True, verbose_name="uri pattern")
    # additional_properties
    # tree_properties
    objects = ContextManager()
    
    """
    to-string representation
    """
    def __unicode__(self):
        return "%s [%s]" % (self.label, self.uri)

    '''
    Returns roots of this context
    '''
    def get_roots(self):
        return [] #TODO

    """
    Django meta information
    """
    class Meta:
        ordering = ['label']
        
              
class ContextAdmin(admin.ModelAdmin):
#    readonly_fields = ('uid',)
    list_display = ('label', 'description', 'uri', 'ns', 'type', 'lang', 'term_uri_pattern',)
    list_filter = ('label', 'type', 'lang',)
    fieldsets = (
            ('text', {
                'fields': ('label', 'description'),
                'classes': ('basic',),
                'description': ("Provide basic information about the context"),
            }),
            ('uri', {
                'fields': ('uri', 'ns', 'term_uri_pattern'),
                'classes': ('basic',),
                'description': ("URI-based information"),
            }),
            ('meta', {
                'fields': ('type', 'lang'),
                'classes': ('basic',),
                'description': ("Additional meta information"),
            }),
    )
            

# --------------------- entry -----------------------------    

PART_OF_SPEECH = (
    ('adj', 'adjective'),
	('sat', 'adjectivesatellite'),
	('adv', 'adverb'),
	('noun', 'noun'),
	('verb', 'verb'),
	('none', 'unknown'),
)

ENTRY_RELATION_TYPES = (
    ('hyponyms', 'hyponyms'),
    ('hypernyms', 'hypernyms'),
    ('antonyms', 'antonyms'),
    ('synonyms', 'synonyms'),
    ('meanings', 'meanings'),
    ('meronymOf', 'meronym of'),
    ('partMeronymOf', 'part meronym of'),
    ('similarTo', 'similar to')
)

CLASSIFICATION_TYPES = (
    ('none', ''),
    ('region', 'region'),
    ('topic', 'topic'),
    ('usage', 'usage'),
)



class EntryManager(models.Manager):
    def search(self, key):
        results = [] #Publisher.objects.filter(name__icontains=key) | Publisher.objects.filter(address__icontains=key)
        print "Found %d results for %s" % (len(results), key)
        return results

    """
    Lookup manifests by isbn
    """   
    def lookup(self, value):
        try:
            result = Entry.objects.get(uri=value)
        except Exception:
            result = None
        return result

"""
Represents the dictionary entry
"""    
class Entry(models.Model):
    label = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    uri = models.URLField(verify_exists=False)
    context = models.ForeignKey(Context)
    is_root = models.BooleanField(default=False)
    # -- thesaurus --
    relations = models.ManyToManyField('self', related_name='relation', symmetrical=False, through='EntryReference', blank=True, null=True)
    # -- word --
    lexical_form = models.CharField(max_length=100, blank=True, null=True)
    # -- word sense --
    in_synset = models.ForeignKey('self', related_name='inSynset', blank=True, null=True)
    tag_count = models.IntegerField(blank=True, null=True) #the tagcount value for word net
    words = models.ManyToManyField('self', related_name='word', symmetrical=False, blank=True, null=True)
    # -- synset --
    gloss = models.CharField(max_length=255, blank=True, null=True)
    synset_id = models.IntegerField(null=True)
    pos = models.CharField(max_length=10, choices=PART_OF_SPEECH) #part of speech
    word_senses = models.ManyToManyField('self', related_name='wordSense', symmetrical=False) # --> containsWordSense, <-- inWordSense
    classified_by = models.ManyToManyField('self', related_name='classifiedBy', symmetrical=False, through='ClassificationReference', blank=True, null=True)
    # -- taxonomy --
    parent = models.ForeignKey('self', related_name='childOf', blank=True, null=True)
    #
    # additional_properties ?
    #
    objects = ContextManager()

    """
    to-string representation
    """
    def __unicode__(self):
        return "%s [%s]" % (self.get_label(), self.uri)
    
    """
    Returns array of entries that are children of this one in the tree
    """
    def get_sub_entries(self):
        return [] #TODO
        
    """
    Returns path from Root to this entry
    """
    def get_path_from_root(self):
        return [] #TODO    
        
    """
    Return all entries below this entry
    """
    def get_descendants(self):
        return [] #TODO

    """
    set of {@link WordSenseEntity} objects related to this <code>WordEntity</code> 
    through inverse property of <code>http://www.w3.org/2006/03/wn/wn20/schema/word</code>
    """
    def get_in_word_sense(self):
        return []; #TODO

    def get_label(self):
        return self.lexical_form if self.lexical_form else self.label

    """
    Django meta information
    """
    class Meta:
        ordering = ['label']
        verbose_name_plural = "entries"

"""
Allows to define multiple references between dictionary entries
"""
class EntryReference(models.Model):
    subject = models.ForeignKey(Entry, related_name='ref_subject')
    object = models.ForeignKey(Entry, related_name='ref_object')
    relation = models.CharField(max_length=15, choices=ENTRY_RELATION_TYPES)

"""
Allows to define multiple references of classifiedBy 
"""
class ClassificationReference(models.Model):
    subject = models.ForeignKey(Entry, related_name='class_subject')
    object = models.ForeignKey(Entry, related_name='class_object')
    type = models.CharField(max_length=10, choices=CLASSIFICATION_TYPES)



class EntryAdmin(admin.ModelAdmin):
#    readonly_fields = ('uid',)
    pass