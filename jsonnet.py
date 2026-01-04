import subprocess, dotbot, os
from pprint import PrettyPrinter
from pathlib import Path

__version__ = "0.0.1"


def which(cmd):
    command = ["which", cmd]
    result = subprocess.run(
        [" ".join(command)], shell=True, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def cat_file(file):
    return Path(file).read_text(encoding="utf-8").strip()


def exec_command(cmd):
    result = subprocess.run(
        [" ".join([cmd])], shell=True, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_jsonnet_version(cmd):
    command = [cmd, "--version"]
    result = subprocess.run(
        [" ".join(command)], shell=True, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


class JsonnetVar:
    def __init__(self, k, v=None):
        self.name = k
        if v == None or isinstance(v, str):
            self.value = v
            return
        elif not isinstance(v, dict):
            raise Exception(f"invalid var value: {v}")
        if "env" in v:
            self.value = "$" + v["env"]
        elif "file" in v:
            try:
                self.value = '"' + cat_file(v["file"]) + '"'
            except Exception as ex:
                raise Exception(f"failed to read jsonnet var from file {v['file']}", ex)
        elif "command" in v:
            try:
                self.value = '"' + exec_command(v["command"]) + '"'
            except subprocess.CalledProcessError as ex:
                raise Exception(
                    f"failed to get jsonnet var from command {v['command']}: {ex.stderr}",
                    ex,
                )

    def __str__(self):
        if self.value:
            return f"{self.name}={self.value}"
        else:
            return self.name


class JsonnetResult:
    def __init__(self, out, config, include_dirs=[]):
        if os.path.isdir(out) or (out.endswith("/") and not os.path.isfile(out)):
            self._multi = out
        else:
            raise ValueError(f"failed to determine output of jsonnet: {out}")

        if isinstance(config, str):
            self._source = str
        elif not "source" in config:
            raise ValueError(f"failed to find source for {config}")
        else:
            self._source = config["source"]
            self._config = config
            self._ext_strs = []
            self._ext_strs += [
                JsonnetVar(v)
                for v in (config["vars_from_env"] if "vars_from_env" in config else [])
            ]
            self._ext_strs += [
                JsonnetVar(k, v)
                for k, v in (config["vars"] if "vars" in config else {}).items()
            ]
            self._include_dirs = include_dirs
            self._include_dirs += (
                config["include_dirs"] if "include_dirs" in config else []
            )

    def is_plain_text(self):
        return self._config.plain_text if "plain_text" in self._config else True

    def is_multi(self):
        return self._multi != None

    def multi(self):
        return self._multi

    def include_dirs(self):
        return self._include_dirs

    def extra_strings(self):
        return self._ext_strs

    def source(self):
        return self._source

    def command(self, extras=[]):
        command = []
        command.append("--create-output-dirs")
        if self.is_plain_text():
            command.append("-S")
        if self.is_multi():
            command.append("-m")
            command.append(self.multi())
        for dir in self.include_dirs():
            command.append("-J")
            command.append(dir)
        for ex in self.extra_strings():
            command.append("--ext-str")
            command.append(str(ex))
        command += extras
        command.append(self.source())
        return command


class DotbotJsonnet(dotbot.Plugin):
    def __init__(self, ctx):
        super().__init__(ctx)
        try:
            self._jsonnet_exec = which("jsonnet")
        except subprocess.CalledProcessError as ex:
            self._log.error(f"failed to find jsonnet executable: {ex.stderr}")
        self._log.info(
            f"found Jsonnet v{get_jsonnet_version(self._jsonnet_exec)}: {self._jsonnet_exec}"
        )

    def can_handle(self, directive):
        """Flag whether or not this plugin supports the given *directive*."""
        valid = directive == "jsonnet"
        if not valid:
            self._log.debug(
                f"The Jsonnet plugin doesn't support the `{directive}` directive"
            )
        return valid

    def include_dirs(self):
        return self._include_dirs

    def handle(self, directive, data):
        if not self.can_handle(directive):
            self._log.error(f"cannot handle the `{directive}` directive")
            return False

        self._include_dirs = []
        if "include_dirs" in data:
            self._include_dirs += data["include_dirs"]

        items = data
        if "items" in items:
            items = items["items"]

        for k, v in items.items():
            result = JsonnetResult(k, v, include_dirs=self._include_dirs)
            try:
                self._log.info(f"compiling {result.source()}....")
                self._jsonnet(self._jsonnet_exec, result)
            except subprocess.CalledProcessError as ex:
                self._log.error(
                    f"failed to process jsonnet file `{k}` with config `{v}`: {ex.stderr}"
                )
        return True

    def _jsonnet(self, exec, source):
        command = source.command()
        self._log.debug(f"executing jsonnet: {' '.join(command)}")
        subprocess.run(
            [" ".join([exec] + command)],
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
