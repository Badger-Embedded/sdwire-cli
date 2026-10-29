"""SD card backed by a sparse image file."""

import os
import tempfile
from dataclasses import dataclass


@dataclass
class SimSdCard:
    size_mib: int = 16
    write_protected: bool = False
    image: str | None = None

    @property
    def sectors(self) -> int:
        return self.size_mib * 2048

    def materialize(self, directory: str) -> str:
        """Create the image file on first use and return its path."""
        if self.image is None:
            fd, self.image = tempfile.mkstemp(
                prefix="card-", suffix=".img", dir=directory
            )
            os.ftruncate(fd, self.size_mib * 1024 * 1024)
            os.close(fd)
        return self.image
