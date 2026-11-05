import base64,io,json,unittest
from urllib.error import HTTPError,URLError
from vision_client import build_payload,extract_text,recognize,VisionError,MAX_IMAGE_BYTES
IMAGE=b'\x89PNG\r\n\x1a\nexample'
class ClientTests(unittest.TestCase):
 def test_payload(self):
  p=build_payload(IMAGE,'DOCUMENT_TEXT_DETECTION')['requests'][0]
  self.assertEqual(base64.b64decode(p['image']['content']),IMAGE)
  self.assertEqual(p['features'],[{'type':'DOCUMENT_TEXT_DETECTION'}])
 def test_invalid_images(self):
  for data in (b'',b'not image',b'x'*(MAX_IMAGE_BYTES+1)):
   with self.subTest(size=len(data)),self.assertRaises(ValueError):build_payload(data)
 def test_unknown_feature(self):
  with self.assertRaises(ValueError):build_payload(IMAGE,'UNKNOWN')
 def test_full_text(self):self.assertEqual(extract_text({'responses':[{'fullTextAnnotation':{'text':'Привіт\n'}}]}),'Привіт\n')
 def test_fallback(self):self.assertEqual(extract_text({'responses':[{'textAnnotations':[{'description':'hello'}]}]}),'hello')
 def test_empty_text(self):self.assertEqual(extract_text({'responses':[{}]}),'')
 def test_embedded_error(self):
  with self.assertRaises(VisionError):extract_text({'responses':[{'error':{'code':3}}]})
 def test_invalid_structure(self):
  for v in ({},[],{'responses':[]},{'responses':[None]}):
   with self.subTest(v=v),self.assertRaises(VisionError):extract_text(v)
 def test_missing_key(self):
  with self.assertRaises(VisionError):recognize(IMAGE,api_key='')
 def test_http_contract(self):
  def opener(req,timeout):
   self.assertEqual(req.method,'POST');self.assertEqual(timeout,30);self.assertIn('key=test',req.full_url)
   self.assertEqual(json.loads(req.data)['requests'][0]['features'][0]['type'],'TEXT_DETECTION')
   return io.BytesIO(b'{"responses":[{"fullTextAnnotation":{"text":"OK"}}]}')
  r=recognize(IMAGE,api_key='test',opener=opener);self.assertEqual(r['text'],'OK');self.assertEqual(r['mode'],'live')
 def test_http_errors_hide_key(self):
  for code in (400,401,403,429,500,503):
   def fail(*a,**k):raise HTTPError('https://example?key=SECRET',code,'SECRET',{},None)
   with self.subTest(code=code),self.assertRaises(VisionError) as cm:recognize(IMAGE,api_key='SECRET',opener=fail)
   self.assertNotIn('SECRET',str(cm.exception))
 def test_network(self):
  for e in (URLError('secret'),TimeoutError()):
   def fail(*a,**k):raise e
   with self.subTest(e=e),self.assertRaises(VisionError):recognize(IMAGE,api_key='test',opener=fail)
 def test_bad_json(self):
  with self.assertRaises(VisionError):recognize(IMAGE,api_key='test',opener=lambda *a,**k:io.BytesIO(b'bad'))
