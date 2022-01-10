
import socket, select, os, threading
from sys import stdin, stdout

port = 40


client = None
server = None

def key_inputs():
    while True:
        d = input()
        if client and d:
            d = bytes( d,'utf-8' )
            client.setblocking( True )
            client.sendall( d )
            client.sendall( b'\r\n' )# input не записывает в строку \r\n, поэтому сами
            client.setblocking( False )
        elif d:
            print( 'no connection, your msg:', d )
    
def main():
    global server, client
    
    print("TCP terminal for term.py on ESP8266 micropython (@lex)")
    
    input_thread = threading.Thread(target=key_inputs, args=())
    input_thread.daemon = True
    input_thread.start()
    
    server = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    server.bind( ('0.0.0.0', port) )
    server.listen( 2 )
    
    while True:
    
        if client:
            inputs = [ server, client ]
        else:
            inputs = [ server ]
        r , w, e = select.select( inputs, [], inputs )

        for obj in e:
            if obj == client:
                client.close()
                client = None
                r = []
                break
            elif obj == server:
                raise Exception('Server error')
                
        for obj in r:
            if obj == client:
                client.setblocking( False )
                d = client.recv(1024)
                if d:
                    os.write( stdout.fileno(), d )
            if obj == server:
                if client: 
                    client.close()
                client, addr = server.accept()
                print('\r\n********  New connection ', str(addr),' ********')
 

if __name__ == '__main__':
    main()



