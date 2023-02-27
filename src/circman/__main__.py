"""Command-line interface."""
import datetime
import glob
import logging
import os
import shutil
import sys
from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import check_output  # noqa: S404
from typing import Any
from typing import List
from typing import Optional

import click
import platformdirs


appname = "circman"
appauthor = "circman"

DATA_DIR = platformdirs.user_data_dir(appname=appname, appauthor=appauthor)
LOG_DIR = platformdirs.user_log_dir(appname=appname, appauthor=appauthor)
#: The location of the log file for the utility.
LOGFILE = os.path.join(LOG_DIR, "circman.log")

BACKUP_DIR = os.path.join(DATA_DIR, "archives")

# Ensure BACKUP_DIR / LOG_DIR related directories and files exist.
if not os.path.exists(BACKUP_DIR):  # pragma: no cover
    os.makedirs(BACKUP_DIR)
if not os.path.exists(LOG_DIR):  # pragma: no cover
    os.makedirs(LOG_DIR)

# Setup logging.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logfile_handler = logging.FileHandler(LOGFILE)
log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s", datefmt="%m/%d/%Y %H:%M:%S"
)
logfile_handler.setFormatter(log_formatter)
logger.addHandler(logfile_handler)
logger.addHandler(logging.StreamHandler())


def find_device() -> Optional[str]:
    """Return the location on the filesystem for the connected CircuitPython device.

    This is based upon how Mu discovers this information.
    :return: The path to the device on the local filesystem.
    """
    device_dir = None
    # Attempt to find the path on the filesystem that represents the plugged in
    # CIRCUITPY board.
    if os.name == "posix":
        # Linux / OSX
        for mount_command in ["mount", "/sbin/mount"]:
            try:
                mount_output = check_output(mount_command).splitlines()  # noqa: S603
                mounted_volumes = [x.split()[2] for x in mount_output]
                for volume in mounted_volumes:
                    if volume.endswith(b"CIRCUITPY"):
                        device_dir = volume.decode("utf-8")
            except FileNotFoundError:
                continue
    else:
        # No support for unknown operating systems.
        raise NotImplementedError(f"OS {os.name!r} not supported.")
    return device_dir


class DeviceCommand(click.Command):
    """Options shared by commands that need a valid device."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a command with standard options."""
        super().__init__(*args, **kwargs)
        self.params.insert(
            0,
            click.Option(
                ("-d", "--device"),
                required=True,
                type=click.Path(exists=True, file_okay=False, writable=True),
                default=find_device(),
                help="CIRCUITPY path",
            ),
        )


@click.group()
@click.version_option()
def main() -> None:
    """Manager for CircuitPython deployment."""


@main.command()
def list() -> None:
    """List backups that can be restored."""
    recent_back_limit = 5
    archive_files = find_archive_files()
    recent_files = archive_files[-recent_back_limit:]
    recent_files_count = len(recent_files)

    logger.info("Backups:")
    for index, archive in enumerate(recent_files):
        file_path = Path(archive)
        file_name = file_path.name
        mtime = file_path.stat().st_mtime
        mtime_dt = datetime.datetime.fromtimestamp(mtime)
        logger.info(
            f"{recent_files_count - index} - {mtime_dt:%Y-%m-%d %H:%M:%S} - {file_name}"
        )


@main.command(cls=DeviceCommand)
@click.option(
    "-a", "--archive", default=1, type=int, help="number of backup to restore"
)
def restore(device: str, archive: int) -> None:
    """Restore a backup."""
    archive_files = find_archive_files()
    if not archive_files:
        logger.error("No backup found to restore.")
        sys.exit(1)

    # Find the backup
    try:
        archive_file = archive_files[-archive]
    except IndexError:
        logger.error("Backup not found.")
        sys.exit(1)

    logger.info(f"Restoring {archive_file}")

    shutil.unpack_archive(archive_file, device)


def find_archive_files() -> List[str]:
    """Find archives in the backup directory, sorted alphabetically."""
    return sorted(glob.glob(glob.escape(BACKUP_DIR) + "/*.tar.bz2"))


def backup(device: str) -> None:
    """Backup up the device directory."""
    now = datetime.datetime.now()
    archive_file = os.path.join(BACKUP_DIR, f"archive-{now:%Y%m%d_%H%M%S}")

    logger.info(f"Archiving to {archive_file}.tar.bz2")
    shutil.make_archive(archive_file, "bztar", device, ".")


@main.command(cls=DeviceCommand)
@click.option(
    "-s",
    "--source",
    default="src",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True),
    help="directory to deploy",
)
def deploy(device: str, source: str) -> None:
    """Copy the source directory to the device directory."""
    backup(device)
    logger.info(f"Deploying {source} to {device}")
    copy_tree(source, device, update=1)


if __name__ == "__main__":
    main(prog_name="circman")  # pragma: no cover
