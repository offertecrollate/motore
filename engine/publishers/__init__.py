"""Canali su cui pubblicare. Ogni canale ha send(deal) e una lingua."""
from .channels import ConsolePublisher, TelegramPublisher, WhatsAppWahaPublisher, FacebookPagePublisher

PUBLISHER_TYPES = {
    "console": ConsolePublisher,
    "telegram": TelegramPublisher,
    "whatsapp_waha": WhatsAppWahaPublisher,
    "facebook_page": FacebookPagePublisher,
}


def build_publisher(cfg: dict):
    kind = cfg["type"]
    if kind not in PUBLISHER_TYPES:
        raise ValueError(f"Tipo di canale sconosciuto: {kind}")
    return PUBLISHER_TYPES[kind](cfg)
