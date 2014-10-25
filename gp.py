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
    hfile = kwargs.get('hfile',os.path.join(os.getenv('HOME'),'.cache','gp.py.hist'))
    mode = 'w' if kwargs.get('clrhist') else 'a'
    self.history = GPHistFile(hfile,mode)

    # temp data files
    self.files = {} # dictionary of temp files used to store data for plots
    self.set('datafile separator "{s}"'.format(s=kwargs.get('fsep',' ')))

    # terminal
    term = kwargs.get('term','wxt')
    size = kwargs.get('size',(800,480))
    self.set('term {t} size {x},{y}'.format(t=term,x=size[0],y=size[1]))

    # resolution
    self.set('samples {s}'.format(s=kwargs.get('samples',128)))
    self.set('isosamples {i}'.format(i=kwargs.get('isosamples',128)))

    # time formatting
    self.set('timefmt "{t}"'.format(t=kwargs.get('timefmt',ISO_8601)))
    self.axtimefmt = kwargs.get('axtimefmt','%m-%d\\n%H:%M')

    # key
    self.set('key {k}'.format(k=kwargs.get('key','top left')))

  def __del__(self):
    self.stdin.close()
    self.stdout.close()
    self.history.close()
    for f_name in self.files.keys():
      if not self.files[f_name].closed:
        self.files[f_name].close()
      if os.path.exists(f_name):
        os.remove(f_name)

  def action(act):
    def submit(self,arg):
      self.write('{act} {arg}'.format(act=act,arg=arg))
    return submit

  set = action('set')
  unset = action('unset')
  plot = action('plot')
  splot = action('splot')

  def read(self):
    return self.stdout.read()

  def write(self,arg):
    '''
    submit command 'arg' to gnuplot and write it to history
    '''
    self.stdin.write('{a}\n'.format(a=arg))
    time.sleep(len(str(arg))/1000.) # gnuplot actions are nonblocking
    self.history.write('{a}\n'(a=arg))

  def write_here(self,name,rows,EOD='EOD'):
    '''
    format 'rows' into a gnuplot here document named '$name' (supported by
    >=gnuplot-4.7.p0).  'rows' consists of an iterable of strings, where each
    string is a row of data
    '''
    here = '${n} << {E}\n'.format(n=name,E=EOD)
    for row in rows:
      here += '{r}\n'.format(r=row)
    here += '{E}\n'.format(E=EOD)
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
          line += '{element:g}'.format(element=matrix[column][row])
        else:
          line += matrix[column][row]
      self.files[f_name].write('{l}\n'.format(l=line))
    self.files[f_name].close()
