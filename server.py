import json
import asyncio
import websockets
import hashlib
import random
import psycopg2
from cryptography.hazmat.backends import default_backend

baseG = 12
moduloP = 31
private_key = random.randint(500, 4000)
conn = psycopg2.connect(database="keys",
                        host="localhost",
                        user="postgres",
                        password="123",
                        port="5432")


async def send_encription_key(websocket, contract_address):

    cursor = conn.cursor()

    sql = "SELECT keys FROM keys WHERE contract_address = %s"

    cursor.execute(sql, (contract_address,))

    llave = cursor.fetchall()

    print(llave)

    data = {
        "event": "serverEncriptionKey",
        "key": llave[0]
    }

    await websocket.send(json.dumps(data))


async def send_public_key(websocket):

    print("------------------------")

    key_to_send = (baseG ** private_key) % moduloP

    print(key_to_send)

    data = {
        "event": "computedOfferServer",
        "computedKey": key_to_send,
        "p": moduloP,
        "g": baseG,
    }

    await websocket.send(json.dumps(data))


async def get_shared_key(websocket, computedClient):

    print("datos recibidos\n\n\n")

    shared_key = (computedClient ** private_key) % moduloP
    print("llave compartida: ", shared_key)

    llave_bytes = shared_key.to_bytes(16, byteorder='big')
    hash_object = hashlib.sha256(llave_bytes)
    llave_string = hash_object.hexdigest()[:16]

    print("llave aes: ", llave_string)

    data = {
        "event": "close",
    }

    await websocket.send(json.dumps(data))


async def save_contract_addresses_key(websocket, address1, address2, key):

    print("direccion recibida\n")
    # aqui guardar la llave
    cursor = conn.cursor()

    sql = "INSERT INTO keys (keys,contract_address,report_address) VALUES (%s,%s,%s)"

    cursor.execute(sql, (key, address1, address2))
    conn.commit()

    data = {
        "event": "close",
    }

    await websocket.send(json.dumps(data))


async def send_contract_address(websocket, index):

    print("enviando direccion\n")

    print("Index: ", index)

    cursor = conn.cursor()

    sql = "SELECT contract_address FROM keys"

    cursor.execute(sql)

    allContracts = cursor.fetchall()

    data = {
        "event": "close",
        "contract_address": allContracts[index]
    }

    await websocket.send(json.dumps(data))


async def handler(websocket):
    print("Hola, bienvenido al centro de proteccion de llaves")
    async for message in websocket:

        message = json.loads(message)

        action = message["action"]

        match action:

            case "sendPublicKey":

                await send_public_key(websocket)

            case "sendClientPk":

                await get_shared_key(websocket, message["computedValue"])

            case "sendEncriptionKey":

                await send_encription_key(websocket, message["contract_address"])

            case "saveAndRelateAddressToKey":

                await save_contract_addresses_key(websocket, message["contract_address"], message["report_address"], message["key"])

            case "sendContractAddress":

                await send_contract_address(websocket, message["index"])

            case _:
                print("default")


async def main():
    async with websockets.serve(handler, "", 8006):
        print("esperando........")

        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
