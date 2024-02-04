"""Test cases for the __main__ module."""

import os
from pathlib import Path
from typing import Iterator
from typing import Tuple
from unittest import mock

import pytest
from click.testing import CliRunner

from circman import __main__


BACKUP_DIR = "backups"
DEST_DIR = "dest"
SRC_DIR = "src"

# Remove the log file handler to prevent logging to disk
__main__.logger.removeHandler(__main__.logfile_handler)


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    with mock.patch("circman.__main__.find_device", return_value=None):
        yield CliRunner()


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.main)
    assert result.exit_code == 0


def test_find_device_posix_exists() -> None:
    """
    Simulate being on os.name == 'posix' and a call to "mount" returns a
    record indicating a connected device.
    """
    with open("tests/mount_exists.txt", "rb") as fixture_file:
        fixture = fixture_file.read()
        with mock.patch("os.name", "posix"):
            with mock.patch("circman.__main__.check_output", return_value=fixture):
                assert __main__.find_device() == "/media/ntoll/CIRCUITPY"


def test_find_device_posix_no_mount_command() -> None:
    """
    When the user doesn't have administrative privileges on OSX then the mount
    command isn't on their path. In which case, check circup uses the more
    explicit /sbin/mount instead.
    """
    with open("tests/mount_exists.txt", "rb") as fixture_file:
        fixture = fixture_file.read()
    mock_check = mock.MagicMock(side_effect=[FileNotFoundError, fixture])
    with mock.patch("os.name", "posix"), mock.patch(
        "circman.__main__.check_output", mock_check
    ):
        assert __main__.find_device() == "/media/ntoll/CIRCUITPY"
        assert mock_check.call_count == 2
        assert mock_check.call_args_list[0][0][0] == "mount"
        assert mock_check.call_args_list[1][0][0] == "/sbin/mount"


def test_find_device_posix_missing() -> None:
    """
    Simulate being on os.name == 'posix' and a call to "mount" returns no
    records associated with an Adafruit device.
    """
    with open("tests/mount_missing.txt", "rb") as fixture_file:
        fixture = fixture_file.read()
        with mock.patch("os.name", "posix"), mock.patch(
            "circman.__main__.check_output", return_value=fixture
        ):
            assert __main__.find_device() is None


def test_find_device_unknown_os() -> None:
    """
    Raises a NotImplementedError if the host OS is not supported.
    """
    with mock.patch("os.name", "foo"):
        with pytest.raises(NotImplementedError) as ex:
            __main__.find_device()
    assert ex.value.args[0] == "OS 'foo' not supported."


def test_list_no_backups(
    runner: CliRunner, mock_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    result = runner.invoke(__main__.main, "list")
    assert result.exit_code == 0
    assert caplog.messages == ["Backups:"]


def test_list_show_backups(
    runner: CliRunner,
    mock_dir: str,
    mock_backups: Tuple[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    result = runner.invoke(__main__.main, "list")
    assert result.exit_code == 0
    assert "Backups:" in caplog.text
    assert mock_backups[0] in caplog.text
    assert mock_backups[1] in caplog.text


def test_restore_no_device(runner: CliRunner, mock_dir: str) -> None:
    result = runner.invoke(__main__.main, "restore")
    assert result.exit_code == 2
    assert "Error: Missing option '-d' / '--device'." in result.output


def test_restore_no_backups(
    runner: CliRunner, mock_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch("shutil.unpack_archive") as mock_unpack:
        result = runner.invoke(__main__.main, ["restore", "-d", DEST_DIR])
        assert result.exit_code == 1
        assert "No backup found to restore." in caplog.text

        mock_unpack.assert_not_called()


def test_restore_backup_not_found(
    runner: CliRunner,
    mock_dir: str,
    mock_backups: Tuple[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with mock.patch("shutil.unpack_archive") as mock_unpack:
        result = runner.invoke(__main__.main, ["restore", "-d", DEST_DIR, "-a", "3"])
        assert result.exit_code == 1
        assert "Backup not found." in caplog.text

        mock_unpack.assert_not_called()


def test_restore_success(
    runner: CliRunner,
    mock_dir: str,
    mock_backups: Tuple[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with mock.patch("shutil.unpack_archive") as mock_unpack:
        result = runner.invoke(__main__.main, ["restore", "-d", DEST_DIR])
        assert result.exit_code == 0
        assert "Restoring" in caplog.text

        mock_unpack.assert_called_with(
            f"{mock_dir}/{BACKUP_DIR}/{mock_backups[1]}", DEST_DIR
        )


def test_restore_success_older(
    runner: CliRunner,
    mock_dir: str,
    mock_backups: Tuple[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with mock.patch("shutil.unpack_archive") as mock_unpack:
        result = runner.invoke(__main__.main, ["restore", "-d", DEST_DIR, "-a", "2"])
        assert result.exit_code == 0
        assert "Restoring" in caplog.text

        mock_unpack.assert_called_with(
            f"{mock_dir}/{BACKUP_DIR}/{mock_backups[0]}", DEST_DIR
        )


def test_deploy_success(
    runner: CliRunner, mock_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch("shutil.make_archive") as mock_archive, mock.patch(
        "circman.__main__.copy_tree"
    ) as mock_copy:
        result = runner.invoke(__main__.main, ["deploy", "-d", DEST_DIR])
        assert result.exit_code == 0
        assert "Archiving" in caplog.text
        assert "Deploying" in caplog.text

        mock_archive.assert_called_once()
        mock_copy.assert_called_with("src", DEST_DIR, update=1)


def test_sync_success(
    runner: CliRunner, mock_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch("circman.__main__.copy_tree") as mock_copy:
        result = runner.invoke(__main__.main, ["sync", "-d", DEST_DIR])
        assert result.exit_code == 0
        assert "Copying" in caplog.text

        mock_copy.assert_called_with(DEST_DIR, "src")


@pytest.fixture
def mock_dir(runner: CliRunner, tmp_path: Path) -> Iterator[str]:
    with runner.isolated_filesystem(temp_dir=tmp_path) as td, mock.patch(
        "circman.__main__.BACKUP_DIR", f"{td}/{BACKUP_DIR}"
    ):
        os.makedirs(f"{td}/{DEST_DIR}")
        os.makedirs(f"{td}/{SRC_DIR}")
        os.makedirs(f"{td}/{BACKUP_DIR}")
        yield td


@pytest.fixture
def mock_backups(mock_dir: str) -> Tuple[str, str]:
    backups = ("archive-20230224_034752.tar.bz2", "archive-20230227_101709.tar.bz2")

    # Create empty files
    for backup in backups:
        open(f"{mock_dir}/{BACKUP_DIR}/{backup}", "a").close()

    return backups
