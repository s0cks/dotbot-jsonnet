import subprocess, dotbot, os
from pprint import PrettyPrinter

__version__ = "0.0.1"


def get_jsonnet_exec():
    pass


def which(cmd):
    command = ["which", cmd]
    result = subprocess.run(
        [" ".join(command)], shell=True, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_jsonnet_version(cmd):
    command = [cmd, "--version"]
    result = subprocess.run(
        [" ".join(command)], shell=True, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


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
            if "vars_from_env" in config:
                for v in config["vars_from_env"]:
                    self._ext_strs.append(v)
            if "vars_from_file" in config:
                for k, v in config["vars_from_file"].items():
                    # TODO(@s0cks): dont use cat to consume file
                    self._ext_strs.append(f'{k}="$(/bin/cat {v})"')
            if "vars" in config:
                for k, v in config["vars"].items():
                    self._ext_strs.append(f'{k}="{v}"')
            self._include_dirs = include_dirs
            if "include_dirs" in config:
                self._include_dirs += config["include_dirs"]

    def source(self):
        return self._source

    def ext_strs(self):
        return self._ext_strs

    def is_plain_text(self):
        return self._config.plain_text if "plain_text" in self._config else True

    def multi(self):
        return self._multi


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
                self._jsonnet(
                    self._jsonnet_exec,
                    result.source(),
                    self.include_dirs(),
                    result.is_plain_text(),
                    result.multi(),
                    result.ext_strs(),
                )
            except subprocess.CalledProcessError as ex:
                print(
                    f"failed to process jsonnet file `{k}` with config `{v}`: {ex.stderr}"
                )
        return True

    def _jsonnet(
        self,
        exec,
        source,
        include_dirs=[],
        plain_text=True,
        multi=None,
        ext_strs=[],
        extras=[],
    ):
        command = [exec]
        command.append("--create-output-dirs")
        if plain_text:
            command.append("-S")
        if multi != None:
            command.append("-m")
            command.append(multi)
        for dir in include_dirs:
            command.append("-J")
            command.append(dir)
        for ex in ext_strs:
            command.append("--ext-str")
            command.append(ex)
        command += extras
        command.append(source)
        self._log.debug(f"executing {' '.join(command)}")
        subprocess.run(
            [" ".join(command)], shell=True, check=True, capture_output=True, text=True
        )
