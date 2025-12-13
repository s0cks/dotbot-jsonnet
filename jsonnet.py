import subprocess, dotbot, os
from pprint import PrettyPrinter

__version__ = "0.0.1"

class JsonnetResult:
  def __init__(self, out, config):
    if os.path.isdir(out) or (out.endswith("/") and not os.path.isfile(out)):
      self._multi = out
      print(f"multi: {out}")
    else:
      raise ValueError(f"failed to determine output of jsonnet: {out}")
    if isinstance(config, str):
      self._source = str
    elif not "source" in config:
      raise ValueError(f"failed to find source for {config}")
    self._source = config["source"]
    self._config = config
    
    self._ext_strs = []
    if "vars_from_env" in config:
      for v in config["vars_from_env"]:
        self._ext_strs.append(v)
    if "vars" in config:
      for k,v in config["vars"].items():
        self._ext_strs.append(f"{k}=\"{v}\"")

  def is_plain_text(self):
    return self._config.plain_text if "plain_text" in self._config else True

  def is_multi(self):
    return self._multi != None

  def get_command(self, extras = None):
    command = []
    command.append('jsonnet')
    command.append('--create-output-dirs')
    if self.is_plain_text():
      command.append('-S')
    if self.is_multi():
      command.append('-m')
      command.append(self._multi)
    print("ex strs")
    for ex in self._ext_strs:
      command.append("--ext-str")
      command.append(ex)
    command.append(self._source)
    if extras != None:
      command.append(extras)
    return command

class DotbotJsonnet(dotbot.Plugin):
  def can_handle(self, directive):
    """Flag whether or not this plugin supports the given *directive*."""
    valid = directive == "jsonnet"
    if not valid:
      self._log.debug(f"The Jsonnet plugin doesn't support the `{directive}` directive")
    return valid

  def handle(self, directive, data):
    if not self.can_handle(directive):
      self._log.error(f'cannot handle the `{directive}` directive')
      return False

    try:
      self._validate(data)
    except ValueError as error:
      self._log.error(error.args[0])
      return False

    for k,v in data.items():
      try:
        result = JsonnetResult(k, v)
        command = result.get_command()
        self._run_command(command)
      except Exception as ex:
        print(f"failed to process jsonnet file `{k}` with config `{config}`: {ex}")
    return True

  def _validate(self, data):
    pass

  def _run_command(self, command):
    try:
      if not isinstance(command, list):
        command = [command]
      print(f'running: {command}')
      subprocess.run([' '.join(command)], shell=True, check=True)
      return True
    except Exception as error:
      print(f"failed to run jsonnet: {error}")
      return False
