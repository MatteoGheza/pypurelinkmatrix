"""EDID control API."""

import logging

from ..exceptions import DeviceError
from ..http_client import post_request

logger = logging.getLogger(__name__)


class EDIDProfile:
    """EDID profile definitions."""

    PROFILES = {
        1: "Default1:4K60 444-LPCM: 2.0, HDR:HLG",
        2: "Default2:4K60 420-LPCM: 2.0, HDR:None",
        3: "Default3:4K30 444-LPCM: 2.0, HDR:None",
        4: "Default4:1080P60 444-LPCM: 2.0, HDR:None",
        5: "Default5:4K60 444-DTS: 5.1, HDR:HLG",
        6: "Default6:4K60 420-DTS: 5.1, HDR:None",
        7: "Default7:4K30 444-DTS: 5.1, HDR:None",
        8: "Default8:1080P60 444-DTS: 5.1, HDR:None",
        9: "User1",
        10: "User2",
        11: "User3",
        12: "User4",
        13: "Output1",
        14: "Output2",
        15: "Output3",
        16: "Output4",
        17: "Temp1",
    }


class EDIDAPI:
    """API for EDID control operations."""

    def __init__(self, session, base_url: str):
        """Initialize EDID API.

        Args:
            session: Requests session for HTTP communication
            base_url: Base URL of the device
        """
        self.session = session
        self.base_url = base_url
        self.endpoint = "input.set"

    def set_input_edid(self, input_num: int, edid_source: int, timeout: int = 30) -> bool:
        """Set EDID profile for an input.

        Available EDID sources:
        - 1-8: Default profiles (various resolutions/audio/HDR combinations)
        - 9-12: User-defined EDID profiles
        - 13-16: Copy from output
        - 17: Temp storage

        Args:
            input_num: Input number (1-4, 0 for all)
            edid_source: EDID profile number (1-17)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If input number or EDID source is invalid
            DeviceError: If operation fails

        Example:
            >>> api.set_input_edid(1, 1)  # Set Default1 profile on Input 1
            >>> api.set_input_edid(0, 4)  # Set Default4 on all inputs
        """
        if not 0 <= input_num <= 4:
            raise ValueError("Input number must be 0 (all) or 1-4")
        if not 1 <= edid_source <= 17:
            raise ValueError("EDID source must be 1-17")

        try:
            # Determine EDID type and index based on source
            if edid_source <= 8:
                # Default profiles (type 0)
                edid_type = 0
                edid_index = edid_source
            elif edid_source <= 12:
                # User profiles (type 1)
                edid_type = 1
                edid_index = edid_source - 8
            elif edid_source <= 16:
                # Output profiles (type 2)
                edid_type = 2
                edid_index = edid_source - 12
            else:
                # Temp profile (type 4)
                edid_type = 4
                edid_index = 1

            cmd = f"#edid in{input_num} cfg={edid_type}/{edid_index}"
            logger.debug(f"Setting input EDID: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()

            input_label = f"Input {input_num}" if input_num != 0 else "All inputs"
            profile_name = EDIDProfile.PROFILES.get(edid_source, f"Profile {edid_source}")
            logger.info(f"Set {input_label} EDID to {profile_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to set input EDID: {e}")
            raise DeviceError(f"Input EDID configuration failed: {e}") from e

    def set_user_edid(self, source_profile: int, destination: int, timeout: int = 30) -> bool:
        """Copy EDID profile to user storage.

        Copy a source EDID profile (default, user, output, or temp) to a
        user storage location (User1-User4).

        Args:
            source_profile: Source EDID profile number (1-17)
            destination: Destination user slot (1-4, 0 for all user slots)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If parameters are invalid
            DeviceError: If operation fails

        Example:
            >>> api.set_user_edid(1, 1)  # Copy Default1 to User1
            >>> api.set_user_edid(2, 0)  # Copy Default2 to all user slots
        """
        if not 1 <= source_profile <= 17:
            raise ValueError("Source profile must be 1-17")
        if not 0 <= destination <= 4:
            raise ValueError("Destination must be 0 (all) or 1-4")

        try:
            # Determine source EDID type and index
            if source_profile <= 8:
                edid_type = 0
                edid_index = source_profile
            elif source_profile <= 12:
                edid_type = 1
                edid_index = source_profile - 8
            elif source_profile <= 16:
                edid_type = 2
                edid_index = source_profile - 12
            else:
                edid_type = 4
                edid_index = 1

            cmd = f"#edid user{destination} cfg={edid_type}/{edid_index}"
            logger.debug(f"Setting user EDID: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()

            source_name = EDIDProfile.PROFILES.get(source_profile, f"Profile {source_profile}")
            dest_label = f"User{destination}" if destination != 0 else "All user slots"
            logger.info(f"Copied {source_name} to {dest_label}")

            return True

        except Exception as e:
            logger.error(f"Failed to set user EDID: {e}")
            raise DeviceError(f"User EDID configuration failed: {e}") from e

    def rename_input_port(self, input_num: int, name: str, timeout: int = 30) -> bool:
        """Rename an input port in EDID section.

        Args:
            input_num: Input number (1-4)
            name: New name (max 15 characters)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If parameters are invalid
            DeviceError: If operation fails
        """
        if not 1 <= input_num <= 4:
            raise ValueError("Input number must be 1-4")

        self._validate_name(name)

        try:
            cmd = f"#name{input_num - 1} str={name}"
            logger.debug(f"Renaming input port: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(f"Renamed Input {input_num} to '{name}'")

            return True

        except Exception as e:
            logger.error(f"Failed to rename input port: {e}")
            raise DeviceError(f"Input port rename failed: {e}") from e

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate name format.

        Args:
            name: Name to validate

        Raises:
            ValueError: If name format is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")

        if len(name) > 15:
            raise ValueError("Name must be 15 characters or less")

        import re

        pattern = re.compile(r"^[a-zA-Z0-9_\-]{1,15}$")
        if not pattern.match(name):
            raise ValueError("Name must contain only letters, numbers, underscores, and hyphens")
