import aiohttp
import json
import logging

_LOGGER = logging.getLogger(__name__)

class CentauriWebSocketClient:
    def __init__(self, hass, ip_address):
        self._hass = hass
        self._ws = None
        self.data = {}
        self.ip = ip_address
        self.url = f"ws://{ip_address}:3030/websocket"

    async def connect(self):
        session = aiohttp.ClientSession()
        try:
            self._ws = await session.ws_connect(self.url)
            _LOGGER.info("Connected to Centauri WebSocket")

            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    payload = json.loads(msg.data)
                    _LOGGER.debug(f"Received WS payload: {payload}")
                    self._handle_message(payload)
        except Exception as e:
            _LOGGER.error(f"WebSocket connection failed: {e}")

    def _handle_message(self, payload):
        try:
            status = payload.get("Status", {})
            print_info = status.get("PrintInfo", {})
            fan_speeds = status.get("CurrentFanSpeed", {})

            progress = round(print_info.get("Progress", 0), 1)
            status_code = print_info.get("Status", 0)

            if status_code in [1, 16, 21]:
                printable_status = "Preparing"
            elif status_code == 13:
                printable_status = "Printing"
            elif status_code == 9:
                printable_status = "Print Complete"
            elif status_code == 0:
                printable_status = "Idle"
            else:
                printable_status = f"Unknown ({status_code})"

            self.data = {
                "nozzle_temp": round(status.get("TempOfNozzle", 0), 1),
                "bed_temp": round(status.get("TempOfHotbed", 0), 1),
                "enclosure_temp": round(status.get("TempOfBox", 0), 1),
                "target_bed_temp": round(status.get("TempTargetHotbed", 0), 1),
                "target_nozzle_temp": round(status.get("TempTargetNozzle", 0), 1),
                "z_offset": round(status.get("ZOffset", 0), 3),
                "model_fan_speed": fan_speeds.get("ModelFan", 0),
                "aux_fan_speed": fan_speeds.get("AuxiliaryFan", 0),
                "box_fan_speed": fan_speeds.get("BoxFan", 0),
                "progress": progress,
                "print_status": printable_status,
                "current_layer": print_info.get("CurrentLayer", 0),
                "total_layers": print_info.get("TotalLayer", 0),
                "print_speed_pct": print_info.get("PrintSpeedPct", 100)
            }

            _LOGGER.debug(f"Parsed data: {self.data}")
        except Exception as e:
            _LOGGER.warning(f"Error parsing WebSocket message: {e}")