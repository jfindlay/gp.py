# gp.py: a simple, transparent python gnuplot interface
import os,sys,time,subprocess

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
      if not self.file.closed:
        self.file.write(string)
  def close(self):
    if self.file:
      self.file.close()

class GP:
  def __init__(self,*args,**kwargs):
    # gnuplot
    self.gp = subprocess.Popen(('gnuplot',),stdout=subprocess.PIPE,stdin=subprocess.PIPE,close_fds=True)
    self.stdin,self.stdout = self.gp.stdin,self.gp.stdout

    # history
    hfile = kwargs['hfile'] if 'hfile' in kwargs else os.path.join(os.getenv('HOME'),'.cache','gp.py.hist')
    mode = 'w' if 'clrhist' in kwargs and kwargs['clrhist'] else 'a'
    self.history = GPHistFile(hfile,mode)

    # temp data files
    self.files = {} # dictionary of temp files used to store data for plots
    self.set('datafile separator "%s"' % (kwargs['fsep'] if 'fsep' in kwargs else ' '))

    # terminal
    term = kwargs['term'] if 'term' in kwargs else 'wxt'
    x,y = 800,480
    if 'pltsize' in kwargs:
      x,y = kwargs['pltsize'][0],kwargs['pltsize'][1]
    self.set('term %s size %d,%d' % (term,x,y))

    # resolution
    self.set('samples %s' % (kwargs['samples'] if 'samples' in kwargs else 128))
    self.set('isosamples %s' % (kwargs['isosamples'] if 'isosamples' in kwargs else 128))

    # time formatting
    self.set('timefmt "%s"' % (kwargs['timefmt'] if 'timefmt' in kwargs else ISO_8601))
    self.axtimefmt = kwargs['axtimefmt'] if 'axtimefmt' in kwargs else '%m-%d\\n%H:%M'

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
    time.sleep(len(str(arg))/1000.) # gnuplot actions are nonblocking
    self.history.write('%s\n' % arg)

  def write_here(self,name,rows,EOD='EOD'):
    '''
    format 'rows' into a gnuplot here document named '$name' (supported by
    >=gnuplot-2.7).  'rows' consists of an iterable of strings, where each
    string is a row of data
    '''
    here = '$%s << %s\n' % (name,EOD)
    for row in rows:
      here += '%s\n' % row
    here += '%s\n' % EOD
    self.write(here)

  def write_file(self,f_name,*matrix):
    '''
    Write data to temp file used to construct gnuplot plots.  All matrix
    columns supplied must be 1D iterables of the same size.
    '''
    def get_separator():
      self.write('show datafile separator')
      if 'whitespace' == re.match(r'^\s+datafile fields separated by (.+)\s*$',self.read()).groups(1):
        return ' '
      else:
        return re.match(r'^"(.+)"$').groups(1)
    fsep = get_separator()
    self.files[f_name] = open(f_name,'w')
    for row in xrange(len(matrix[0])):
      line = ''
      for column in xrange(len(matrix)):
        if len(line):
          line += fsep
        if not isinstance(matrix[column][row],str):
          line += '%g' % matrix[column][row]
        else:
          line += matrix[column][row]
      self.files[f_name].write('%s\n' % line)
    self.files[f_name].close()
