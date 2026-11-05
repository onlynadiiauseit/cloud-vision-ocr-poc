import json,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from app import Handler
class ServerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url=f'http://127.0.0.1:{cls.server.server_port}'
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def test_static(self):
  for path in ('/','/app.js','/style.css','/sample.png'):
   with urlopen(self.url+path) as r:self.assertEqual(r.status,200)
 def test_demo(self):
  with urlopen(Request(self.url+'/api/demo',data=b'',headers={'X-OCR-Client':'local-poc'})) as r:d=json.load(r)
  self.assertEqual(d['mode'],'demo');self.assertIsNone(d['elapsed_ms']);self.assertIn('125.50',d['text'])
 def test_post_protection(self):
  with self.assertRaises(HTTPError) as cm:urlopen(Request(self.url+'/api/demo',data=b''))
  self.assertEqual(cm.exception.code,403)
 def test_bad_image(self):
  with self.assertRaises(HTTPError) as cm:urlopen(Request(self.url+'/api/ocr',data=b'not image',headers={'X-OCR-Client':'local-poc'}))
  self.assertEqual(cm.exception.code,400)
 def test_unknown_route(self):
  with self.assertRaises(HTTPError) as cm:urlopen(self.url+'/../vision_client.py')
  self.assertEqual(cm.exception.code,404)
