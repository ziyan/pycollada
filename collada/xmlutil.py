import functools

VERSION_1_4_1 = '1.4.1'
VERSION_1_4 = VERSION_1_4_1
VERSION_1_5_0 = '1.5.0'
VERSION_1_5 = VERSION_1_5_0
DEFAULT_VERSION = VERSION_1_4

_COLLADA_VERSION = DEFAULT_VERSION

COLLADA_NAMESPACES = {
   '1.4.1': 'http://www.collada.org/2005/11/COLLADASchema',
   '1.5.0': 'http://www.collada.org/2008/03/COLLADASchema',
}

get_collada_ns = lambda: COLLADA_NAMESPACES[_COLLADA_VERSION]
get_collada_version = lambda: _COLLADA_VERSION

HAVE_LXML = False

try:
    from lxml import etree
    HAVE_LXML = True
except ImportError:
    from xml.etree import ElementTree as etree

ET = etree

try:
    from functools import partial
except ImportError:
    # fake it for pre-2.5 releases
    def partial(func, tag):
        return lambda *args, **kwargs: func(tag, *args, **kwargs)

try:
    callable
except NameError:
    # Python 3
    def callable(f):
        return hasattr(f, '__call__')

try:
    basestring
except (NameError, KeyError):
    basestring = str

try:
    unicode
except (NameError, KeyError):
    unicode = str

if HAVE_LXML:
    from lxml.builder import E, ElementMaker
    
    def writeXML(xmlnode, fp):
        xmlnode.write(fp, pretty_print=True)

    E = ElementMaker(namespace=get_collada_ns(), nsmap={None: get_collada_ns()})
else:
    class ElementMaker(object):
        def __init__(self, namespace=None, nsmap=None):
            if namespace is not None:
                self._namespace = '{' + namespace + '}'
            else:
                self._namespace = None
        
        def __call__(self, tag, *children, **attrib):
            if self._namespace is not None and tag[0] != '{':
                tag = self._namespace + tag
            
            elem = etree.Element(tag, attrib)
            for item in children:
                if isinstance(item, dict):
                    elem.attrib.update(item)
                elif isinstance(item, basestring):
                    if len(elem):
                        elem[-1].tail = (elem[-1].tail or "") + item
                    else:
                        elem.text = (elem.text or "") + item
                elif etree.iselement(item):
                    elem.append(item)
                else:
                    raise TypeError("bad argument: %r" % item)
            return elem
    
        def __getattr__(self, tag):
            return functools.partial(self, tag)

    E = ElementMaker(namespace=get_collada_ns(), nsmap={None: get_collada_ns()})
    
    if etree.VERSION[0:3] == '1.2':
        #in etree < 1.3, this is a workaround for supressing prefixes
        
        def fixtag(tag, namespaces):
            import string
            # given a decorated tag (of the form {uri}tag), return prefixed
            # tag and namespace declaration, if any
            if isinstance(tag, etree.QName):
                tag = tag.text
            namespace_uri, tag = string.split(tag[1:], "}", 1)
            prefix = namespaces.get(namespace_uri)
            if namespace_uri not in namespaces:
                prefix = etree._namespace_map.get(namespace_uri)
                if namespace_uri not in etree._namespace_map:
                    prefix = "ns%d" % len(namespaces)
                namespaces[namespace_uri] = prefix
                if prefix == "xml":
                    xmlns = None
                else:
                    if prefix is not None:
                        nsprefix = ':' + prefix
                    else:
                        nsprefix = ''
                    xmlns = ("xmlns%s" % nsprefix, namespace_uri)
            else:
                xmlns = None
            if prefix is not None:
                prefix += ":"
            else:
                prefix = ''
                
            return "%s%s" % (prefix, tag), xmlns
    
        etree.fixtag = fixtag
        etree._namespace_map[get_collada_ns()] = None
    else:
        #For etree > 1.3, use register_namespace function
        etree.register_namespace('', get_collada_ns())

    def indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def writeXML(xmlnode, fp):
        indent(xmlnode.getroot())
        xmlnode.write(fp)

def _set_version(version):
    global _COLLADA_VERSION
    _COLLADA_VERSION = version
    E._namespace = '{' + get_collada_ns() + '}'
    E._nsmap = {None: get_collada_ns()}
    if not HAVE_LXML and etree.VERSION[0:3] == '1.2':
        etree._namespace_map[get_collada_ns()] = None
    elif not HAVE_LXML:
        etree.register_namespace('', get_collada_ns())

# need this for URI decoding
try:
    from urllib import unquote
    def UnquoteSafe(s):
        if s is not None:
            return unquote(s)
        return None
except ImportError:
    def UnquoteSafe(s):
        return s
