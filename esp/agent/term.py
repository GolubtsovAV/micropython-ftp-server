
import socket, os

port = 40
host_addr = ('192.168.1.52', port )

sock = None

def sock_close():
    if sock: 
        sock.setsockopt( socket.SOL_SOCKET, 20, None )
        sock.close()

def set_sockOpt():
    sock.setblocking( False )
    sock.setsockopt( socket.SOL_SOCKET, 20, os.dupterm_notify )
    os.dupterm( sock )
    sock.sendall('Hello from micropython!\r\n')

def connect():
    global sock
    sock_close()
    try:
        sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
        sock.connect( host_addr )
        set_sockOpt()
    except:
        print( 'can`t connect term' )

def accept( s ):
    global sock
    sock_close()
    sock, addr = s.accept()
    set_sockOpt()

serv = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
serv.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
serv.bind(("0.0.0.0", port))
serv.listen( 2 )
serv.setsockopt( socket.SOL_SOCKET, 20, accept )

connect()

