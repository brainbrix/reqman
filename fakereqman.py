##/usr/bin/python
# -*- coding: utf-8 -*-

    
from aiohttp import web
import json,asyncio

routes = web.RouteTableDef()

@routes.get('/set')
async def hello(request):
    return web.Response(status=200,text=request.query.get("value","?"))

@routes.get('/bigtxt')
async def hello(request):
    return web.Response(status=200,text="".join(["[%s]" % i for i in range(10000)]))

@routes.get('/wait')
async def hello(request):
    await asyncio.sleep(float(request.query.get("value","5")))
    return web.Response(status=200,text="OK" )

@routes.get('/get_404')
async def hello(request):
    return web.Response(status=404,text="My not found")

@routes.get('/get_500')
async def hello(request):
    a=12/0


@routes.get('/get_txt')
async def hello(request):
    return web.Response(status=200,text="Héllo ça và ?")

@routes.get('/get_txt_cp1252')
async def hello(request):
    return web.Response(status=200,text="Héllo ça và ?",charset="Windows-1252")

@routes.get('/get_bytes')
async def hello(request):
    return web.Response(status=200,body=bytes(range(0,255)) )

@routes.get('/get_json')
async def hello(request):
    obj=dict( info=dict(t="Hello",n=42,m="42"), infos=[1,2,3], float=3.14, empty=None, mot="héllo ça va ?",msg="héllo")
    return web.Response(status=200,body=json.dumps(obj),headers={"X-MyHeader":"hello"})

@routes.get('/get_header')
async def hello(request):
    return web.Response(status=200,body="ok", headers=dict(msg="héhé"))

@routes.get('/get_xml')
async def hello(request):
    xml="""<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:ns2="www">
    <entete>
        <ns2:typeDocument>hello</ns2:typeDocument>
    </entete>
    <age>42</age>
    <a v="1">aaa1</a>
    <a>aaa2</a>
    <b v="9">b9</b>
    <b v="11">b11</b>
    <c>yolo <i>xxx</i></c>
</x>"""
    return web.Response(status=200,text=xml)

import socket
def isFree(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    return not (s.connect_ex((ip,port)) == 0)

import sys,reqman
import threading,asyncio
class FakeWebServer(threading.Thread): # the webserver is ran on a separated thread
    def __init__(self,port):
        super(FakeWebServer, self).__init__()
        self.port=port
        self.app = web.Application()
        self.app.add_routes(routes)
        self.root="http://localhost:%s" % self.port
        self._exit=False

    def run(self):
        print("> Fake Server:",self.root)

        async def start():
            runner = web.AppRunner(self.app)
            await runner.setup()
            self.site=web.TCPSite(runner, 'localhost', self.port)
            await self.site.start()
        
            while self._exit==False:
                await asyncio.sleep(0.333333)

            await self.site.stop()
            await runner.shutdown()

        asyncio.set_event_loop(asyncio.new_event_loop())
        loop=asyncio.get_event_loop()


        async def wait():
            while not isFree("127.0.0.1",self.port):
                await asyncio.sleep(0.5)

        loop.run_until_complete(wait()) 
        loop.run_until_complete(start())       
        loop.run_until_complete(wait()) 

        # gracefull death
        tasks = asyncio.all_tasks(loop) #py37
        for task in tasks: task.cancel()
        try:
            loop.run_until_complete(asyncio.gather(*tasks))
        except:
            pass
        loop.close() 


    def stop(self):
        self._exit=True





def checkSign(sign1,sign2):
    """ Return the error or '' """
    if sign1==sign2:
        return "" # no error
    else:
        dsign1=sign1.split(',')
        dsign2=sign2.split(',')
        if len(dsign1)!=len(dsign2):
            return "Not same number od requests (is there a new ?)"
        else:
            for idx,(t1,t2) in enumerate(zip(dsign1,dsign2)):
                if len(t1) != len(t2):
                    return "Req %s has %s tests (expected %s)" % (idx+1,len(t2),len(t1))
                else:
                    if t1!=t2:
                        diffs=[i+1 for i,(a1,a2)  in enumerate(zip(t1,t2)) if a1!=a2]
                        return "Req %s fail on its %s test" % (idx+1,diffs[0])

def main( runServer=False ):
    """
    retourne 0 : si valid est ok
    retourne 1 : si valid est ko
    retourne None : si pas validation
    """


    class RR: pass
    o=RR()

    #check valid in argv -> valid
    #=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    removeArgIdx=None
    valid=None
    for idx, argv in enumerate(sys.argv):
        if argv.startswith("valid:"):
            valid = argv[6:]
            removeArgIdx=idx
    if removeArgIdx:
        del sys.argv[removeArgIdx]
    #=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    try:
        if runServer:
            ws=FakeWebServer(11111)
            ws.start()
            import time
            time.sleep(1) # wait server start ;-(

        rc=reqman.main(hookResults=o)
    finally:
        if runServer:
            ws.stop()

    frc=None
    if rc>=0 and hasattr(o,"rr"):
        details=[]
        for i in o.rr.results:
            for j in i.exchanges:
                details.append("".join([str(int(t)) for t in j.tests]))
        toValid=",".join(details)
        
        if valid:
            err=checkSign(valid,toValid)
            print("> Check valid:",valid,"?==",toValid,"-->","!!! ERROR: %s !!!"%err if err else "OK")
        else:
            print("> No validation check! (valid:%s)" % toValid)
            err=None
    else:
        toValid="ERROR"
        if valid:
            err="" if valid==toValid else "no error"
            print("> Check valid:",valid,"?==",toValid,"-->","!!! ERROR: %s !!!"%err if err else "OK")
        else:
            print("> No validation check! (valid:%s)" % toValid)
            err=None

    return err


if __name__=="__main__":
    err=main(runServer=True)
    if err is None:
        sys.exit( -1)
    elif err=="":
        sys.exit(0)
    else:
        sys.exit(1)

