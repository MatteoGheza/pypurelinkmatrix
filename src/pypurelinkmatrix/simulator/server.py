"""HTTP Server for PureLink Matrix Simulator."""

import logging
import re

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .core import MatrixSimulator, calculate_crc32

logger = logging.getLogger(__name__)

app = FastAPI(title="PureLink Matrix Simulator")
simulator = MatrixSimulator()

# Regex to match timestamped endpoints (e.g., video_set1704283200000)
SET_ENDPOINT_PATTERN = re.compile(
    r"/(video_set|audio_set|ip\.set|input\.set|system_set|login\.set)\d*"
)

# Regex for binary endpoint with CRCs (e.g., binary0,0,0,0.get1704283200000)
BINARY_ENDPOINT_PATTERN = re.compile(r"/binary([^.]+)\.get\d*")


@app.post("/{endpoint:path}")
async def handle_set_commands(endpoint: str, request: Request):
    """Handle POST commands to set device state."""
    full_path = f"/{endpoint}"

    if not SET_ENDPOINT_PATTERN.match(full_path):
        return Response(status_code=404)

    body = await request.body()
    cmd = body.decode("utf-8")

    logger.debug(f"Received command for {endpoint}: {cmd}")

    response_data = simulator.process_command(cmd)

    if response_data:
        # Some commands (login, register) return JSON
        if response_data.startswith("{"):
            import json

            return JSONResponse(content=json.loads(response_data))
        return Response(content=response_data)

    return Response(content="OK")


@app.get("/{endpoint:path}")
async def handle_get_requests(endpoint: str):
    """Handle GET requests for status."""
    full_path = f"/{endpoint}"

    # Check if it's a binary status request
    binary_match = BINARY_ENDPOINT_PATTERN.match(full_path)
    if binary_match:
        client_crcs = binary_match.group(1).split(",")

        # Generate full binary data
        data = simulator.get_binary_data()

        # Device logic: Only return blocks that have changed compared to client CRCs
        # Header (16 bytes) contains sizes of blocks 0, 1, 2, 3
        # If client CRC for block i matches server CRC, server sets size[i] to 0 in header
        # and omits the block data.

        import struct

        block_sizes = list(struct.unpack("<IIII", data[:16]))
        data_blocks = []
        offset = 16

        new_sizes = [0, 0, 0, 0]

        for i in range(4):
            block_data = data[offset : offset + block_sizes[i]]
            offset += block_sizes[i]

            if block_sizes[i] > 0:
                server_crc = f"{calculate_crc32(block_data):08x}"

                # If CRC changed (or client doesn't have it), include the block
                is_known = False
                if i < len(client_crcs):
                    # Clean the client CRC (remove whitespace/quotes if any)
                    clean_client_crc = client_crcs[i].strip().lower()
                    if clean_client_crc == server_crc.lower():
                        is_known = True

                if not is_known:
                    new_sizes[i] = block_sizes[i]
                    data_blocks.append(block_data)
                    logger.debug(
                        f"Block {i} sent: server_crc={server_crc}, "
                        f"client_crc={client_crcs[i] if i < len(client_crcs) else 'none'}"
                    )
                else:
                    new_sizes[i] = 0
                    logger.debug(f"Block {i} skipped: client already has {server_crc}")
            else:
                new_sizes[i] = 0

        # Construct response with modified header
        new_header = struct.pack("<IIII", *new_sizes)
        response_content = new_header + b"".join(data_blocks)

        return Response(content=response_content, media_type="application/octet-stream")

    return Response(status_code=404)
