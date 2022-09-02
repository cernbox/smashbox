import logging
import os.path
import pickle
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseSettings


# this should probably be moved into a utilities module
def get_logger(name: str = "config", level: int | None = None) -> logging.Logger:
    if level is None:
        level = (
            logging.INFO
        )  # change here to DEBUG if you want to debug config stuff
    logging.basicConfig(level=level)
    return logging.getLogger(".".join(["smash", name]))


class Configuration(BaseSettings):
    """Root configuration object that parses the values defined in the config file."""

    smashdir: str
    oc_account_name: str | None
    oc_number_test_users: int
    oc_group_name: str | None
    oc_number_test_groups: int
    oc_account_password: str
    oc_server: str
    oc_root: str
    oc_server_folder: str
    oc_ssl_enabled: bool
    oc_server_shell_cmd: str
    oc_server_tools_path: str  # TODO: is this still needed?
    oc_sync_cmd: str
    oc_sync_repeat: int

    runid: int | None
    workdir_runid_enabled: bool
    oc_account_runid_enabled: bool

    oc_account_reset_procedure: Literal[
        "delete", "keep"
    ]  # there are some more types that are not yet implemented
    rundir_reset_procedure: Literal["delete", "keep"]

    web_user: str
    oc_admin_user: str
    oc_admin_password: str

    scp_port: int
    oc_server_log_user: str
    oc_check_server_log: bool

    @property
    def oc_webdav_endpoint(self) -> str:
        return os.path.join(self.oc_root, "remote.php/webdav")

    @property
    def oc_server_datadirectory(self) -> str:
        return os.path.join("/var/www/html", self.oc_root, "data")

    # these methods exists for backwards compatibility
    def _dict(self, **args: Any) -> dict[str, object]:
        """Returns a dictionary representation of the configuration object.
        Any extra arguments passed are also returned in this dictionary."""
        return {**self.dict(), **args}

    def get(self, key: str, default: object) -> object:
        """Returns the value of the specified setting, or the
        default if the key doesn't exist."""
        logger = get_logger()
        logger.debug("config.get(%s,default=%s)", key, default)
        return self._dict().get(key, default=default)


def log_config(
    config: Configuration, level: int = logging.DEBUG, hide_password: bool = False
) -> None:
    """Dump the entire configuration to the logging system at the given level.
    If hide_password=True then do not show the real value of the options which contain "password" in their names.
    """
    logger = get_logger()
    for key, val in config.dict().items():
        if hide_password and "password" in key:
            val = "***"
        logger.log(level, "CONFIG: %s = %s", key, val)


def load_config(fp: Path | str) -> Configuration:
    """Loads and parses the specified configuration file."""
    with open(fp, "r") as file:
        return Configuration(**yaml.load(file, Loader=yaml.Loader))


def configure_from_blob(fp: Path | str) -> Configuration:
    with open(fp, "rb") as file:
        return pickle.load(file)


def dump_config(config: Configuration, fp: Path | str) -> None:
    """Serialize given config object as YAML and write it to the specified file."""
    with open(fp, "w") as file:
        yaml.dump(config.dict(), file)
