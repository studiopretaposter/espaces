# Espaces clientes Prêt à Poster

Un espace web par cliente = le livrable final (remplace les liens Drive).
En ligne : https://espaces-pretaposter.netlify.app/<slug>/
Dépôt : github.com/studiopretaposter/espaces (Netlify déploie automatiquement à chaque push sur main).

## Nouvelle cliente
1. Écrire `<slug>.json` (voir cecile.json) : client (slug, name, first, tone tu|vous), pack (dates, retouches, cadre),
   contact, profile (photo, nom, bio, couvertures, post épinglé), items (date ISO, label, type Reel|Carrousel|Post|Story,
   title, media[], cover pour les reels, caption, tip).
2. Vidéos : version légère 720p ~2,3 Mo (voir encodage dans l'historique), vignette .jpg en `cover`.
3. `python3 build_espace.py <slug>.json` → site/<slug>/
4. Copier site/<slug> dans /home/claude/espaces, commit, push. En ligne ~30 s après.
