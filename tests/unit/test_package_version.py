"""Package versions follow installed metadata and tolerate source-only imports."""

import runpy
from importlib import metadata

import collaborative_hill


def test_version_follows_distribution_metadata(tmp_path, monkeypatch):
    distribution = tmp_path / "collaborative_hill-9.8.7.dist-info"
    distribution.mkdir()
    (distribution / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: collaborative-hill\nVersion: 9.8.7\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    package = runpy.run_path(collaborative_hill.__file__)

    assert package["__version__"] == "9.8.7"


def test_source_only_import_has_explicit_unknown_version(monkeypatch):
    def missing_distribution(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing_distribution)

    package = runpy.run_path(collaborative_hill.__file__)

    assert package["__version__"] == "0+unknown"
