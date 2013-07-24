
# Turns out we can't use pylal inside of a CGI script...
#from pylal.dq.dqFrameUtils import Channel

from shared import data

H5_FILE = "channels.h5"

class Channel(object):

    def __init__(self, ifo='', subsystem='', name='', properties=None):
        self.ifo = ifo
        self.subsystem = subsystem
        self.name = name
        self.properties = properties or dict()

    def todict(self):
        return {'ifo': self.ifo,
                'subsystem': self.subsystem, 
                'name': self.name, 
                'properties': self.properties}
    
    @data.use_h5(H5_FILE, 'w')
    def flush_properties(self, h5=None):
        for name, value in self.properties.iteritems():
            h5[self.h5_path].attrs[name] = value
            
    @data.use_h5(H5_FILE, 'w')
    def clear_properties(self, h5=None):
        attrs = h5[self.h5_path].attrs
        for name in attrs: del attrs[name]
        self.properties.clear()

    @property
    def h5_path(self):
        return "{0.ifo}/{0.subsystem}/{0.name}".format(self)
        
    @property
    def file_path(self):
        return "{0.ifo}-{0.subsystem}-{0.name}".format(self)
        
    @property
    def dt(self):
        return 1.0/self.properties['sampling']
        
    @property
    def full_name(self):
        return '{0.ifo}:{0.subsystem}_{0.name}'.format(self)

    def __repr__(self):
        return """Channel(name='{0.name}', 
                          ifo='{0.ifo}', 
                          subsystem='{0.subsystem}', 
                          properties={0.properties})"""\
               .replace(' ', '').replace('\n', ' ').format(self)

    def __str__(self):
        return "Channel {0.h5_path}".format(self)
        
    def __eq__(self, other):
        if isinstance(other, Channel):
            return self.ifo == other.ifo and\
                   self.subsystem == other.subsystem and\
                   self.name == other.name
        else:
            return False


@data.use_h5(H5_FILE, 'r')
def get_all_ifos(h5=None):
    return list(h5)

@data.use_h5(H5_FILE, 'r')
def get_subsystems(ifo, h5=None):
    return list(h5[ifo])

@data.use_h5(H5_FILE, 'r')
def get_channels(ifo, subsystem, h5=None):
    root = h5[ifo][subsystem]
    return [_parse_channel(root[name], ifo=ifo, subsystem=subsystem, name=name) 
            for name in root]
            
@data.use_h5(H5_FILE, 'r')
def get_all_channels(h5=None):
    return [channel for ifo in get_all_ifos(h5=h5)
                    for subsystem in get_subsystems(ifo, h5=h5)
                    for channel in get_channels(ifo, subsystem, h5=h5)]

@data.use_h5(H5_FILE, 'r')
def get_channel(ifo, subsystem, name, h5=None):
    return _parse_channel(h5[ifo][subsystem][name], 
                          ifo=ifo, subsystem=subsystem, name=name)

@data.use_h5(H5_FILE, 'w')
def add_ifo(ifo, h5=None):
    return h5.require_group(ifo)
    
@data.use_h5(H5_FILE, 'w')
def add_subsystem(ifo, subsystem, h5=None):
    return add_ifo(ifo).require_group(subsystem)

@data.use_h5(H5_FILE, 'w')
def add_channel(channel, clear_other_properties=False, h5=None):
    subsystem = add_subsystem(channel.ifo, channel.subsystem, h5=h5)
    group = subsystem.require_group(channel.name)
    
    if clear_other_properties: 
        channel.clear_properties(h5=h5)
    channel.flush_properties(h5=h5)
    
    return group

def _parse_channel(group, ifo='', subsystem='', name=''):
    return Channel(ifo=ifo, subsystem=subsystem, name=name,
                   properties=dict(group.attrs.iteritems()))
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    