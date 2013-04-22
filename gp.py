# gp.py: a simple, transparent python gnuplot interface
import os,sys
from subprocess import Popen,PIPE

ISO_8601 = '%Y-%m-%dT%H:%M:%S'

class GP:
  def __init__(self):
    self.term = 'wxt'
    self.samples = 128
    self.isosamples = 128
    self.canvas_size = (1024,600)
    self.time_format = ISO_8601
    self.axis_time_format = '%m-%d\\n%H:%M'
    self.files = {}  # dictionary of files used to store data for plots
    self.f_sep = '|' # data file field separator
    self.history = open('%s/pygp.hist' % self._ensure_dir('%s/.cache' % os.getenv('HOME')),'w')
    self.gp = Popen(('gnuplot',),stdout=PIPE,stdin=PIPE,close_fds=True)
    self.stdin,self.stdout = self.gp.stdin,self.gp.stdout
    self.write('set samples %d\n' % self.samples)
    self.write('set isosamples %d\n' % self.isosamples)
    self.write('set key top left\n')
    self.set_datafile_separator()
    self.set_term()

  def __del__(self):
    self.gp.stdin.close()
    self.gp.stdout.close()
    self.history.close()
    for f_name in self.files.keys():
      if not self.files[f_name].closed:
        self.files[f_name].close()
      if os.path.exists(f_name):
        os.remove(f_name)

  def _ensure_dir(self,directory):
    '''
    check whether the supplied directory exists, create it if it doesn't, and
    exit if it is not a directory
    '''
    if not os.path.exists(directory):
      if not os.path.islink(directory):
        os.makedirs(directory)
        return directory
    elif os.path.isdir(directory):
      return directory
    sys.stderr.write('%s exists and is not a directory\n' % directory)
    sys.stderr.flush()
    sys.exit(1)

  def write(self,arg):
    '''
    submit command 'arg' to gnuplot and write it to history
    '''
    self.stdin.write(arg)
    self.history.write(arg)

  def set_datafile_separator(self,f_sep=None):
    if f_sep : s = f_sep
    else : s = self.f_sep
    self.set('datafile separator "%s"' % s)

  def set_term(self,term=None,width=None,height=None):
    '''
    setup terminal
    '''
    if term : t = term
    else : t = self.term
    if width : x = width
    else : x = self.canvas_size[0]
    if height : y = height
    else : y = self.canvas_size[1]
    self.set('term %s size %d,%d' % (t,x,y))

  def set_time_format(self,fmt=None):
    if fmt : f = fmt
    else : f = self.time_format
    self.set('timefmt "%s"' % f)

  def set(self,arg=None):
    '''
    set gnuplot setting 'arg'
    '''
    if arg:
      self.write('set %s\n' % arg)

  def write_file(self,f_name,*args):
    '''
    Write data to temp file used to construct gnuplot plots.  All args supplied
    must be 1D iterables of the same size.
    '''
    self.files[f_name] = open(f_name,'w')
    for row in xrange(len(args[0])):
      line = ''
      for arg in args:
        if not isinstance(arg[row],str):
          m = '%g' % arg[row]
        else:
          m = arg[row]
        if len(line):
          line += self.f_sep
        line += m
      self.files[f_name].write('%s\n' % line)
    self.files[f_name].close()

  def plot(self,arg=None):
    '''
    plot with argument 'arg'
    '''
    self.write('plot %s\n' % arg)
    self.gp.wait()
