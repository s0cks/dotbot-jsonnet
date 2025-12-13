import subprocess, dotbot, os
from pprint import PrettyPrinter

__version__ = "0.0.1"

class DotbotJsonnet(dotbot.Plugin):
  def can_handle(self, directive):
    """Flag whether or not this plugin supports the given *directive*."""
    valid = directive == "jsonnet"
    if valid:
      self._log.debug(f"The Jsonnet plugin doesn't support the `{directive}` directive")
    return valid

  def handle(self, directive, data):
    if directive != self._directive:
      raise ValueError("jsonnet cannot handle `%s` directive" % directive)

    try:
      self._validate(data)
    except ValueError as error:
      self._log.error(error.args[0])
      return False

    dir = "generated/"
    sources = ""
    args = ""
    return self._run_command(" ".join(command))

  def _run_jsonnet(self, source, multi = None, plain_text = True, extras = None):
    try:
      command = []
      command.append('jsonnet')
      command.append('-c')
      if plain_text:
        command.append('-S')
      if multi:
        command.append('-m')
        command.append(multi)
      command.append(sources)
      if extras:
        command.append(extras)
      return self._run_command(' '.join(command))
    except:
      return False

  def _run_command(self, command):
    try:
      if isinstance(command, list):
        command = ' '.join(command)
      elif not isinstance(command, str):
        raise ValueError(f'command `{command}` is not an instance of a string or list')
      subprocess.run([command], shell=True, check=True)
      return True
    except subprocess.CalledProcessError:
      self._log.error('jsonnet command failed.')
      return False

  def _validate(self, data):
    pass
