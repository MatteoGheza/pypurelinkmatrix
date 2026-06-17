"""Video matrix control API."""

import logging

from ..exceptions import DeviceError
from ..http_client import post_request

logger = logging.getLogger(__name__)


class VideoAPI:
    """API for video matrix control operations."""

    def __init__(self, session, base_url: str, state=None):
        """Initialize video API.

        Args:
            session: Requests session for HTTP communication
            base_url: Base URL of the device
            state: Optional reference to DeviceState for updating local state
        """
        self.session = session
        self.base_url = base_url
        self.endpoint = "video_set"
        self.state = state

    def switch_matrix(self, output_port: int, input_port: int, timeout: int = 30) -> bool:
        """Switch video matrix input to output.

        Routes an input to one or more outputs. Output 0 means all outputs.

        Args:
            output_port: Output number (1-4 for specific, 0 for all outputs)
            input_port: Input number (1-4)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            DeviceError: If operation fails

        Example:
            >>> api.switch_matrix(1, 2)  # Route Input 2 to Output 1
            >>> api.switch_matrix(0, 3)  # Route Input 3 to all outputs
        """
        if not 0 <= output_port <= 4:
            raise ValueError("Output must be 0 (all) or 1-4")
        if not 1 <= input_port <= 4:
            raise ValueError("Input port must be 1-4")

        # Convert output 0 to 256 for all outputs
        device_output = 256 if output_port == 0 else output_port

        try:
            cmd = f"#video_d out{device_output} matrix={input_port}"
            logger.debug(f"Switching matrix: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(f"Routed Input {input_port} to Output {output_port}")

            # Update local state if available
            if self.state and output_port != 0:
                self.state.video._set_output_input(output_port, input_port)
            elif self.state and output_port == 0:
                # Update all outputs
                for out in range(1, 5):
                    self.state.video._set_output_input(out, input_port)

            return True

        except Exception as e:
            logger.error(f"Failed to switch matrix: {e}")
            raise DeviceError(f"Matrix switch failed: {e}") from e

    def save_preset(self, preset_num: int, timeout: int = 30) -> bool:
        """Save current matrix configuration to a preset.

        Saves the current input/output routing to a numbered preset (1-8).

        Args:
            preset_num: Preset number (1-8)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If preset number is invalid
            DeviceError: If operation fails

        Example:
            >>> api.save_preset(1)  # Save to Preset 1
        """
        if not 1 <= preset_num <= 8:
            raise ValueError("Preset number must be 1-8")

        try:
            cmd = f"#preset:{preset_num} exe=1"
            logger.debug(f"Saving preset: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(f"Saved configuration to Preset {preset_num}")
            return True

        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
            raise DeviceError(f"Preset save failed: {e}") from e

    def recall_preset(self, preset_num: int, timeout: int = 30) -> bool:
        """Recall a saved preset configuration.

        Restores a previously saved preset (1-8).

        Args:
            preset_num: Preset number (1-8)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If preset number is invalid
            DeviceError: If operation fails

        Example:
            >>> api.recall_preset(1)  # Load Preset 1
        """
        if not 1 <= preset_num <= 8:
            raise ValueError("Preset number must be 1-8")

        try:
            cmd = f"#preset:{preset_num} exe=0"
            logger.debug(f"Recalling preset: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(f"Recalled Preset {preset_num}")
            return True

        except Exception as e:
            logger.error(f"Failed to recall preset: {e}")
            raise DeviceError(f"Preset recall failed: {e}") from e

    def rename_input(self, input_num: int, name: str, timeout: int = 30) -> bool:
        """Rename an input port.

        Sets a custom name for an input port (max 15 characters).

        Args:
            input_num: Input number (1-4)
            name: New name (1-15 alphanumeric/underscore characters)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If input number or name format is invalid
            DeviceError: If operation fails

        Example:
            >>> api.rename_input(1, "Camera_Main")
        """
        if not 1 <= input_num <= 4:
            raise ValueError("Input number must be 1-4")

        return self._rename_port(
            input_num, name, name_index_offset=0, port_type="Input", timeout=timeout
        )

    def rename_output(self, output_num: int, name: str, timeout: int = 30) -> bool:
        """Rename an output port.

        Sets a custom name for an output port (max 15 characters).

        Args:
            output_num: Output number (1-4)
            name: New name (1-15 alphanumeric/underscore characters)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If output number or name format is invalid
            DeviceError: If operation fails

        Example:
            >>> api.rename_output(1, "Display_Main")
        """
        if not 1 <= output_num <= 4:
            raise ValueError("Output number must be 1-4")

        return self._rename_port(
            output_num, name, name_index_offset=4, port_type="Output", timeout=timeout
        )

    def rename_preset(self, preset_num: int, name: str, timeout: int = 30) -> bool:
        """Rename a preset.

        Sets a custom name for a preset (max 15 characters).

        Args:
            preset_num: Preset number (1-8)
            name: New name (1-15 alphanumeric/underscore characters)
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If preset number or name format is invalid
            DeviceError: If operation fails

        Example:
            >>> api.rename_preset(1, "Conference")
        """
        if not 1 <= preset_num <= 8:
            raise ValueError("Preset number must be 1-8")

        return self._rename_port(
            preset_num, name, name_index_offset=8, port_type="Preset", timeout=timeout
        )

    def _rename_port(
        self, port_num: int, name: str, name_index_offset: int, port_type: str, timeout: int
    ) -> bool:
        """Generic method to rename a port or preset.

        Args:
            port_num: Port or preset number
            name: New name
            name_index_offset: Offset for the name index calculation
            port_type: Type of port ("Input", "Output", or "Preset")
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            DeviceError: If operation fails
        """
        self._validate_port_name(name)

        try:
            name_index = port_num + name_index_offset - 1
            cmd = f"#name{name_index} str={name}"
            logger.debug(f"Renaming {port_type.lower()}: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(f"Renamed {port_type} {port_num} to '{name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to rename {port_type.lower()}: {e}")
            raise DeviceError(f"{port_type} rename failed: {e}") from e

    @staticmethod
    def _validate_port_name(name: str) -> None:
        """Validate port name format.

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

        pattern = re.compile(r"^[a-zA-Z0-9_]{1,15}$")
        if not pattern.match(name):
            raise ValueError("Name must contain only letters, numbers, and underscores")
