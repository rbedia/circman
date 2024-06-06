"""Command-line interface."""

import datetime
import logging
import os
import shutil
import sys
from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import check_output
from typing import Any
from typing import List
from typing import Optional

import click
import platformdirs

appname = "circman"
appauthor = "circman"

DATA_DIR = Path(platformdirs.user_data_dir(appname=appname, appauthor=appauthor))
LOG_DIR = Path(platformdirs.user_log_dir(appname=appname, appauthor=appauthor))
#: The location of the log file for the utility.
LOGFILE = LOG_DIR / "circman.log"
BACKUP_DIR = DATA_DIR / "archives"

# Ensure BACKUP_DIR / LOG_DIR related directories and files exist.
if not BACKUP_DIR.exists():  # pragma: no cover
    BACKUP_DIR.mkdir(parents=True)
if not LOG_DIR.exists():  # pragma: no cover
    LOG_DIR.mkdir(parents=True)

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
                default=lambda: find_device(),
                help="CIRCUITPY path. If not provided, autodiscovery is attempted.",
            ),
        )


@click.group()
@click.version_option()
def main() -> None:
    """Manager for CircuitPython project deployment."""


@main.command()
def list() -> None:  # noqa: A001
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
        mtime_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
        logger.info(
            f"{recent_files_count - index} - {mtime_dt:%Y-%m-%d %H:%M:%S} - {file_name}"
        )


@main.command(cls=DeviceCommand)
@click.option(
    "-a",
    "--archive",
    default=1,
    type=int,
    help="""Number of backup to restore.
    Use the list command to find the backup number.
    Defaults to restoring the most recent backup.""",
)
def restore(device: str, archive: int) -> None:
    """Restore a backup."""
    require_device(device)

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


def find_archive_files() -> List[Path]:
    """Find archives in the backup directory, sorted alphabetically."""
    return sorted(BACKUP_DIR.glob("*.tar.bz2"), key=lambda x: str(x))


def backup(device: str) -> None:
    """Backup up the device directory."""
    now = datetime.datetime.now(datetime.timezone.utc)
    archive_file = BACKUP_DIR / f"archive-{now:%Y%m%d_%H%M%S}"

    logger.info(f"Archiving to {archive_file}.tar.bz2")
    shutil.make_archive(str(archive_file), "bztar", device, ".")


@main.command(cls=DeviceCommand)
@click.option(
    "-s",
    "--source",
    default="src",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True),
    help='Directory to deploy. Defaults to "src".',
)
def deploy(device: str, source: str) -> None:
    """Copy the source directory to the device directory."""
    require_device(device)

    backup(device)
    logger.info(f"Deploying {source} to {device}")
    copy_tree(source, device, update=1)


@main.command(cls=DeviceCommand)
@click.option(
    "-D",
    "--dest",
    default="src",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True),
    help='Destination directory. Defaults to "src".',
)
def sync(device: str, dest: str) -> None:
    """Copy the device directory to the source directory.

    This will overwrite files in dest without prompting and without backup so use
    with caution.
    """
    require_device(device)

    logger.info(f"Copying {device} to {dest}")
    copy_tree(device, dest)


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


def require_device(device: Optional[str]) -> None:
    """Exit if device doesn't have a value."""
    if not device:
        sys.exit(2)  # pragma: no cover


if __name__ == "__main__":
    main(prog_name="circman")  # pragma: no cover
