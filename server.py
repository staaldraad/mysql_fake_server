import asyncio
import logging
import signal
import random
signal.signal(signal.SIGINT, signal.SIG_DFL)

from mysqlproto.protocol import start_mysql_server
from mysqlproto.protocol.base import OK, ERR, EOF
from mysqlproto.protocol.flags import Capability
from mysqlproto.protocol.handshake import HandshakeV10, HandshakeResponse41, AuthSwitchRequest
from mysqlproto.protocol.query import ColumnDefinition, ColumnDefinitionList, ResultSet,FileReadPacket
import subprocess
import time


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))

@asyncio.coroutine
def process_fileread(server_reader, server_writer,filename):
    print("Start Reading File:"+filename.decode('utf8'))
    FileReadPacket(filename).write(server_writer)
    yield from server_writer.drain()
    #server_writer.reset()
    #time.sleep(3)
    
    isFinish = False
    outContent=b''
    outputFileName="%s/%s___%d___%s"%(fileOutputDir,server_writer.get_extra_info('peername')[:2][0],int(time.time()),filename.decode('ascii').replace('/','_').replace('\\','_').replace(':','_'))
    while not isFinish:
        packet = server_reader.packet()
        while True:
            fileData = (yield from packet.read())
            if fileData == '':
                break
            if fileData == b'':
                isFinish = True
                break
            outContent+=fileData
    if len(outContent) == 0:
        print("Nothing had been read")
    else:
        if displayFileContentOnScreen:
            print("========File Conntent Preview=========")
            try:
                print(outContent.decode('utf8')[:1000])
            except Exception as e:
                print(outContent[:1000])
            print("=======File Conntent Preview End==========")
        if saveToFile:
            with open(outputFileName,'wb') as f:
                f.write(outContent)
            print("Save to File:"+outputFileName)
    return

@asyncio.coroutine
def handle_server(server_reader, server_writer):
    handshake = HandshakeV10()
    handshake.write(server_writer)
    print("Incoming Connection:"+str(server_writer.get_extra_info('peername')[:2]))
    yield from server_writer.drain()
    switch2clear=False
    handshake_response = yield from HandshakeResponse41.read(server_reader.packet(), handshake.capability)
    username = handshake_response.user
    print("Login Username:"+username.decode("ascii"))
    if username.endswith(b"_clear"):
        switch2clear = True
        username = username[:-len("_clear")]
    capability = handshake_response.capability_effective

    if (Capability.PLUGIN_AUTH in capability and
            handshake.auth_plugin != handshake_response.auth_plugin
            and switch2clear):
        print("Switch Auth Plugin to mysql_clear_password")
        AuthSwitchRequest().write(server_writer)
        yield from server_writer.drain()
        auth_response = yield from server_reader.packet().read()
        print("<=", auth_response)

    result = OK(capability, handshake.status)
    result.write(server_writer)
    yield from server_writer.drain()

    while True:
        server_writer.reset()
        packet = server_reader.packet()
        try:
            cmd = (yield from packet.read(1))[0]
        except Exception as _:
            return
            pass
        print("<=", cmd)
        query =(yield from packet.read())
        if query != '':
            query = query.decode('ascii')
        if username.startswith(b"fileread_"):    
            yield from process_fileread(server_reader, server_writer,username[len("fileread_"):])
            result = OK(capability, handshake.status)
        else:
            result = ERR(capability)

        result.write(server_writer)
        yield from server_writer.drain()

logging.basicConfig(level=logging.INFO)

fileOutputDir="./fileOutput/"
displayFileContentOnScreen = True
saveToFile=True
if __name__ == "__main__":
    
    import os
    try:
        os.makedirs(fileOutputDir)
    except FileExistsError as _:
        pass

    
    loop = asyncio.get_event_loop()
    f = start_mysql_server(handle_server, host=None, port=3306)
    print("===========================================")
    print("MySQL File Read Server")
    print("Modified from:https://github.com/fnmsd/MySQL_Fake_Server")
    print("Start Server at port 3306")
    loop.run_until_complete(f)
    loop.run_forever()
