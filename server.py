import json
import asyncio
import websockets
import hashlib
import random
import psycopg2
from cryptography.hazmat.backends import default_backend

baseG = 12
moduloP = 31
private_key = random.randint(500,4000)
llaveAes = 0
conn = psycopg2.connect(database="keys",
                        host="localhost",
                        user="postgres",
                        password="123",
                        port="5432")


async def send_encription_key(websocket):
    
    archivo = open("keystorage.txt","r")
    
    llave = archivo.read()
    
    print("---------\n\n\n",llave,"\n\n\n--------")
    
    archivo.close()
    
    data={
        "event": "serverEncriptionKey",
        "key":llave
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
    print("llave compartida: ",shared_key)
    
    llave_bytes = shared_key.to_bytes(16, byteorder='big')
    hash_object = hashlib.sha256(llave_bytes)
    llave_string = hash_object.hexdigest()[:16]
    
    print("llave aes: ",llave_string)
    
    #aqui guardar la llave
    cursor = conn.cursor()
    
    sql = "INSERT INTO encode_keys (encoding) VALUES (%s)"
    
    cursor.execute(sql,llave_string)
    conn.commit()
    
    archivo = open("keystorage.txt","w")
    archivo.write(llave_string)
    archivo.close
    
    data = {
        "event": "close",
    }
    
    await websocket.send(json.dumps(data))
    
async def save_contract_address_key(websocket,address):
    
    print("direccion recibida\n")
    
    data = {
        "event": "close",
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
                
                await get_shared_key(websocket,message["computedValue"])

            case "sendEncriptionKey":
                
                await send_encription_key(websocket)
                
            case "saveAndRelateAddressToKey":
                
                await save_contract_address_key(websocket,message["contract_address"])

            case _:
                print("default")


async def main():
    async with websockets.serve(handler, "", 8006):
        print("esperando........")

        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
