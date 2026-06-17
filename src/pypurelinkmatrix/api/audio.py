"""Audio output control API."""

import logging

from ..exceptions import DeviceError
from ..http_client import post_request

logger = logging.getLogger(__name__)


class AudioAPI:
    """API for audio output control operations."""

    def __init__(self, session, base_url: str, state=None):
        """Initialize audio API.

        Args:
            session: Requests session for HTTP communication
            base_url: Base URL of the device
            state: Optional reference to DeviceState for updating local state
        """
        self.session = session
        self.base_url = base_url
        self.endpoint = "audio_set"
        self.state = state

    def set_hdmi_output(self, output: int, enabled: bool, timeout: int = 30) -> bool:
        """Enable/disable HDMI audio output.

        Args:
            output: Output number (1-4 for specific, 0 for all)
            enabled: True to enable, False to disable
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If output number is invalid
            DeviceError: If operation fails

        Example:
            >>> api.set_hdmi_output(1, True)  # Enable HDMI on Output 1
            >>> api.set_hdmi_output(0, False)  # Disable HDMI on all outputs
        """
        if not 0 <= output <= 4:
            raise ValueError("Output must be 0 (all) or 1-4")

        return self._send_audio_command(output, 0, enabled, timeout)

    def set_de_embed_output(self, output: int, enabled: bool, timeout: int = 30) -> bool:
        """Enable/disable de-embedded audio output.

        Args:
            output: Output number (1-4 for specific, 0 for all)
            enabled: True to enable, False to disable
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If output number is invalid
            DeviceError: If operation fails

        Example:
            >>> api.set_de_embed_output(2, True)  # Enable de-embed on Output 2
        """
        if not 0 <= output <= 4:
            raise ValueError("Output must be 0 (all) or 1-4")

        return self._send_audio_command(output, 1, enabled, timeout)

    def _send_audio_command(self, output: int, mode: int, enabled: bool, timeout: int) -> bool:
        """Send audio control command to device.

        Args:
            output: Output number (0 = all, 1-4 = specific)
            mode: 0 = HDMI, 1 = De-Embed
            enabled: True to enable, False to disable
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            DeviceError: If operation fails
        """
        try:
            # Convert boolean to device value (1 = enable, 0 = disable)
            onoff = 1 if enabled else 0
            mode_str = "hdmi" if mode == 0 else "dec"

            # For all outputs, use output 0
            device_output = output

            cmd = f"#audio_d out{device_output} {mode_str}={onoff}"
            logger.debug(f"Sending audio command: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()

            output_label = f"Output {output}" if output != 0 else "All outputs"
            mode_label = "HDMI" if mode == 0 else "De-Embed"
            status = "enabled" if enabled else "disabled"
            logger.info(f"{mode_label} {status} on {output_label}")

            # Update local state if available
            if self.state and output != 0:
                audio_output = self.state.audio.get_output(output)
                if audio_output:
                    if mode == 0:
                        audio_output.hdmi_enabled = enabled
                    else:
                        audio_output.de_embed_enabled = enabled
            elif self.state and output == 0:
                # Update all outputs
                for out in range(1, 5):
                    audio_output = self.state.audio.get_output(out)
                    if audio_output:
                        if mode == 0:
                            audio_output.hdmi_enabled = enabled
                        else:
                            audio_output.de_embed_enabled = enabled

            return True

        except Exception as e:
            logger.error(f"Failed to set audio output: {e}")
            raise DeviceError(f"Audio output control failed: {e}") from e
