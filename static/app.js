const $ = id => document.getElementById(id);
let previewUrl;
function status(text, error=false){$('status').textContent=text;$('status').className=error?'error':'';}
function clear(){ $('result').value='';$('download').disabled=true; }
$('file').onchange=()=>{clear();if(previewUrl)URL.revokeObjectURL(previewUrl);const f=$('file').files[0];$('preview').hidden=!f;if(f){previewUrl=URL.createObjectURL(f);$('preview').src=previewUrl;}status('Зображення обрано. Натисніть «Розпізнати».');};
async function run(demo){
 const f=$('file').files[0];if(!demo&&(!f||f.size>4*1024*1024)){status('Оберіть PNG/JPEG до 4 MiB.',true);return;}
 clear();$('demo').disabled=$('recognize').disabled=true;status(demo?'Завантажуємо імітацію відповіді…':'Google обробляє зображення…');
 try{const res=await fetch(demo?'/api/demo':'/api/ocr?feature='+encodeURIComponent($('feature').value),{method:'POST',headers:{'X-OCR-Client':'local-poc','Content-Type':'application/octet-stream'},body:demo?null:f});const data=await res.json();if(!res.ok)throw new Error(data.error||'Помилка запиту.');
 if(demo){$('file').value='';$('preview').src='/sample.png';$('preview').hidden=false;}
 $('result').value=data.text;$('download').disabled=!data.text;
 status(demo?data.notice:`Реальний API · ${data.elapsed_ms} мс · ${data.text.length} символів. ${data.text?'':'Тексту не знайдено.'}`);
 }catch(e){status(e.message,true);}finally{$('demo').disabled=$('recognize').disabled=false;}
}
$('demo').onclick=()=>run(true);$('recognize').onclick=()=>run(false);
$('result').oninput=()=>{$('download').disabled=!$('result').value;};
$('download').onclick=()=>{const url=URL.createObjectURL(new Blob([$ ('result').value],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='recognized_text.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
fetch('/api/status').then(r=>r.json()).then(d=>{$('connection').textContent=d.key_configured?'Ключ налаштовано. Доступність API перевіриться під час запиту.':'Ключ не налаштовано. Доступний демоприклад без запиту до Google.';}).catch(()=>{$('connection').textContent='Сервер недоступний.';});
