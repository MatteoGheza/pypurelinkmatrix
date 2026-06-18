"""Unit tests for device models."""

from pypurelinkmatrix.models import (
    AudioOutputState,
    AudioState,
    DeviceState,
    EDIDState,
    NetworkState,
    PortNames,
    VideoMatrixState,
)


class TestModels:
    """Tests for device models."""

    def test_video_matrix_state(self):
        """Test VideoMatrixState."""
        state = VideoMatrixState()

        # Test _set_output_input
        state._set_output_input(1, 2)
        assert state.output_1_input == 2
        state._set_output_input(4, 1)
        assert state.output_4_input == 1
        state._set_output_input(5, 1)  # Invalid output

        # Test get_output_input
        assert state.get_output_input(1) == 2
        assert state.get_output_input(4) == 1
        assert state.get_output_input(5) == 0  # Invalid output

    def test_audio_state(self):
        """Test AudioState."""
        state = AudioState()

        # Test get_output
        output1 = state.get_output(1)
        assert isinstance(output1, AudioOutputState)
        assert output1.output_num == 1

        output4 = state.get_output(4)
        assert isinstance(output4, AudioOutputState)
        assert output4.output_num == 4

        assert state.get_output(5) is None  # Invalid output

    def test_edid_state(self):
        """Test EDIDState."""
        state = EDIDState()

        # Test _set_input_edid
        state._set_input_edid(1, 10)
        assert state.input_1_edid == 10
        state._set_input_edid(4, 20)
        assert state.input_4_edid == 20
        state._set_input_edid(5, 30)  # Invalid input

        # Test get_input_edid
        assert state.get_input_edid(1) == 10
        assert state.get_input_edid(4) == 20
        assert state.get_input_edid(5) == 0  # Invalid input

    def test_port_names(self):
        """Test PortNames."""
        names = PortNames()

        # Test set_input_name
        names.set_input_name(1, "NewInput1")
        assert names.input_names[0] == "NewInput1"
        names.set_input_name(5, "Invalid")  # Invalid index

        # Test set_output_name
        names.set_output_name(1, "NewOutput1")
        assert names.output_names[0] == "NewOutput1"
        names.set_output_name(5, "Invalid")  # Invalid index

        # Test set_preset_name
        names.set_preset_name(1, "NewPreset1")
        assert names.preset_names[0] == "NewPreset1"
        names.set_preset_name(9, "Invalid")  # Invalid index

    def test_device_state(self):
        """Test DeviceState defaults."""
        state = DeviceState()
        assert isinstance(state.video, VideoMatrixState)
        assert isinstance(state.audio, AudioState)
        assert isinstance(state.edid, EDIDState)
        assert isinstance(state.network, NetworkState)
        assert isinstance(state.port_names, PortNames)
        assert state.mcu_version == "Unknown"
