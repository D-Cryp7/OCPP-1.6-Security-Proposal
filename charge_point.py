from ocpp.v16 import call
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import RegistrationStatus
import asyncio
import logging
import os
import websockets
from random import randint
from datetime import datetime, timedelta
from util import *
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Util.Padding import pad, unpad

logging.basicConfig(level = logging.INFO)

class ChargePoint(cp):
    async def send_authorize(self):
        request = call.AuthorizePayload(
            id_tag = os.urandom(10).hex()
        )
        response = await self.call(request)
        
    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model = "Optimus",
            charge_point_vendor = "The Mobility House"
        )

        response = await self.call(request)

        if response.status == RegistrationStatus.accepted:
            print("Connected to central system.")
            
    async def send_start_transaction(self):
        request = call.StartTransactionPayload(
            connector_id = randint(1, 10),
            id_tag = os.urandom(10).hex(),
            meter_start = randint(1, 10),
            timestamp = datetime.utcnow().isoformat()
        )
        response = await self.call(request)
        
    async def send_stop_transaction(self):
        meter_stop = randint(11, 20)
        print("Meter Stop from Charging Point:", meter_stop)
        plaintext = long_to_bytes(meter_stop)
        key = sha256(bytes.fromhex(shared)).digest()
        cipher = AES.new(key, AES.MODE_GCM)
        encrypted, tag = cipher.encrypt_and_digest(pad(plaintext, 16))
            
        request = call.StopTransactionPayload(
            meter_stop = bytes_to_long(encrypted),
            timestamp = datetime.utcnow().isoformat(),
            transaction_id = randint(1, 10),
            transaction_data = [{
                "timestamp": datetime.utcnow().isoformat(),
                "sampledValue": [{
                    "value": tag.hex()
                }]
            }, {
                "timestamp": datetime.utcnow().isoformat(),
                "sampledValue": [{
                    "value": cipher.nonce.hex()
                }]
            }]
        )
        response = await self.call(request)
            
    async def send_heartbeat(self):
        request = call.HeartbeatPayload()
        '''
        for i in range(10):
            response = await self.call(request)
        '''
        response = await self.call(request)
        
    async def key_exchange(self):
        s = randint(2, p - 2)
        Q = multiply(s, G, E)
        request = call.DataTransferPayload(
            vendor_id = "The Mobility House",
            message_id = "KEP",
            data = str(Q)
        )
        response = await self.call(request)
        P = eval(response.data)
        shared = multiply(s, P, E)[0]
        self.key = sha256(long_to_bytes(shared)).digest()
        
async def main():
    async with websockets.connect(
        'ws://localhost:9000/CP_1',
        subprotocols=['ocpp1.6']
    ) as ws:
        cp = ChargePoint('CP_1', ws)
        
        tasks = [cp.start(), cp.key_exchange(), cp.send_authorize(), cp.send_start_transaction(), cp.send_authorize(), cp.send_stop_transaction()]
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    # await main() is used when running this example in jupyter notebook
    asyncio.run(main())