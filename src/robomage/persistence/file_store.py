"""
File storage management for diffraction data files.

Handles persistent storage of .chi and .xy files on disk.
"""

import shutil
from pathlib import Path

from robomage.data.loaders import load_chi_file, load_xy_file
from robomage.data.models import DiffractionData

# Default file store location
DEFAULT_STORE_PATH = Path.home() / ".robomage" / "files"


class FileStore:
    """
    Manages persistent storage of diffraction data files.

    Files are organized by session in the file store directory:
    ~/.robomage/files/session_1/file1.chi
    ~/.robomage/files/session_2/file2.xy
    """

    def __init__(self, store_path: Path | str | None = None):
        """
        Initialize file store.

        Args:
            store_path: Root directory for file storage.
                       Defaults to ~/.robomage/files/
        """
        if store_path is None:
            store_path = DEFAULT_STORE_PATH

        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

    def store_file(self, session_id: int, filename: str, data: DiffractionData) -> Path:
        """
        Store diffraction data file.

        Args:
            session_id: ID of the session this file belongs to
            filename: Original filename
            data: DiffractionData object to store

        Returns:
            Path to stored file

        Example:
            >>> store = FileStore()
            >>> data = load_test_data()
            >>> path = store.store_file(1, "sample.chi", data)
            >>> print(path)
            ~/.robomage/files/session_1/sample.chi
        """
        # Create session directory
        session_dir = self.store_path / f"session_{session_id}"
        session_dir.mkdir(exist_ok=True)

        # Generate unique filename (handle duplicates)
        stored_path = session_dir / filename
        counter = 1
        while stored_path.exists():
            name = Path(filename).stem
            ext = Path(filename).suffix
            stored_path = session_dir / f"{name}_{counter}{ext}"
            counter += 1

        # Write data to file in simple two-column format
        # This is compatible with load_chi_file
        with open(stored_path, "w") as f:
            f.write("# Q (A^-1)  Intensity\n")
            for q, intensity in zip(data.q_values, data.intensities, strict=False):
                f.write(f"{q}  {intensity}\n")

        return stored_path

    def load_file(self, stored_path: Path | str) -> DiffractionData:
        """
        Load diffraction data from stored file.

        Args:
            stored_path: Path to stored file

        Returns:
            DiffractionData object

        Example:
            >>> store = FileStore()
            >>> data = store.load_file("~/.robomage/files/session_1/sample.chi")
        """
        stored_path = Path(stored_path)

        # Use appropriate loader based on file extension
        if stored_path.suffix.lower() == ".chi":
            return load_chi_file(str(stored_path))
        elif stored_path.suffix.lower() == ".xy":
            return load_xy_file(str(stored_path))
        else:
            # Default to .chi loader for unknown extensions
            return load_chi_file(str(stored_path))

    def delete_session_files(self, session_id: int) -> None:
        """
        Delete all files for a session.

        Args:
            session_id: ID of the session to delete files for

        Example:
            >>> store = FileStore()
            >>> store.delete_session_files(1)  # Deletes all files in session 1
        """
        session_dir = self.store_path / f"session_{session_id}"
        if session_dir.exists():
            shutil.rmtree(session_dir)


# Global file store instance (singleton pattern)
_file_store: FileStore | None = None


def get_file_store(store_path: Path | str | None = None) -> FileStore:
    """
    Get or create the global file store instance.

    Args:
        store_path: Path to file storage directory (only used on first call)

    Returns:
        FileStore instance

    Example:
        >>> store = get_file_store()
        >>> path = store.store_file(1, "sample.chi", data)
    """
    global _file_store
    if _file_store is None:
        _file_store = FileStore(store_path)
    return _file_store
