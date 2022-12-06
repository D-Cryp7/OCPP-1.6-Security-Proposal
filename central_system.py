import asyncio
import logging
from datetime import datetime, date, timedelta
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.v16 import call_result
import os
import websockets
from random import randint
from util import *
from hashlib import sha256
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

logging.basicConfig(level = logging.INFO)

class ChargePoint(cp):
    @on(Action.Authorize)
    def on_authorize(self, id_tag: str):
        return call_result.AuthorizePayload(
             id_tag_info = {
                 "expiryDate": (datetime.utcnow() + timedelta(days = 2)).isoformat(),
                 "parentIdTag": os.urandom(5).hex(),
                 "status": RegistrationStatus.accepted
             }
        )
    
    @on(Action.BootNotification)
    def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        return call_result.BootNotificationPayload(
            current_time = datetime.utcnow().isoformat(),
            interval = 10,
            status = RegistrationStatus.accepted
        )
    
    @on(Action.StartTransaction)
    def on_start_transaction(self, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        return call_result.StartTransactionPayload(
            transaction_id = randint(1, 10),
            id_tag_info = {
                "expiryDate": (datetime.utcnow() + timedelta(days = 2)).isoformat(),
                "parentIdTag": os.urandom(5).hex(),
                "status": RegistrationStatus.accepted
            }  
        )
    
    @on(Action.StopTransaction)
    def on_stop_transaction(self, meter_stop: int, timestamp: str, transaction_id: int, transaction_data: list, **kwargs):
        print("Transaction data from Charging Point:", transaction_data)
        encrypted = long_to_bytes(meter_stop)
        # tag = long_to_bytes(transaction_id)
        tag = bytes.fromhex(transaction_data[0]["sampled_value"][0]["value"])
        # nonce = bytes.fromhex(timestamp.split("/")[1])
        nonce = bytes.fromhex(transaction_data[1]["sampled_value"][0]["value"])
        key = sha256(bytes.fromhex(shared)).digest()
        cipher = AES.new(key, AES.MODE_GCM, nonce = nonce)
        try:
            recovered_meter_stop = bytes_to_long(unpad(cipher.decrypt_and_verify(encrypted, tag), 16))
            print("Meter Stop from Central System:", recovered_meter_stop)
            return call_result.StopTransactionPayload(
                id_tag_info = {
                    "expiryDate": (datetime.utcnow() + timedelta(days = 2)).isoformat(),
                    "parentIdTag": os.urandom(5).hex(),
                    "status": RegistrationStatus.accepted
                } 
            )
        except:
            return call_result.StopTransactionPayload(
                id_tag_info = {
                    "expiryDate": "-",
                    "parentIdTag": "-",
                    "status": "Invalid"
                } 
            )
    
    @on(Action.Heartbeat)
    def on_heartbeat(self):
        return call_result.HeartbeatPayload(
            current_time = datetime.utcnow().isoformat()
        )
    
    @on(Action.DataTransfer)
    def on_data_transfer(self, vendor_id: str, message_id: str, data: str):
        if message_id == "KEP":
            s = randint(2, p - 2)
            Q = multiply(s, G, E)
            P = eval(data)
            shared = multiply(s, P, E)[0]
            self.key = sha256(long_to_bytes(shared)).digest()
            return call_result.DataTransferPayload(
                status = RegistrationStatus.accepted,
                data = str(Q)
            )
        

async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint
    instance and start listening for messages.
    """
    try:
        requested_protocols = websocket.request_headers[
            'Sec-WebSocket-Protocol']
    except KeyError:
        logging.error(
            "Client hasn't requested any Subprotocol. Closing Connection"
        )
        return await websocket.close()
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning('Protocols Mismatched | Expected Subprotocols: %s,'
                        ' but client supports  %s | Closing connection',
                        websocket.available_subprotocols,
                        requested_protocols)
        return await websocket.close()

    charge_point_id = path.strip('/')
    cp = ChargePoint(charge_point_id, websocket)

    await cp.start()


async def main():
    server = await websockets.serve(
        on_connect,
        None, 
        9000,
        subprotocols=['ocpp1.6']
    )

    logging.info("Server Started listening to new connections...")
    await server.wait_closed()


if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    # await main() is used when running this example in jupyter notebook
    asyncio.run(main())