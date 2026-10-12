from dataclasses import dataclass, field
from typing import Dict, List
from .infrai_client import InfraiClient, InfraiError


@dataclass
class ShipmentEvent:
    shipment_id: str
    status: str
    location: str


@dataclass
class Shipment:
    shipment_id: str
    recipient: str
    events: List[ShipmentEvent] = field(default_factory=list)
    proof_files: List[str] = field(default_factory=list)
    exception: str | None = None


class LogisticsSignup:
    def __init__(self, client: InfraiClient):
        self.client = client
        self.shipments: Dict[str, Shipment] = {}

    def signup(self, email: str, password: str, name: str, verification_base: str):
        created = self.client.create_user(email, password, name)
        user_id = created["data"]["user_id"]
        session = self.client.create_session(user_id)
        session_id = session["data"]["session_id"]
        link = verification_base.rstrip("/") + "/verify/" + session_id
        sent = self.client.send_verification(email, link)
        return {"user_id": user_id, "session_id": session_id, "message_id": sent["data"]["message_id"], "verification_link": link}

    def record_event(self, shipment_id: str, recipient: str, status: str, location: str):
        shipment = self.shipments.setdefault(shipment_id, Shipment(shipment_id, recipient))
        shipment.events.append(ShipmentEvent(shipment_id, status, location))
        if status == "exception":
            shipment.exception = "delivery exception at " + location
        return shipment

    def attach_proof(self, shipment_id: str, file_name: str):
        if shipment_id not in self.shipments:
            raise ValueError("shipment must exist")
        self.shipments[shipment_id].proof_files.append(file_name)
        return self.shipments[shipment_id]
