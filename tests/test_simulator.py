"""Tests for PureLink Matrix Simulator."""

import pytest
from pypurelinkmatrix.simulator.core import MatrixSimulator


@pytest.fixture
def simulator():
    """Fixture for MatrixSimulator instance."""
    return MatrixSimulator()


def test_initialization(simulator):
    """Test default simulator state."""
    assert simulator.ip == "192.168.1.168"
    assert simulator.video_mx == [1, 1, 1, 1]
    assert simulator.mcu_version == "V1.0.0"


def test_switch_video_matrix(simulator):
    """Test switching video matrix."""
    simulator.process_command("#video_d out1 matrix=2")
    assert simulator.video_mx[0] == 2
    assert simulator.video_mx[1] == 1

    # Test switch all
    simulator.process_command("#video_d out256 matrix=3")
    assert simulator.video_mx == [3, 3, 3, 3]


def test_preset_management(simulator):
    """Test saving and recalling presets."""
    # Set custom routing
    simulator.process_command("#video_d out1 matrix=4")

    # Save preset 1
    simulator.process_command("#preset:1 exe=1")
    assert simulator.presets[1] == [4, 1, 1, 1]

    # Change routing
    simulator.process_command("#video_d out1 matrix=1")
    assert simulator.video_mx[0] == 1

    # Recall preset 1
    simulator.process_command("#preset:1 exe=0")
    assert simulator.video_mx == [4, 1, 1, 1]


def test_ip_configuration(simulator):
    """Test IP configuration command."""
    simulator.process_command("#ip ip=10.0.0.1 mask=255.0.0.0 gw=10.0.0.254")
    assert simulator.ip == "10.0.0.1"
    assert simulator.mask == "255.0.0.0"
    assert simulator.gw == "10.0.0.254"


def test_reset(simulator):
    """Test simulator reset."""
    simulator.process_command("#video_d out256 matrix=4")
    assert simulator.video_mx == [4, 4, 4, 4]

    simulator.process_command("#factory1")
    assert simulator.video_mx == [1, 1, 1, 1]
    assert simulator.ip == "192.168.1.168"


def test_binary_data(simulator):
    """Test generation of binary status data."""
    data = simulator.get_binary_data()
    assert isinstance(data, bytes)
    assert len(data) > 16  # Header + data
