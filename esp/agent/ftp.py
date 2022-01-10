
import socket, os, network, gc

USER = '111'
gc.enable()

def createTCPServer( port, listen ):
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    s.bind(( '0.0.0.0', port ))
    s.listen( listen )
    return s

auth = False
dsock = None
fsock = None
RNFR = None
CWD = '/'
fileForSend = None
deserv_task = None

def fserv_accept( s ):
    global fsock
    if fsock: fsock_close()
    fsock, addr = s.accept()
    fsock.setblocking( False ) 
    fsock.setsockopt( socket.SOL_SOCKET, 20, fsock_callback )
    fsock.sendall("200 hello\r\n")

def dserv_accept( s ):
    global dsock, deserv_task
    f = deserv_task
    deserv_task = None
    dsock, addr = s.accept()
    dsock.settimeout(1.0)
    if f: f()
    
def set_deservTask( t ):
    global dsock, deserv_task
    if dsock:
        t()
    else:
        deserv_task = t

fserv = createTCPServer( 21, 2 )
dserv = createTCPServer( 20, 2 )

fserv.setsockopt( socket.SOL_SOCKET, 20, fserv_accept )
dserv.setsockopt( socket.SOL_SOCKET, 20, dserv_accept )
print("ftp started")


def fsock_callback( s ):
    global fsock, dserv, RNFR, CWD, fileForSend
    global dsock, deserv_task, auth
    if not fsock: return
    
    data = fsock.read()

    if not data:
        return
    arr = str( data, 'utf-8' ).strip().split(' ')
    cmd = arr[0] = arr[0].upper()
    #print( arr )
    
    if cmd == 'USER' and USER == arr[1]:
        fsock_sendOK(230)
        auth = True
        return
    
    if not auth:
        fsock.sendall("530 Not logged in.\r\n")
        fsock_close()
        return
    
    if cmd == 'OPTS' or cmd == 'NOOP' or cmd == 'TYPE' or cmd == 'MODE' or cmd == 'STRU':
        fsock_sendOK()
    elif cmd == 'SIZE':
        fsock.sendall( '213 {}\r\n'.format( os.stat( normalizeFName( arr[1] ) )[6] ) )
    elif cmd == 'PASV':
        fsock.sendall( '227 ok ({},0,20)\r\n'.format(
                network.WLAN().ifconfig()[0].replace('.',',') ) )
    elif cmd == 'DELE':
        try:
            os.remove( normalizeFName( arr[1] ) )
            fsock_sendOK( 250 )
        except:
            fsock_sendErr( 550 )
    elif cmd == 'RNFR':
        try:
            n = normalizeFName( arr[1] )
            os.stat( n )
            RNFR = n
            fsock_sendOK( 350 )
        except:
            fsock_sendErr( 550 )
    elif cmd == 'RNTO':
        try:
            os.rename( RNFR, normalizeFName( arr[1] ) )
            fsock_sendOK( 250 )
        except:
            fsock_sendErr( 550 )
    elif cmd == 'MKD':
        try:
            os.mkdir( normalizeFName( arr[1] ) )
            fsock_sendOK( 257 )
        except:
            fsock_sendErr( 550 )
    elif cmd == 'RMD':
        try:
            os.rmdir( normalizeFName( arr[1] ) )
            fsock_sendOK( 257 )
        except:
            fsock_sendErr( 550 )
    elif cmd == 'CWD':
        try:
            n = normalizeFName( arr[1] )
            os.stat( n )
            CWD = n
            fsock_sendOK()
        except:
            fsock_sendErr( 550 )
    elif cmd == 'PWD':
        fsock.sendall('257 "')
        fsock.sendall( CWD )
        fsock.sendall('" \r\n')
    elif cmd == 'SYST':
        fsock.sendall("215 UNIX Type: L8\r\n")
    elif cmd == 'LIST':
        fsock_sendOK( 150 )
        set_deservTask( dserv_sendList )
    elif cmd == 'RETR':
        fileForSend = normalizeFName( arr[1] )
        fsock_sendOK( 150 )
        set_deservTask( dserv_sendFile )
    elif cmd == 'STOR':
        fileForSend = normalizeFName( arr[1] )
        fsock_sendOK( 150 )
        set_deservTask( dserv_loadFile )
    elif cmd == 'PORT':
        a = arr[1].split(',')
        addr = ( a[0]+'.'+a[1]+'.'+a[2]+'.'+a[3], ( int(a[4]) * 256 + int(a[5]) )  )
        if dsock: dsock_close()
        dsock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
        dsock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        dsock.connect( addr )
        fsock_sendOK( 200 )
        if deserv_task : set_deservTask( deserv_task )
    ###
    elif cmd == 'QUIT':
        fsock.sendall('221 Bye.\r\n')
        fsock_close()
    else:
        fsock.sendall("502 Unsupported command.\r\n")
        
    gc.collect()


def normalizeFName( fn ):
    if fn[0] != '/':
        if CWD[-1] != '/':
            return CWD + '/' + fn
        return CWD + fn
    return fn

def fsock_close():
    global RNFR, CWD, fsock, auth
    RNFR = None
    CWD = '/'
    fsock.setsockopt( socket.SOL_SOCKET, 20, None )
    fsock.close()
    fsock = auth = None
    gc.collect()
    
def dsock_close():
    global deserv_task, dsock
    dsock.close()
    dsock = deserv_task =None

def fsock_sendOK( code = 200 ):
    fsock.sendall( str(code) )
    fsock.sendall(' ok mem:')
    fsock.sendall( str( gc.mem_free() ) )
    fsock.sendall( '\r\n' )
    
def fsock_sendErr( code ):
    fsock.sendall( str(code) )
    fsock.sendall(' err\r\n')

def dserv_sendList():
    try:
        for file in os.listdir( CWD ):
            stat = os.stat( CWD+'/'+file)
            fp = "drwxr-xr-x" if (stat[0] & 0o170000 == 0o040000) else "-rw-r--r--"
            fz = stat[6]
            dsock.sendall( "{}    1 owner group {:>13} Jan 1  1980 {}\r\n".format(fp, fz, file))
        fsock_sendOK( 226 )
    except Exception as err:
        fsock_sendErr( 550 )
        raise err
    finally:
        dsock_close()


def dserv_sendFile():
    try:
        file = open( fileForSend, 'r' )
        while data := file.read( 128 ):
            dsock.sendall( data )
        fsock_sendOK(226)
    except Exception as err:
        fsock_sendErr( 550 )
        raise err
    finally:
        dsock_close()
        if file: file.close()

def dserv_loadFile():
    try:
        file = open( fileForSend, 'w' )
        while data := dsock.read( 128 ):
            file.write( data )
        fsock_sendOK( 226 )
    except:
        fsock_sendErr( 550 )
    finally:
        dsock_close()
        if file: file.close()

