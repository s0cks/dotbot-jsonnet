import subprocess, dotbot, os
from pprint import PrettyPrinter

class DotbotJsonnet(dotbot.Plugin):
  _directive = 'jsonnet'
  def can_handle(self, directive):
    return self._directive == directive

  def handle(self, directive, data):
    if directive != self._directive:
      raise ValueError("jsonnet cannot handle `%s` directive" % directive)
    return self._run_command('jsonnet install')

  def _run_command(self, command):
    try:
      subprocess.run([command], shell=True, check=True)
      return True
    except subprocess.CalledProcessError:
      self._log.error('jsonnet command failed.')
      return False
