import openpyxl, json, re, glob
I='/home/claude/ingrid/v2'
wb=openpyxl.load_workbook('/home/claude/scripts/espace/ingrid_cal.xlsx')
MO={'nov':11,'déc':12}
def iso(lbl):
  m=re.search(r'(\d+)(?:er)?\s+(nov|déc)',lbl); return f'2026-{MO[m.group(2)]:02d}-{int(m.group(1)):02d}'
DAYS={'Lun':'Lundi','Mar':'Mardi','Mer':'Mercredi','Jeu':'Jeudi','Ven':'Vendredi','Sam':'Samedi','Dim':'Dimanche'}
def lab(s):
  w=s.split(' ',1); return (DAYS[w[0]]+' '+w[1]+'.') if w[0] in DAYS else s
REELS=glob.glob(I+'/reels/*.mp4')
def reel(where):
  m=re.search(r'Reel (\d+\w*) (nov|déc)',where); key=f'{m.group(1)}{m.group(2)}'
  for p in REELS:
    f=p.split('/')[-1].replace(' ','').replace('_','')
    if key in f: return p
car={'1':'BN','2':'ENVIES','3':'AVIS','4':'CADEAU'}
items=[]; ws=wb['1 Calendrier']
for k,r in enumerate(ws.iter_rows(min_row=5,values_only=True)):
  if not r[0] or 'terracotta' in str(r[0]): continue
  d,_,what,where,cap,ht=r[:6]
  cap=(cap or '').strip()+('\n\n'+ht if ht else '')
  title=where.split('›')[-1].strip(); title=re.sub(r'^(Reel \d+\w* \w+\.? – |\d )','',title); title=re.sub(r' \(\d+ \w+\.?\)$','',title)
  if 'Reel' in what:
    p=reel(where); items.append({'id':f'p{k:02d}','date':iso(d),'label':lab(d),'type':'Reel','title':title,'media':[p],'caption':cap,'tip':'🎵 Ajoute une musique au moment de publier. Partage aussi le reel en story.'})
  else:
    n=where.split('›')[-1].strip()[0]; fs=sorted(glob.glob(f'{I}/carrousels/{car[n]}-*.jpg'),key=lambda x:int(re.findall(r'-(\d+)',x)[-1]))
    items.append({'id':f'p{k:02d}','date':iso(d),'label':lab(d),'type':'Carrousel','title':title,'media':fs,'caption':cap,'tip':"🎵 Ajoute une musique au moment de publier. Sélectionne les images dans l'ordre."})
ws=wb['2 Stories']; seq=None; seqs=[]
SF={p.split('/')[-1].rsplit('.',1)[0].replace('_',' ').lower():p for p in glob.glob(I+'/stories/*.jpg')+glob.glob(I+'/stories2/*.jpg')}
SF['1 – fond forêt']=I+'/charte/templates_stories/1_Fond_foret.jpg'
ALIAS={'black november – story du vendredi':'black november vendredi','écrivez info':'ecrivez info','histoire 1':'histoire 1 je vous raconte','histoire 2':'histoire 2 800 calories','histoire 3':'histoire 3 on a ajuste','histoire 4':'histoire 4 vos questions'}
def sfile(w):
  w=w.split('›')[-1].replace('(ou toi face caméra)','').strip().lower(); w=ALIAS.get(w,w)
  return SF.get(w)
for r in ws.iter_rows(min_row=1,values_only=True):
  a,b,c=(list(r)+[None]*3)[:3]
  if a and not b and ' · ' in a and re.search(r'\d+\w*\s+(nov|déc)',a): seq={'head':a,'steps':[]}; seqs.append(seq)
  elif a and str(a).startswith('Story') and seq: seq['steps'].append((b,c))
for j,s in enumerate(seqs):
  d,t=s['head'].split(' · ',1)
  media=[]; steps=[]
  for b,c in s['steps']:
    f=sfile(b) if b and '›' in b else None
    if f and f not in media: media.append(f)
    steps.append({'what':('Image prête' if f else b),'text':c or ''})
  if not media: print('NO MEDIA',d)
  label=lab(d) if ' et ' not in d else 'Vendredis 20 et 27 nov.'
  items.append({'id':f's{j:02d}','date':iso(d),'label':label,'type':'Story','title':t,'media':media,'caption':'','steps':steps,'tip':"Une séquence de stories, à publier dans l'ordre. « Image prête » : le bouton l'envoie pour toi. Le reste, tu le filmes en quelques secondes."})
ws=wb['4 Réponses & bio']; rows=[r for r in ws.iter_rows(values_only=True) if any(r)]
rep=[{'label':r[0],'text':r[1],'copy':True} for r in rows[1:5]]; bio=rows[-1][1]
prix=[r for r in wb['3 Prix Black November'].iter_rows(values_only=True) if r[1] and '€' in str(r[1])]
spec={'client':{'slug':'ingrid','name':'Ingrid Franz · Énergéticienne','first':'Ingrid','tone':'tu'},
 'pack':{'name':'Pack Prêt à Poster · 1 mois','start':'2026-11-16','end':'2026-12-14','retouches':'1 tour inclus, dans les 7 jours après la livraison',
  'cadre':[['Ce que tu reçois',['Tes publications du mois : reels, carrousels et séquences de stories','Tous les textes, prêts à copier','Le calendrier : quoi publier, et quel jour','Ton profil revu : bio et couvertures à la une','Les vidéos sont livrées sans musique : tu ajoutes un son en publiant']],
   ['Les retouches',['1 tour de retouches inclus, dans les 7 jours après la livraison',"En un seul message : la publication concernée et ce qu'il faut changer",'Corrections livrées sous 48 h ouvrées']],
   ['Ce qui reste entre tes mains',["C'est toi qui publies : je n'accède pas à ton compte",'Répondre aux commentaires et aux messages','Les petites stories face caméra : ce sont elles qui créent la confiance']],
   ['Mon engagement',['Des contenus pros, prêts à publier, adaptés à ton activité',"Je ne promets ni vues, ni abonnés, ni clients : ils dépendent de ton offre, de ta régularité et des réseaux eux-mêmes"]]]},
 'contact':{'email':'studio.pretaposter@gmail.com','text':"Un fichier qui ne s'ouvre pas, une étape pas claire, une retouche ? Écris-moi, je te réponds sous 24 h ouvrées, du lundi au vendredi."},
 'profile':{'bio':bio,'covers':[{'label':n,'file':f'{I}/profil/{f}'} for n,f in [('Qui suis-je','1_Qui_suis_je.jpg'),('Mes soins','2_Mes_soins.jpg'),('Offres','3_Offres.jpg'),('Avis','4_Avis.jpg'),('Conseils','5_Conseils.jpg'),('Recettes','6_Recettes.jpg')]],
  'pinned':"Le carrousel Black November (18 nov.) : épingle-le jusqu'au 27 novembre. Sur la publication › ⋯ › Épingler."},
 'extras':[{'title':'Mes réponses types','intro':"À copier quand on t'écrit en message privé.",'rows':rep},
  {'title':'Mes prix Black November','intro':'Pour les achats faits le vendredi 20 ou le vendredi 27 novembre.','rows':[{'label':p[0],'text':f'{p[1]} → {p[2]}'} for p in prix]}],
 'items':items}
json.dump(spec,open('/home/claude/scripts/espace/ingrid.json','w'),ensure_ascii=False,indent=1)
for it in items: print(it['date'],it['label'],it['type'],it['title'][:38],len(it['media']),[m.split('/')[-1][:22] for m in it['media']][:3])
