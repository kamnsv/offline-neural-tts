import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
from cgi import parse_header, parse_multipart
from urllib.parse import parse_qs
import json
from syntez import *

syntez = V3()

FILE_INDEX = os.path.join('html', 'index.htm')

def start(serverPort=80, hostName='localhost'):   
    
    class WebServer(BaseHTTPRequestHandler):
        with open(FILE_INDEX, 'r', encoding="utf-8") as f:
            home = f.read()
            
        def do_GET(self):
            if '/favicon.ico' == self.path: 
                self.send_response(404)
                self.end_headers()
                return
            if len(self.path)>1: 
                fname = self.syntez({'text': unquote(self.path)[1:]})
                with open(fname, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'audio/wav')
                    self.end_headers()
                    self.wfile.write(f.read())          
            else:
                self.home_page()
                
                    
        def syntez(self, params={}):
            for k, v in DEFAULT.items():
                params[k] = params.get(k, v)
            return syntez(**params)
            
        def form(self):
            speakers = '<option>' + '</option><option>'.join([i for i in syntez.speakers()]) +'</option>' 
            speakers = speakers.replace('<option>%s' % DEFAULT['speaker'], '<option selected>%s' % DEFAULT['speaker'])

            sample_rates = '<option>' + '</option><option>'.join([str(i) for i in (8000, 24000, 48000)]) +'</option>' 
            sample_rates = sample_rates.replace('<option>%s' % DEFAULT['sample_rate'], '<option selected>%s' % DEFAULT['sample_rate'])

            options = {
                'speaker': speakers,
                'sample_rate': sample_rates
            }
            form = ''
            for k, v in DEFAULT.items():
                form += '<div>'
                if type(v) == bool:
                    form += f'<div><label><input type=checkbox %s name={k}>{k}</label><div>' % ['', 'checked'][v]
                else:
                    form += k + f': <select name={k}>' +  options[k] + '</select>'
                form += '</div>'
            return form
            
        def cach(self):
            cach = ''
            li = {}
            for a in os.listdir(DIR_CACH):
                m = os.path.getmtime(DIR_CACH+os.sep+a) 
                a = a[:-4]
                li[a] = m
            for a, m in sorted(li.items(), key=lambda x: x[1], reverse=True):
                cach += f'<li><a target=_blank href="/{a}">{a}</a></li>';
            return cach
            
        def home_page(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(bytes(self.home % {'form': self.form(), 'cach': self.cach()}, 'utf-8'))
        
        def parse_POST(self):
            ctype, pdict = parse_header(self.headers['content-type'])
            length = int(self.headers['content-length'])
            encoded  = self.rfile.read(length).decode('utf-8')
  
            postvars = {}
            if 'application/x-www-form-urlencoded' == ctype:
                postvars = parse_qs(encoded, encoding='utf-8')
            elif 'application/json' == ctype :
                postvars = json.loads(encoded)
            
            for k, v in postvars.items():
                if type(v) == list: v = v[0]
                postvars[k] = {'on': True, 'off': False}.get(v,  int(v) if v.isdigit() else v )
                            
            return postvars    
                       
        def do_POST(self):
            postdict = self.parse_POST()
            if postdict.get('text'):
                fname = self.syntez(postdict)[len(DIR_CACH)+1:-4]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(fname, 'utf-8'))
            else:
                self.send_response(301)
                self.send_header('Location', '/')
                self.end_headers()
        
            
    webServer = HTTPServer((hostName, int(serverPort)), WebServer)
    webServer.serve_forever()
        
if "__main__" == __name__ :  # ?????????? ???? ??????????????
    start(*sys.argv[1:])     