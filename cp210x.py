# Silicon Laboratories CP210x USB to RS232 serial adaptor driver
#
# based on linux kernel driver
#
# Copyright (C) 2005 Craig Shelley (craig@microtron.org.uk)
# Copyright (C) 2010 Erik Gilling (konkers@konkers.net)
# 
# 	This program is free software; you can redistribute it and/or
# 	modify it under the terms of the GNU General Public License version
# 	2 as published by the Free Software Foundation.

import usb
import time

# Config request types
REQTYPE_HOST_TO_DEVICE	= 0x41
REQTYPE_DEVICE_TO_HOST	= 0xc1

# Config request codes
CP210X_IFC_ENABLE	= 0x00
CP210X_SET_BAUDDIV	= 0x01
CP210X_GET_BAUDDIV	= 0x02
CP210X_SET_LINE_CTL	= 0x03
CP210X_GET_LINE_CTL	= 0x04
CP210X_SET_BREAK	= 0x05
CP210X_IMM_CHAR		= 0x06
CP210X_SET_MHS		= 0x07
CP210X_GET_MDMSTS	= 0x08
CP210X_SET_XON		= 0x09
CP210X_SET_XOFF		= 0x0A
CP210X_SET_EVENTMASK	= 0x0B
CP210X_GET_EVENTMASK	= 0x0C
CP210X_SET_CHAR		= 0x0D
CP210X_GET_CHARS	= 0x0E
CP210X_GET_PROPS	= 0x0F
CP210X_GET_COMM_STATUS	= 0x10
CP210X_RESET		= 0x11
CP210X_PURGE		= 0x12
CP210X_SET_FLOW		= 0x13
CP210X_GET_FLOW		= 0x14
CP210X_EMBED_EVENTS	= 0x15
CP210X_GET_EVENTSTATE	= 0x16
CP210X_SET_CHARS	= 0x19

# CP210X_IFC_ENABLE
UART_ENABLE		= 0x0001
UART_DISABLE		= 0x0000

# CP210X_(SET|GET)_BAUDDIV
BAUD_RATE_GEN_FREQ	= 0x384000

# CP210X_(SET|GET)_LINE_CTL
BITS_DATA_MASK		= 0X0f00
BITS_DATA_5		= 0X0500
BITS_DATA_6		= 0X0600
BITS_DATA_7		= 0X0700
BITS_DATA_8		= 0X0800
BITS_DATA_9		= 0X0900

BITS_PARITY_MASK	= 0x00f0
BITS_PARITY_NONE	= 0x0000
BITS_PARITY_ODD		= 0x0010
BITS_PARITY_EVEN	= 0x0020
BITS_PARITY_MARK	= 0x0030
BITS_PARITY_SPACE	= 0x0040

BITS_STOP_MASK		= 0x000f
BITS_STOP_1		= 0x0000
BITS_STOP_1_5		= 0x0001
BITS_STOP_2		= 0x0002

# CP210X_SET_BREAK
BREAK_ON		= 0x0000
BREAK_OFF		= 0x0001

# CP210X_(SET_MHS|GET_MDMSTS)
CONTROL_DTR		= 0x0001
CONTROL_RTS		= 0x0002
CONTROL_CTS		= 0x0010
CONTROL_DSR		= 0x0020
CONTROL_RING		= 0x0040
CONTROL_DCD		= 0x0080
CONTROL_WRITE_DTR	= 0x0100
CONTROL_WRITE_RTS	= 0x0200


class cp210x:
    def __init__(self, vendor_id, product_id):
        self.device = self.find_device(vendor_id, product_id)
        self.handle = self.device.open();

        self.handle.claimInterface(0);
        self._in = 0x81
        self._out = 0x01
        self.data = ""
        
        self.handle.controlMsg(requestType = REQTYPE_HOST_TO_DEVICE,
                               request = CP210X_RESET,
                               value = 0,
                               index = 0,
                               buffer = 0,
                               timeout = 300)
        self.handle.controlMsg(requestType = REQTYPE_HOST_TO_DEVICE,
                               request =CP210X_IFC_ENABLE,
                               value = UART_ENABLE,
                               index = 0,
                               buffer = 0,
                               timeout = 300)
        baud = 460800
        self.handle.controlMsg(requestType = REQTYPE_HOST_TO_DEVICE,
                               request = CP210X_SET_BAUDDIV,
                               value = (BAUD_RATE_GEN_FREQ + baud/2) / baud,
                               index = 0,
                               buffer = 0,
                               timeout = 300)


    def read(self, l):
        l = min(l, len(self.data))

        if l > 0:
            data = self.data[0:l]
            self.data = self.data[l:]
            return data
        else:
            return ""
    
    def write(self, data):
        return self.handle.bulkWrite(self._out, data, 100)


    def inWaiting(self, l):
        try:
            d = self.handle.bulkRead(self._in, l, 1000);
            poo = [chr(x) for x in d];
        except:
            return 0
        l = len(poo)
        poo = "".join(poo)
        self.data += poo
        return len(self.data)

    
    def find_device(self, vendor_id, product_id):
        buses = usb.busses() 
        for bus in buses: 
            for device in bus.devices: 
                if device.idVendor == vendor_id: 
                    if device.idProduct == product_id: 
                        return device 
        return None 

#cp = Cp210x(0x3195, 0xf190)
