# -*- coding: utf-8 -*- 
import network
import sys
import socket
import time
import machine
import get_date
from machine import Pin
from get_date import month_data, week_data

ap_if = network.WLAN(network.AP_IF)
ap_if.config(essid="Light", authmode=network.AUTH_WPA_WPA2_PSK, password="63423light")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('K2P','415038973')

p4 = Pin(4, Pin.OUT)
p5 = Pin(5, Pin.OUT)
p12 = Pin(12, Pin.OUT)
p14 = Pin(14, Pin.OUT)
header_200 = """HTTP/1.1 200 OK\r\n%s\r\nServer: K-httpd\r\nContent-Type: %s\r\nConnection: keep-alive\r\nConent-Length: %s\r\n\r\n"""
header_404 = """HTTP/1.1 404 Not Found\r\n%s\r\nServer: K-httpd\r\nContent-Type: %s\r\nConnection: close\r\nConent-Length: %s\r\n\r\n"""
content_type = ["text/html; charset=utf-8", "text/css; charset=utf-8", "application/x-javascript; charset=utf-8", "image/x-icon", "image/jpeg", "image/png"]

host = '0.0.0.0'
port = 80
addr = socket.getaddrinfo(host, port)[0][-1]
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setblocking(1)
s.bind(addr)
s.listen(10)
print('listening on', addr)

def ip_status(inp):   #gmt+8:北京时间 gmt：格林时间 (str类型)
    ip = wlan.ifconfig()
    if ip[1] == '255.255.255.0':
        return get_date.get_date(inp)
    else:
        return 'Unconnected'

def getlocaltime():
    global t
    t = list(time.localtime())
    for m in [1,2,3,4,5,6,7,8,9,10,11,12]:
        if t[1] == m:
            month = month_data[m - 1]
            break
    for w in [0,1,2,3,4,5,6]:
        if t[6] == w:
            week = week_data[w]
            break
    if t[3] < 10:
        t[3] = "%s%s" % ("0",t[3])
    if t[4] < 10:
        t[4] = "%s%s" % ("0",t[4])
    if t[5] < 10:
        t[5] = "%s%s" % ("0",t[5])
    global local_date
    local_date = "Date: %s, %s %s %s %s:%s:%s GMT" % (week, t[2], month, t[0], t[3], t[4], t[5])

def writefiledata(filename, status, filedata):     #写文件数据
    f = open(filename, status)
    f.write(filedata)
    f.close()

def readfilesize(filename):
    f = open(filename, 'r')
    f.seek(0,0)
    f.seek(0,2)
    return f.tell()
    f.close()

while True:
    cl, addr = s.accept()
    #print('client connected from', addr)     #Debug mode
    data = cl.recv(1024)
    print(data)     #Debug mode
    getlocaltime()
    #print(local_date)     #Debug mode
    if data.find(b'GET / HTTP') != -1:
        if p4.value() == 1:
            status = '开启'
        else:
            status = '关闭'
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/index.html") + len(status))))
        f = open("/html/index.html", 'r')
        for i in range(10):
            html_index = f.read(536)
            if len(html_index) == 0:
                break
            if html_index.find("%s") != -1:
                cl.sendall(html_index % (status))
            else:
                cl.sendall(html_index)
        f.close()
    elif data.find(b'GET /upload ') != -1:
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/upload.html"))))
        f = open("/html/upload.html", 'r')
        for i in range(10):
            html_upload = f.read(536)
            if len(html_upload) == 0:
                break
            if html_upload.find("%s") != -1:
                cl.sendall(html_upload % (''))
            else:
                cl.sendall(html_upload)
        f.close()
    elif data.find(b'POST /upload ') != -1:
        datalen_beg = data.find(b'Content-Length: ') + 16
        datalen_end = data.find(b'\r\n', datalen_beg)
        datalen = int(data[datalen_beg:datalen_end])
        boundary_beg = data.find(b'boundary=') + 9
        boundary_end = data.find(b'\r\n', boundary_beg)
        boundary = data[boundary_beg:boundary_end]
        boundary_len = len(boundary)
        print(datalen)     #Debug mode
        print(boundary)     #Debug mode
        filestatus = False
        for i in range(100):
            receives = cl.recv(1024)
            #print(receives)
            if receives.find(b'--' + boundary + b'\r\n') != -1:     #寻找数据结构开头并计算长度
                receives_beg = receives.find(b'--' + boundary + b'\r\n')
                formdata_len = len(receives[receives_beg:])
                print(formdata_len)     #Debug mode
            if receives.find(b'filename="') != -1:     #寻找文件名
                filename_beg = receives.find(b'filename="', receives_beg) + 10
                filename_end = receives.find(b'"\r\n', filename_beg)
                upload_filename = bytes.decode(receives[filename_beg:filename_end], 'utf-8')
                filestatus = True
                print(upload_filename)     #Debug mode
            if filestatus == True and receives.find(b'\r\n\r\n', filename_end) != -1:     #寻找文件数据开头
                    upload_contect_beg = receives.find(b'\r\n\r\n', filename_end) + 4
                    upload_contect_1 = bytes.decode(receives[upload_contect_beg:])
                    datafind = True
                    print(upload_contect_beg)
                    #if i != 0:
                        #writefiledata(upload_filename, 'w', upload_contect_1)
                        #print(upload_contect_1)     #Debug mode
                        #f = open(upload_filename, 'w')
                        #f.write(upload_contect_1)
                        #f.close()
            if filestatus == True and receives.find(b'\r\n--' + boundary + b'--\r\n') != -1:     #寻找文件数据结尾
                upload_contect_end = receives.find(b'\r\n--' + boundary + b'--\r\n')
                if i == 0:
                    upload_contect = bytes.decode(receives[upload_contect_beg:upload_contect_end], 'utf-8')
                    print(upload_contect)     #Debug mode
                    #writefiledata(upload_filename, 'w', upload_contect)
                    #f = open(upload_filename, 'w')
                    #f.write(upload_contect)
                    #f.close()
                    break
                else:
                    upload_contect = bytes.decode(receives[:upload_contect_end], 'utf-8')
                    print(upload_contect)     #Debug mode
                    #writefiledata(upload_filename, 'a', upload_contect)
                    #f = open(upload_filename, 'a')
                    #f.write(upload_contect)
                    #f.close()
                    break
            elif filestatus == True and datafind == True:
                residue_len = datalen - formdata_len
                if residue_len < boundary_len:
                    receives = receives + cl.recv(1024)
                    upload_contect_end = receives.find(b'\r\n--' + boundary + b'--\r\n')
                    upload_contect = bytes.decode(receives[upload_contect_beg:upload_contect_end], 'utf-8')
                    #writefiledata(upload_filename, 'w', upload_contect)
                    print(upload_contect)     #Debug mode
                    f = open(upload_filename, 'w')
                    f.write(upload_contect)
                    f.close()
                    break
                if i != 0:
                    print(bytes.decode(receives))
                    #writefiledata(upload_filename, 'a', bytes.decode(receives))
                    #f = open(upload_filename, 'a')
                    #f.write(receives)
                    #f.close()
        upload_status = '<p><b style="color: red;">上传成功！</b></p>'
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/upload.html") + len(upload_status))))
        f = open("/html/upload.html", 'r')
        for i in range(10):
            html_upload = f.read(536)
            if len(html_upload) == 0:
                break
            if html_upload.find("%s") != -1:
                cl.sendall(html_upload % (upload_status))
            else:
                cl.sendall(html_upload)
        f.close()
    elif data.find(b'GET /favicon.ico ') != -1:
        cl.sendall("%s" % (header_200 % (local_date, content_type[3], readfilesize("/html/favicon.ico"))))
        f = open("/html/favicon.ico", 'r')
        for i in range(10):
            icofile = f.read(536)
            if len(icofile) == 0:
                break
            cl.sendall(icofile)
        f.close()
    elif data.find(b'GET /off ') != -1:
        p4.value(0)
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/status.html") + len('已关灯！'))))
        f = open("/html/status.html", 'r')
        for i in range(10):
            html_result = f.read(536)
            if len(html_result) == 0:
                break
            if html_result.find("%s") != -1:
                cl.sendall(html_result % ('已关灯！'))
            else:
                cl.sendall(html_result)
        f.close()
        print("Controller(turn off):", addr)
    elif data.find(b'GET /on ') != -1:
        p4.value(1)
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/status.html") + len('已开灯！'))))
        f = open("/html/status.html", 'r')
        for i in range(10):
            html_result = f.read(536)
            if len(html_result) == 0:
                break
            if html_result.find("%s") != -1:
                cl.sendall(html_result % ('已开灯！'))
            else:
                cl.sendall(html_result)
        f.close()
        print("Controller(turn on):", addr)
    elif data.find(b'GET /synctime ') != -1:
        utc_time = ip_status("gmt")
        if utc_time != 'Unconnected':
            machine.RTC().datetime(utc_time[0:8])
            #print(time.localtime())     #Debug mode
            if utc_time[1] < 10:
                utc_time[1] = "%s%s" % ("0", utc_time[1])
            if (utc_time[4] + 8) < 10:
                utc_time[4] = "%s%s" % ("0", utc_time[4] + 8)
            else:
                utc_time[4] = str(utc_time[4] + 8)
            if utc_time[5] < 10:
                utc_time[5] = "%s%s" % ("0", utc_time[5])
            if utc_time[6] < 10:
                utc_time[6] = "%s%s" % ("0", utc_time[6])
            addtime = "时间已校准！</b><br><br><b>当前北京时间是：%s年%s月%s日 %s:%s:%s" % (str(utc_time[0]), utc_time[1], str(utc_time[2]), utc_time[4], utc_time[5], utc_time[6])
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(addtime)))))
            f = open("/html/status.html", 'r')
            for i in range(10):
                html_result = f.read(536)
                if len(html_result) == 0:
                    break
                if html_result.find("%s") != -1:
                    cl.sendall(html_result % (addtime))
                else:
                    cl.sendall(html_result)
            f.close()
        else:
            network_status = '时间校准失败，网络未连接！'
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(network_status)))))
            f = open("/html/status.html", 'r')
            for i in range(10):
                html_result = f.read(536)
                if len(html_result) == 0:
                    break
                if html_result.find("%s") != -1:
                    cl.sendall(html_result % (network_status))
                else:
                    cl.sendall(html_result)
            f.close()
    elif data.find(b'GET /') != -1:
        print(bytes.decode(data, 'utf-8'))
        len_beg = data.find(bytes("Host: ", 'utf-8')) + 6
        len_end = data.find(bytes("\r\n", 'utf-8'), len_beg)
        url_beg = data.find(bytes("GET ", 'utf-8')) + 4
        url_end = data.find(bytes(" HTTP/", 'utf-8'))
        msg_404 = "%s%s" % (bytes.decode(data[len_beg:len_end], 'utf-8'), bytes.decode(data[url_beg:url_end], 'utf-8')) ,t[0], t[1], t[2], t[3], t[4], t[5]
        cl.sendall("%s" % (header_404 % (local_date, content_type[0], readfilesize("/html/404.html") + len(msg_404))))
        f = open("/html/404.html", 'r')
            for i in range(10):
                html_404 = f.read(536)
                if len(html_404) == 0:
                    break
                if html_result.find("%s") != -1:
                    cl.sendall(html_404 % (msg_404))
                else:
                    cl.sendall(html_404)
            f.close()
    #print(data)     #Debug mode
    #print(addr,'client disconnected')     #Debug mode
    print('Close', addr)
    cl.close()