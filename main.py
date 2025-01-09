#!/usr/bin/env python3

import os
import subprocess
import posixpath
import http.server
import urllib.request, urllib.parse, urllib.error
import html
import shutil
import mimetypes
import re
from io import BytesIO
from http.server import HTTPServer


class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    __version__ = "1.0"
    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, fileoutputpathname = self.deal_post_data()
        f = BytesIO()
        with open(fileoutputpathname, 'r') as file1:
            Lines = file1.read()
            f.write(bytes(str(Lines), "utf8"))

        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-Disposition", "attachment; filename=Output.txt")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def deal_post_data(self):
        content_type = self.headers['content-type']
        if not content_type:
            return (False, "Content-Type header doesn't contain boundary")
        boundary = content_type.split("=")[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
        fn2 = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")

        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith(b'\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                modifiedname = fn2[0] + ".txt"
                outputfilename = os.path.join(path, modifiedname)

                process = subprocess.Popen(["apkleaks", "-f", fn, "-o", outputfilename])
                process.wait()

                return (True, outputfilename)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpected Ends of data.")

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = BytesIO()
        displaypath = html.escape(urllib.parse.unquote(self.path))
        f.write(b'<!DOCTYPE html>')
        f.write((
            "<html>\n"
            "<head>\n"
            "<title>by TRHACKNON, APK Leaks Android Testing</title>\n"
            "<style>\n"
            "body { font-family: 'Courier New', monospace; background-color: #0d1117; color: #c9d1d9; margin: 0; padding: 0; text-align: center; }\n"
            "h2 { color: #58a6ff; text-shadow: 0 0 10px #58a6ff; }\n"
            "form { margin: 20px auto; padding: 20px; background: #161b22; border-radius: 10px; display: inline-block; box-shadow: 0 0 15px #238636; }\n"
            "input[type='file'], input[type='submit'] { margin: 10px; padding: 10px; border: none; border-radius: 5px; font-size: 14px; }\n"
            "input[type='submit'] { background-color: #238636; color: #fff; cursor: pointer; transition: background-color 0.3s ease; }\n"
            "input[type='submit']:hover { background-color: #2ea043; box-shadow: 0 0 10px #2ea043; }\n"
            "hr { border: 1px solid #30363d; margin: 20px 0; }\n"
            "ul { list-style-type: none; padding: 0; }\n"
            "li { margin: 5px 0; color: #58a6ff; }\n"
            "li:hover { color: #2ea043; cursor: pointer; text-shadow: 0 0 5px #2ea043; }\n"
            "img { max-width: 150px; margin-top: 20px; border-radius: 10px; box-shadow: 0 0 10px #58a6ff; }\n"
            "a { color: #58a6ff; text-decoration: none; }\n"
            "a:hover { color: #2ea043; text-shadow: 0 0 5px #2ea043; }\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            "<h2>APK Leak - Upload APK</h2>\n"
            "<center><img src='https://h.top4top.io/p_32961wh6f0.jpg' alt='APK Leak Logo'></center>\n"
            "<form method='POST' enctype='multipart/form-data'>\n"
            "<input type='file' name='apkfile' required><br>\n"
            "<input type='submit' value='Upload APK'>\n"
            "</form>\n"
            "<hr>\n"
            "<ul>\n"
        ).encode())

        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            f.write((
                f"<li><a href=\"{html.escape(linkname)}\">{html.escape(displayname)}</a></li>\n"
            ).encode())

        f.write(b"</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init()
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
    })


with HTTPServer(('', 8000), SimpleHTTPRequestHandler) as server:
    server.serve_forever()
