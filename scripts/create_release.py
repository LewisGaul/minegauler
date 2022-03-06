#!/usr/bin/env python3

import argparse
import enum
import logging
import os
import pathlib
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, List, Optional

import minegauler.app  # To get the version


APP_NAME = "minegauler"


class Platform(enum.Enum):
    WINDOWS = enum.auto()
    LINUX = enum.auto()
    MACOS = enum.auto()

    @classmethod
    def current(cls) -> "Platform":
        if sys.platform.startswith("win"):
            return cls.WINDOWS
        elif sys.platform.startswith("linux"):
            return cls.LINUX
        elif sys.platform.startswith("darwin"):
            return cls.MACOS


class Format(enum.Enum):
    TAR = enum.auto()
    TGZ = enum.auto()
    ZIP = enum.auto()
    PLAIN = enum.auto()

    @classmethod
    def from_str(cls, name: str) -> "Format":
        return getattr(cls, name.upper())

    @classmethod
    def default(cls) -> "Format":
        if Platform.current() is Platform.WINDOWS:
            return cls.ZIP
        else:
            return cls.TGZ

    def extension(self) -> str:
        if self is Format.PLAIN:
            return ""
        else:
            return f".{self.name.lower()}"


def run_pyinstaller(output_dir: pathlib.Path) -> None:
    cmd = [
        # fmt: off
        "pyinstaller",
        "--distpath", str(output_dir),
        "package/minegauler.spec",
        # fmt: on
    ]
    logging.debug("Running command: %s", " ".join(shlex.quote(x) for x in cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise Exception(f"Pyinstaller command with exit code {proc.returncode}")


def create_windows_wrapper(
    src: os.PathLike,
    dest: os.PathLike,
    *,
    cd: Optional[os.PathLike] = None,
    argv: Iterable[str] = (),
    console: bool = False,
) -> None:
    content = []
    if cd:
        content.append(f"CD {cd!s}")
    run_cmd = "CALL" if console else "START"
    argv = [str(src), *argv]
    content.append(f"{run_cmd} {subprocess.list2cmdline(argv)} %*")
    dest = pathlib.Path(dest).with_suffix(".bat")
    with open(dest, "w") as f:
        f.write("\n".join(content))


def create_posix_wrapper(
    src: os.PathLike,
    dest: os.PathLike,
    *,
    cd: Optional[os.PathLike] = None,
    argv: Iterable[str] = (),
    console: bool = False,
) -> None:
    content = ["#!/bin/sh"]
    if cd:
        content.append(f"cd {shlex.quote(str(cd))}")
    argv = [str(src), *argv]
    if not console:
        argv.insert(0, "exec")
    elif argv[0][0] != "/":
        argv[0] = "./" + argv[0]
    content.append(shlex.join(argv) + ' "$@"')
    dest = pathlib.Path(dest).with_suffix(".sh")
    with open(dest, "w") as f:
        f.write("\n".join(content))
    os.chmod(dest, 0o755)


def create_wrapper(
    src: os.PathLike,
    dest: os.PathLike,
    *,
    cd: Optional[os.PathLike] = None,
    argv: Iterable[str] = (),
    console: bool = False,
) -> None:
    if Platform.current() is Platform.WINDOWS:
        create_windows_wrapper(src, dest, cd=cd, argv=argv, console=console)
    else:
        create_posix_wrapper(src, dest, cd=cd, argv=argv, console=console)


def create_package(from_dir: pathlib.Path, dest_dir: pathlib.Path, fmt: Format) -> str:
    # Create outer files.
    shutil.copy2("CHANGELOG.md", from_dir / "CHANGELOG.txt")
    shutil.copy2("LICENSE.txt", from_dir)
    if Platform.current() is Platform.WINDOWS:
        root_filename = "minegauler.bat"
        dist_filename = "minegauler.exe"
        create_windows_wrapper(dist_filename, from_dir / root_filename, cd=APP_NAME)
        create_windows_wrapper(
            "minegauler-bot.exe", from_dir / "minegauler-bot.bat", cd=APP_NAME
        )
    else:
        root_filename = "minegauler.exe"
        dist_filename = "minegauler"
        os.symlink(os.path.join(APP_NAME, dist_filename), from_dir / root_filename)
        os.symlink(os.path.join(APP_NAME, "minegauler-bot"), from_dir / "minegauler-bot")

    with open("package/README.txt.template", "r") as f:
        readme = f.read().format(
            root_filename=root_filename, dist_filename=dist_filename
        )
    with open(from_dir / "README.txt", "w") as f:
        f.write(readme)

    # Copy over and archive at destination.
    os.makedirs(dest_dir, exist_ok=True)
    logging.debug("Creating package in: %s/", dest_dir)
    dest = str(dest_dir / archive_name())
    if fmt is Format.PLAIN:
        shutil.copytree(from_dir, dest, symlinks=True)
        return dest
    if fmt is Format.TGZ:
        shutil_fmt = "gztar"
    else:
        shutil_fmt = fmt.name.lower()
    return shutil.make_archive(dest, shutil_fmt, from_dir)


def archive_name() -> str:
    plat = Platform.current().name.lower()
    arch = platform.machine().lower()
    return f"minegauler-v{minegauler.app.__version__}-{plat}-{arch}"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--format",
        metavar="FMT",
        type=Format.from_str,
        default=Format.default(),
        choices=Format,
        help="output format, one of {}".format(
            ", ".join(
                f.name.lower() + (" (default)" if f is Format.default() else "")
                for f in Format
            )
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="DIR",
        type=pathlib.Path,
        default=pathlib.Path("./"),
        help="output directory, defaults to cwd",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug logging"
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    with tempfile.TemporaryDirectory(prefix="pyinstaller-") as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        run_pyinstaller(tmpdir)
        path = create_package(tmpdir, args.output_dir, args.format)
    logging.info("Created package at %s", path)


if __name__ == "__main__":
    main(sys.argv[1:])
