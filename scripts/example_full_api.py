"""Comprehensive examples for PyPureLink Matrix API usage."""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypurelinkmatrix import PureLinkClient  # noqa: E402
from pypurelinkmatrix.exceptions import DeviceError  # noqa: E402


def example_video_control():
    """Example: Video matrix switching and preset management."""
    print("\n" + "=" * 60)
    print("EXAMPLE: VIDEO CONTROL")
    print("=" * 60)

    with PureLinkClient(host="192.168.1.100") as client:
        if not client.login("admin", "password"):
            print("❌ Authentication failed")
            return

        print("✓ Connected to device")

        try:
            # Switch Input 2 to Output 1
            print("\n1. Routing Input 2 to Output 1...")
            client.video.switch_matrix(output=1, input_port=2)

            # Route same input to all outputs
            print("2. Routing Input 3 to all outputs...")
            client.video.switch_matrix(output=0, input_port=3)

            # Save current configuration to preset
            print("3. Saving current configuration to Preset 1...")
            client.video.save_preset(preset_num=1)

            # Recall a preset
            print("4. Recalling Preset 2...")
            client.video.recall_preset(preset_num=2)

            # Rename ports for better organization
            print("5. Renaming input ports...")
            client.video.rename_input(1, "Camera_Main")
            client.video.rename_input(2, "Laptop_Presenter")
            client.video.rename_input(3, "Backup_Input")
            client.video.rename_input(4, "Document_Camera")

            print("6. Renaming output ports...")
            client.video.rename_output(1, "MainDisplay")
            client.video.rename_output(2, "SecondDisplay")

            print("7. Renaming presets...")
            client.video.rename_preset(1, "Conference")
            client.video.rename_preset(2, "Presentation")

            print("\n✓ All video operations completed successfully")

        except DeviceError as e:
            print(f"❌ Device error: {e}")


def example_audio_control():
    """Example: Audio output configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE: AUDIO CONTROL")
    print("=" * 60)

    with PureLinkClient(host="192.168.1.100") as client:
        if not client.login("admin", "password"):
            print("❌ Authentication failed")
            return

        print("✓ Connected to device")

        try:
            # Enable HDMI audio on Output 1
            print("\n1. Enabling HDMI audio on Output 1...")
            client.audio.set_hdmi_output(output=1, enabled=True)

            # Enable de-embedded audio on Output 2
            print("2. Enabling de-embedded audio on Output 2...")
            client.audio.set_de_embed_output(output=2, enabled=True)

            # Disable HDMI on all outputs
            print("3. Disabling HDMI audio on all outputs...")
            client.audio.set_hdmi_output(output=0, enabled=False)

            # Re-enable on specific outputs
            print("4. Enabling HDMI on Output 3 and 4...")
            client.audio.set_hdmi_output(output=3, enabled=True)
            client.audio.set_hdmi_output(output=4, enabled=True)

            print("\n✓ All audio operations completed successfully")

        except DeviceError as e:
            print(f"❌ Device error: {e}")


def example_edid_control():
    """Example: EDID profile configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE: EDID CONTROL")
    print("=" * 60)

    with PureLinkClient(host="192.168.1.100") as client:
        if not client.login("admin", "password"):
            print("❌ Authentication failed")
            return

        print("✓ Connected to device")

        try:
            # Set EDID profiles for inputs
            print("\n1. Setting EDID profiles for inputs...")
            client.edid.set_input_edid(input_num=1, edid_source=1)  # 4K60 LPCM
            client.edid.set_input_edid(input_num=2, edid_source=4)  # 1080P60
            client.edid.set_input_edid(input_num=3, edid_source=5)  # 4K60 DTS

            # Set same EDID on all inputs
            print("2. Setting Default 4K30 profile on all inputs...")
            client.edid.set_input_edid(input_num=0, edid_source=3)

            # Copy EDID profiles to user storage
            print("3. Copying Default1 to User1...")
            client.edid.set_user_edid(source_profile=1, destination=1)

            print("4. Copying Default4 to all user slots...")
            client.edid.set_user_edid(source_profile=4, destination=0)

            # Copy from output to input
            print("5. Copying Output 1 EDID to User2...")
            client.edid.set_user_edid(source_profile=13, destination=2)

            print("\n✓ All EDID operations completed successfully")

        except DeviceError as e:
            print(f"❌ Device error: {e}")


def example_network_control():
    """Example: Network configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE: NETWORK CONTROL")
    print("=" * 60)

    with PureLinkClient(host="192.168.1.100") as client:
        if not client.login("admin", "password"):
            print("❌ Authentication failed")
            return

        print("✓ Connected to device")

        try:
            # Configure static IP
            print("\n1. Configuring static IP address...")
            client.network.configure_static_ip(
                ip_address="192.168.1.150",
                subnet_mask="255.255.255.0",
                gateway="192.168.1.1",
            )

            # Enable DHCP
            print("2. Enabling DHCP...")
            client.network.enable_dhcp()

            # Back to static IP
            print("3. Re-configuring static IP...")
            client.network.configure_static_ip(
                ip_address="192.168.1.100",
                subnet_mask="255.255.255.0",
                gateway="192.168.1.1",
            )

            print("\n✓ All network operations completed successfully")
            print("⚠️  Device may need to reconnect with new network settings")

        except DeviceError as e:
            print(f"❌ Device error: {e}")
        except ValueError as e:
            print(f"❌ Invalid network configuration: {e}")


def example_system_control():
    """Example: System management operations."""
    print("\n" + "=" * 60)
    print("EXAMPLE: SYSTEM CONTROL")
    print("=" * 60)

    with PureLinkClient(host="192.168.1.100") as client:
        if not client.login("admin", "password"):
            print("❌ Authentication failed")
            return

        print("✓ Connected to device")

        try:
            # Change password
            print("\n1. Changing password for admin user...")
            client.system.change_password(
                username="admin",
                password="newpass123",
            )

            # Create new user
            print("2. Creating new user 'operator'...")
            client.system.change_password(
                username="operator",
                password="operator_pass",
            )

            # NOTE: Reboot and factory reset examples commented out
            # as they will disconnect the device

            # print("3. Rebooting device...")
            # client.system.reboot()

            # print("4. Performing factory reset (common settings)...")
            # client.system.factory_reset_common()

            # print("5. Performing factory reset (all settings)...")
            # client.system.factory_reset_all()

            print("\n✓ All system operations completed successfully")
            print("⚠️  Remember new password for next login: newpass123")

        except DeviceError as e:
            print(f"❌ Device error: {e}")
        except ValueError as e:
            print(f"❌ Invalid input: {e}")


def example_combined_workflow():
    """Example: Realistic workflow combining multiple operations."""
    print("\n" + "=" * 60)
    print("EXAMPLE: COMBINED WORKFLOW - Conference Setup")
    print("=" * 60)

    with PureLinkClient(host="192.168.1.100") as client:
        if not client.login("admin", "password"):
            print("❌ Authentication failed")
            return

        print("✓ Connected to device")
        print("\nSetting up device for video conference...\n")

        try:
            # Step 1: Configure video routing
            print("Step 1: Configuring video routing")
            print("  - Routing Presenter Laptop to Main Display")
            client.video.switch_matrix(output=1, input_port=1)
            print("  - Routing Document Camera to Secondary Display")
            client.video.switch_matrix(output=2, input_port=2)
            print("  - Routing Backup to Output 3")
            client.video.switch_matrix(output=3, input_port=3)

            # Step 2: Configure audio
            print("\nStep 2: Configuring audio")
            print("  - Enabling HDMI audio on all outputs")
            client.audio.set_hdmi_output(output=0, enabled=True)

            # Step 3: Configure EDID
            print("\nStep 3: Setting up EDID profiles")
            print("  - Setting 4K60 LPCM profile on all inputs")
            client.edid.set_input_edid(input_num=0, edid_source=1)

            # Step 4: Configure naming
            print("\nStep 4: Configuring port names")
            client.video.rename_input(1, "Presenter_Laptop")
            client.video.rename_input(2, "Document_Cam")
            client.video.rename_input(3, "Backup_HDMI")
            client.video.rename_output(1, "Main_Screen")
            client.video.rename_output(2, "Secondary_Display")
            client.video.rename_output(3, "Overflow")

            # Step 5: Save as preset
            print("\nStep 5: Saving configuration as preset")
            client.video.rename_preset(1, "Conference_Setup")
            client.video.save_preset(preset_num=1)

            print("\n✓ Conference setup completed!")
            print("\nDevice Configuration:")
            print("  Input 1 (Presenter Laptop) → Output 1 (Main Screen)")
            print("  Input 2 (Document Camera) → Output 2 (Secondary)")
            print("  Input 3 (Backup) → Output 3 (Overflow)")
            print("  Audio: HDMI enabled on all outputs")
            print("  Saved as Preset 1 (Conference_Setup)")

        except DeviceError as e:
            print(f"❌ Device error: {e}")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("# PyPureLink Matrix - Comprehensive API Examples")
    print("#" * 60)

    examples = [
        ("Video Control", example_video_control),
        ("Audio Control", example_audio_control),
        ("EDID Control", example_edid_control),
        ("Network Control", example_network_control),
        ("System Control", example_system_control),
        ("Combined Workflow", example_combined_workflow),
    ]

    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n" + "-" * 60)
    print("Note: Update IP address and credentials in examples before running")
    print("Examples assume device is reachable at 192.168.1.100")
    print("-" * 60)

    # Uncomment the example you want to run:
    # example_video_control()
    # example_audio_control()
    # example_edid_control()
    # example_network_control()
    # example_system_control()
    example_combined_workflow()

    print("\n" + "#" * 60)
    print("# Examples completed!")
    print("#" * 60)


if __name__ == "__main__":
    main()
