"""Spec pour les calendriers Prêt à Poster format v2 (Marine, Manon)."""
import openpyxl, json, re, glob, os, sys, subprocess
MO={'nov':11,'déc':12}
DAYS={'Lun':'Lundi','Mar':'Mardi','Mer':'Mercredi','Jeu':'Jeudi','Ven':'Vendredi','Sam':'Samedi','Dim':'Dimanche'}
def iso(l): m=re.search(r'(\d+)(?:er)?\s+(nov|déc)',l); return f'2026-{MO[m.group(2)]:02d}-{int(m.group(1)):02d}'
def lab(s): w=s.split(' ',1); return (DAYS[w[0]]+' '+w[1]+'.') if w[0] in DAYS else s
def light(src, out):
  if not os.path.exists(out):
    d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src])); b=int(2.4*8*1000/d)-100
    for p in (1,2):
      a=['ffmpeg','-v','error','-y','-i',src,'-vf','scale=720:-2','-c:v','libx264','-preset','medium','-b:v',f'{b}k','-pass',str(p),'-passlogfile',out+'.log']
      a+= ['-an','-f','mp4','/dev/null'] if p==1 else ['-c:a','aac','-b:a','96k','-movflags','+faststart',out]
      subprocess.run(a,check=True)
  jpg=out[:-4]+'.jpg'
  if not os.path.exists(jpg): subprocess.run(['ffmpeg','-v','error','-y','-ss','1.2','-i',out,'-frames:v','1','-q:v','4',jpg],check=True)
  return out, jpg

def build(cfg):
  V=cfg['dir']; L=V+'/light'; os.makedirs(L,exist_ok=True)
  wb=openpyxl.load_workbook(cfg['xlsx']); ws=wb['1 Calendrier']
  items=[]; k=0
  for r in ws.iter_rows(values_only=True):
    if not r[0] or not re.match(r'^(Lun|Mar|Mer|Jeu|Ven|Sam|Dim) ',str(r[0])): continue
    d,_,what,msg,where,cap,ht=r[:7]; k+=1
    cap=(cap or '').strip()+('\n\n'+ht if ht else '')
    name=where.split('›')[-1].strip(); title=re.sub(r' \((\d+\w*) \w+\.?\)$','',re.sub(r'^(Reel \d+\w* \w+\.? – |\d+ )','',name))
    it={'id':f'p{k:02d}','date':iso(d),'label':lab(d),'caption':cap}
    if 'filmer' in what.lower():
      it.update(type='Reel à filmer',title=cfg.get('film_title','Ta vidéo face caméra'),media=[],tip='📱 À filmer par toi dans Instagram, en une seule prise.',steps=[{'what':'Comment faire','text':where}])
    elif 'Reel' in what:
      src=[p for p in glob.glob(V+'/reels/*.mp4') if p.split('/')[-1][:-4]==name][0]
      mp4,jpg=light(src,f'{L}/{it["id"]}.mp4'); cov=f"{V}/reels/Couverture – {name}.jpg"
      it.update(type='Reel',title=title,media=[mp4],cover=cov if os.path.exists(cov) else jpg,tip='🎵 Ajoute une musique au moment de publier. Partage aussi le reel en story.')
    elif 'Carrousel' in what:
      n=name.split(' ')[0]; fs=sorted(glob.glob(f"{V}/carrousels/{n} *.jpg"),key=lambda x:int(re.findall(r'– (\d+)\.jpg',x)[0]))
      it.update(type='Carrousel',title=title,media=fs,tip="🎵 Ajoute une musique au moment de publier. Sélectionne les images dans l'ordre.")
    else:
      it.update(type='Post',title=title,media=[f'{V}/posts/{name}.jpg'],tip='🎵 Ajoute une musique au moment de publier.')
    if msg: it['title']=it['title']
    items.append(it)
  ws=wb['2 Stories']; rows=[r for r in ws.iter_rows(values_only=True) if any(r)]
  SD=V+'/stories'
  def sf(x):
    x=x.split('›')[-1].strip(); p=f'{SD}/{x}.jpg'; return p if os.path.exists(p) else None
  if cfg['stories']=='simple':
    for j,r in enumerate(rows):
      if not r[0] or not re.match(r'^(Lun|Mar|Mer|Jeu|Ven|Sam|Dim) ',str(r[0])): continue
      p=sf(r[1]); items.append({'id':f's{j:02d}','date':iso(r[0]),'label':lab(r[0]),'type':'Story','title':r[1],'media':[p] if p else [],'caption':'','tip':r[2] or ''})
  else:
    seqs=[]; seq=None
    for r in rows:
      a,b,c=(list(r)+[None]*3)[:3]
      if a and not b and ' · ' in a and re.search(r'\d+\w*\s+(nov|déc)',a): seq={'head':a,'steps':[]}; seqs.append(seq)
      elif a and str(a).startswith('Story') and seq: seq['steps'].append((b,c))
    for j,s in enumerate(seqs):
      d,t=s['head'].split(' · ',1); media=[]; steps=[]
      for b,c in s['steps']:
        f=sf(b) if b and '›' in b else None
        if f and f not in media: media.append(f)
        steps.append({'what':'Image prête' if f else b,'text':'' if (c or '')=='Rien à ajouter' else (c or '')})
      items.append({'id':f's{j:02d}','date':iso(d),'label':lab(d),'type':'Story','title':t,'media':media,'caption':'','steps':steps,'tip':"Une séquence de stories, à publier dans l'ordre. « Image prête » : le bouton l'envoie pour toi."})
  # tarifs / réponses
  ws=wb['3 Mes tarifs']; tar=[]; 
  for r in ws.iter_rows(min_row=2,values_only=True):
    if r[0] and r[1]: tar.append({'label':r[0],'text':str(r[1])})
    elif r[0] and not r[1] and not str(r[0]).startswith('Tarifs'): tar.append({'label':'— '+r[0]+' —','text':''})
  ws=wb['4 Réponses & bio']; rr=[r for r in ws.iter_rows(values_only=True) if any(r)]
  rep=[]; bio=None; msg=None
  for i,r in enumerate(rr):
    if r[0]=='Ma bio Instagram (à copier)': bio=rr[i+1][1]
    elif r[0]=='Mon message à répéter partout': msg=rr[i+1][1]
    elif r[0] and r[1] and i>0: rep.append({'label':r[0],'text':r[1],'copy':True})
  extras=[{'title':'Mes réponses types','intro':"À copier quand on t'écrit en message privé.",'rows':rep}]
  if msg: extras.insert(0,{'title':'Mon message clé','intro':'La phrase à répéter partout : en story, en message, en vrai.','rows':[{'label':'Mon message','text':msg,'copy':True}]})
  extras.append({'title':'Mes tarifs','intro':'Ceux utilisés dans tes visuels. Un prix change ? Dis-le-moi.','rows':tar})
  dates=sorted(i['date'] for i in items)
  spec={'client':cfg['client'],'pack':{'name':'Pack Prêt à Poster · 1 mois','start':dates[0],'end':dates[-1],'retouches':'1 tour inclus, dans les 7 jours après la livraison','cadre':cfg['cadre']},
    'contact':{'email':'studio.pretaposter@gmail.com','text':"Un fichier qui ne s'ouvre pas, une étape pas claire, une retouche ? Écris-moi, je te réponds sous 24 h ouvrées, du lundi au vendredi."},
    'profile':{'bio':bio,'covers':[{'label':re.sub(r'^À la une \d+ – ','',os.path.basename(p)[:-4]),'file':p} for p in sorted(glob.glob(V+'/profil/À la une*.jpg'))]},'extras':extras,'items':items}
  if cfg.get('photo'): spec['profile']['photo']=cfg['photo']
  return spec
CADRE=[['Ce que tu reçois',['Tes publications du mois : reels, carrousels, posts et stories','Tous les textes, prêts à copier','Le calendrier : quoi publier, et quel jour','Ton profil revu : bio et couvertures à la une','Les vidéos sont livrées sans musique : tu ajoutes un son en publiant']],
 ['Les retouches',['1 tour de retouches inclus, dans les 7 jours après la livraison',"En un seul message : la publication concernée et ce qu'il faut changer",'Corrections livrées sous 48 h ouvrées']],
 ['Ce qui reste entre tes mains',["C'est toi qui publies : je n'accède pas à ton compte",'Répondre aux commentaires et aux messages','Les petites stories spontanées : ce sont elles qui créent le lien']],
 ['Mon engagement',['Des contenus pros, prêts à publier, adaptés à ton activité','Je ne promets ni vues, ni abonnés, ni clientes : ils dépendent de ton offre, de ta régularité et des réseaux eux-mêmes']]]
if __name__=='__main__':
  M='/home/claude/marine/v2'; N='/home/claude/manon/v2'
  for slug,cfg in {'marine':{'dir':M,'xlsx':'marine_cal.xlsx','stories':'simple','client':{'slug':'marine','name':"L'Atelier Nodena",'first':'Marine','tone':'tu'},'photo':f'{M}/profil/Monogramme (photo de profil).png','cadre':CADRE},
                   'manon':{'dir':N,'xlsx':'manon_cal.xlsx','stories':'seq','client':{'slug':'manon','name':"M' & Beauty",'first':'Manon','tone':'tu'},'cadre':CADRE,'film_title':'« Avec toi, j\'ai pu me le permettre »'}}.items():
    s=build(cfg); json.dump(s,open(f'{slug}.json','w'),ensure_ascii=False,indent=1)
    print('##',slug,len(s['items']),s['pack']['start'],s['pack']['end'])
    for it in sorted(s['items'],key=lambda i:i['date']): print(' ',it['date'],it['type'],it['title'][:40],len(it['media']))
