import os
import torch
import re
import sys
import yaml
from transliterate import translit
from pathlib import Path

sys.path.append('ru_number_to_text-master')
from num2t4ru import num2text 

torch.set_grad_enabled(False)
device = torch.device('cpu')
torch.set_num_threads(4) 

with open('options.yml', 'r', encoding="utf-8") as y:   
    OPTIONS = yaml.safe_load(y)
DEFAULT = OPTIONS['syntez']
PARAMS = OPTIONS['params']

FILE_V3 = 'ru_v3.pt'

DIR_CACH    = 'cach'
if not os.path.isdir(DIR_CACH):
    os.mkdir(DIR_CACH)
    
SAMPLE_RATE = DEFAULT.get('sample_rate', 48000)
SPEAKER_V3 = DEFAULT.get('speaker', 'xenia')

def fdigit(txt):
    x = re.findall('[0-9]+', txt)
    x.sort(reverse=True)
    for i in x:
        txt = txt.replace(i, num2text(int(i)))
    return txt

def ftrans(txt):
    return translit(txt, 'ru')
  

def fabr(txt):
    for abr in re.findall('[А-ЯЁ]{2,}', txt):
        aabara = ''
        for i,a in enumerate(abr):
            if a in 'АЕЁИОУЫЭЮЯ':
                aabara += a+a.lower()
            elif a in 'КХШЩ':
                aabara += a+'а+а'
            elif a in 'ЛМНРСФ':
                aabara += 'ээ'+ a
            elif a in 'БВГДЖЗПТЦЧ':
                aabara += a+'ээ'
            elif a == 'Й': aabara += 'ё'
            aabara = aabara.replace('ээээ', 'эээ')
        txt = txt.replace(abr, f'<prosody rate="fast"> {aabara} </prosody>')
        
    return txt
 
def fecran(txt):
    for i in '[]{}|/':
        txt = txt.replace(i, f'\\{i}')
    return txt 
    
def fix(txt, *, digit=True, trans=True, abr=True, word=True, full=True): 
    txt = fecran(txt)
    if full:  txt = flegal(txt)
    if word:  txt = wlegal(txt)
    if digit: txt = fdigit(txt)
    if trans: txt = ftrans(txt)
    if abr:   txt = fabr(txt)
    return txt
    
def wlegal(txt):
    words = txt.split(' ')
    
    ilegals = {}
    if os.path.isfile('dict.yml'):
        with open('dict.yml', 'r', encoding="utf-8") as y:   
            ilegals = yaml.safe_load(y) 
        w = ilegals.get('word', {})
        
        for i in range(len(words)):
            if w.get(words[i]):
                words[i] = w[words[i]]
                
    return ' '.join(words)
    
def flegal(txt):
    ilegals = {}
    if os.path.isfile('dict.yml'):
        with open('dict.yml', 'r', encoding="utf-8") as y:   
            ilegals = yaml.safe_load(y) 
        f = ilegals.get('full', {})
        if f.get(txt):
            return f[txt]
    print(f)        
    return txt  
            
class V3:

    def __init__(self):
        self.model = torch.package.PackageImporter(FILE_V3).load_pickle("tts_models", "model")
        self.model.to(device)
        self.delete = []
        
    def get_name(self, speaker=None):
        name = SPEAKER_V3 if self.speakers().count(SPEAKER_V3) else self.speakers()[0]
        if speaker is None: return name
        if str(speaker).isdigit(): speaker = int(speaker)
        if type(speaker) == int:
            if speaker - 1 < len(self.speakers()): 
                return sorted(self.speakers())[speaker - 1]
        if type(speaker) == str and self.speakers().count(speaker): return speaker
        return None
        
    def speakers(self):
        return sorted(self.model.speakers)
    
    def get_size_cach(self):
        return sum(os.path.getsize(DIR_CACH+os.sep+f) for f in os.listdir(DIR_CACH) if os.path.isfile(DIR_CACH+os.sep+f))
    
    def rotate(self):
        size_cach = self.get_size_cach()
        mb = size_cach/1024/1024
        self.delete = []
        if mb > PARAMS.get('size_cach', 2):
            max_size = PARAMS.get('size_cach')*1024*1024
            li = {}
            for a in os.listdir(DIR_CACH):
                m = os.path.getmtime(DIR_CACH+os.sep+a)
                s = os.path.getsize(DIR_CACH+os.sep+a)
                f = DIR_CACH+os.sep+a
                li[f] = (m, s)
           
            li = sorted(li.items(), key=lambda x: x[1][0], reverse=True)
            
            for f, (m, s) in li:
               max_size -= s
               if max_size < 0:
                self.delete.append(f)
                os.remove(f)
            
    def __call__(self, text, path=None, 
                speaker=SPEAKER_V3, 
                sample_rate=SAMPLE_RATE, 
                accent=True, 
                yo=False, 
                digit=True, 
                trans=True, 
                abr=True,
                rw=False):
        print(text)
        bname = re.sub('[^\w\-_\. ]', '_', text)
        fname = os.path.join(DIR_CACH, f'{bname}.wav') if path is None else path
        if os.path.isfile(fname):
            if rw: 
                os.remove(fname)
            else:
                Path(fname).touch()
                return fname
        
        ssml  = '<speak>\r\n%s</speak>' % fix(text)
        print(ssml)
        self.model.save_wav(ssml_text=ssml,
                            speaker=self.get_name(speaker),
                            sample_rate=sample_rate,
                            audio_path=fname,
                            put_accent=accent,
                            put_yo=yo)
        self.rotate() 
        return fname               