# gp.py: a simple, transparent python gnuplot interface
import os,sys,logging
from time import sleep
from subprocess import Popen,PIPE

ISO_8601 = '%Y-%m-%dT%H:%M:%S'

class GPHistFile:
  def __init__(self,name,mode):
    path,f_name = os.path.split(name)
    try : os.path.makedirs(path)
    except : pass
    try : self.file = open(name,mode)
    except : self.file = None
  def write(self,string):
    if self.file:
      self.file.write(string)
  def close(self):
    if self.file:
      self.file.close()

class GP:
  def __init__(self,*args,**kwargs):
    # gnuplot
    self.gp = Popen(('gnuplot',),stdout=PIPE,stdin=PIPE,close_fds=True)
    self.stdin,self.stdout = self.gp.stdin,self.gp.stdout

    # history
    hist_file = kwargs['hist_file'] if 'hist_file' in kwargs else os.path.join(os.getenv('HOME'),'.cache','gp.py.hist')
    mode = 'w' if 'clear_hist' in kwargs and kwargs['clear_hist'] else 'a'
    self.history = GPHistFile(hist_file,mode)

    # temp data files
    self.files = {} # dictionary of temp files used to store data for plots
    self.set('datafile separator "%s"' % (kwargs['f_sep'] if 'f_sep' in kwargs else ' '))

    # terminal
    term = kwargs['term'] if 'term' in kwargs else 'wxt'
    x,y = 800,480
    if 'canvas_size' in kwargs:
      x,y = kwargs['canvas_size'][0],kwargs['canvas_size'][1]
    self.set('term %s size %d,%d' % (term,x,y))

    # resolution
    self.set('samples %s' % (kwargs['samples'] if 'samples' in kwargs else 128))
    self.set('isosamples %s' % (kwargs['isosamples'] if 'isosamples' in kwargs else 128))

    # time formatting
    self.set('timefmt "%s"' % (kwargs['time_format'] if 'time_format' in kwargs else ISO_8601))
    self.axis_time_format = kwargs['axis_time_format'] if 'axis_time_format' in kwargs else '%m-%d\\n%H:%M'

    # key
    self.set('key %s' % (kwargs['key'] if 'key' in kwargs else 'top left'))

  def __del__(self):
    self.stdin.close()
    self.stdout.close()
    self.history.close()
    for f_name in self.files.keys():
      if not self.files[f_name].closed:
        self.files[f_name].close()
      if os.path.exists(f_name):
        os.remove(f_name)

  def action(action):
    def submit(self,arg):
      self.write('%s %s' % (action,arg))
    return submit

  set = action('set')
  plot = action('plot')
  splot = action('splot')

  def read(self):
    return self.stdout.read()

  def write(self,arg):
    '''
    submit command 'arg' to gnuplot and write it to history
    '''
    self.stdin.write('%s\n' % arg)
    sleep(0.25) # gnuplot actions are nonblocking
    self.history.write('%s\n' % arg)

  def write_file(self,f_name,*columns):
    '''
    Write data to temp file used to construct gnuplot plots.  All columns
    supplied must be 1D iterables of the same size.
    '''
    def get_separator():
      self.write('show datafile separator')
      result = re.match(r'^\s+datafile fields separated by (.+)\s*$',self.read()).groups(1)
      if result == 'whitespace':
        return ' '
      else:
        return re.match(r'^"(.+)"$').groups(1)
    f_sep = get_separator()
    self.files[f_name] = open(f_name,'w')
    for row in xrange(len(columns[0])):
      line = ''
      for column in columns:
        if not isinstance(column[row],str):
          element = '%g' % column[row]
        else:
          element = column[row]
        if len(line):
          line += f_sep
        line += element
      self.files[f_name].write('%s\n' % line)
    self.files[f_name].close()
