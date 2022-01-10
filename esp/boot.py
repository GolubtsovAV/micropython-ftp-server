# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    
    wlan.active(True)
    if not wlan.isconnected():
        
        print('connecting to network...')
        wlan.config( dhcp_hostname = 'black_01' )
        wlan.connect( 'xxxxx', 'xxxxx')
        while not wlan.isconnected():
            pass
    else:
        print('was connected')
    print( wlan.config('dhcp_hostname'))
    print('network config:', wlan.ifconfig())
    
do_connect()

