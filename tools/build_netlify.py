import re,shutil
s=open('/home/claude/farnesio/site/farnesio.html').read()
s=s.replace("const ART_URL='https://claude.ai/artifact/WGUa6aoQiZRF9RHyymsggd';","const ART_URL='https://lubens-farnesio.netlify.app/';")
m=re.match(r'(<title>.*?</title>\n)<meta name="claude:viewport-fit-sides" content="cover">\n((?:<link[^>]*>\n)+)',s,re.S)
s=s[m.end():]
head='''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Residencial Farnesio, Valladolid: 80 viviendas. Explora el edificio en 3D, consulta la disponibilidad, los planos de cada vivienda y cuánto sol recibe.">
<style>*,*::before,*::after{box-sizing:border-box}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
'''+m.group(1)+m.group(2)+'''</head>
<body>
'''
open('/home/claude/farnesio/netlify/index.html','w').write(head+s+'\n</body>\n</html>\n')
shutil.copy('/home/claude/farnesio/site/data.json','/home/claude/farnesio/netlify/data.json')
print('built')
