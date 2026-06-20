# STYLE_GUIDE.md — Manuel de révision Studio 21 A1+A2

Guide de style **obligatoire et commun** aux 4 sous-agents extracteurs.
Objectif : 4 fichiers parfaitement homogènes, fusionnables mécaniquement par l'orchestrateur.
**Respecte ce format au caractère près.** En cas de doute, choisis la clarté pour un élève qui révise seul.

---

## 0. Principes pédagogiques (à appliquer partout)

- **Vocabulaire en contexte (approche lexicale / chunks)** : on ne présente JAMAIS un mot tout seul. Un nom vient avec son article + pluriel, un verbe avec son régime et une collocation typique. Le but : retenir le mot **par l'usage**, via des mini-dialogues réalistes.
- **Grammaire pour réviser seul** : règle expliquée en **français clair**, puis exemples allemands **traduits**, puis **tableau récapitulatif complet** (aucune case vide), puis pièges.
- **Langue** : explications et consignes en **français** ; exemples, mots, dialogues en **allemand** avec **traduction française** systématique.
- **Ton** : pédagogique, direct, encourageant, jamais condescendant. Pas de blabla, on va à l'essentiel.

---

## 1. Format de fichier et conventions générales

- Fichier de sortie : **un seul fichier markdown** par agent, nommé `a1_partie1.md`, `a1_partie2.md`, `a2_partie1.md`, `a2_partie2.md`, dans le dossier `sources_md/`.
- Chaque **thème (Einheit)** = une section de niveau `##` au format **exact** :

  ```
  ## Thème : <Nom exact de l'Einheit> {#niveau=A1|A2 #einheit=<n> #pages=<x>-<y> #sujet=<mot-clé normalisé>}
  ```

  - `<Nom exact de l'Einheit>` : le titre tel qu'il apparaît dans le manuel (ex. `Kaffee oder Tee?`).
  - `#sujet=` : **mot-clé normalisé en minuscules** servant au dédoublonnage entre A1 et A2. Utilise IMPÉRATIVEMENT un mot de cette liste fermée (choisis le plus proche) :
    `salutations, cours-langue, pays-langues, logement, rendez-vous-heure, orientation-ville, metiers, ville-tourisme, voyage-vacances, nourriture, vetements-meteo, corps-sante, famille, transports, loisirs, medias, apparence-rencontres, campagne-ville, culture, monde-travail, fetes, sens-emotions, idees-inventions, europe-apprentissage, divers`
  - Exemple : `## Thème : Kaffee oder Tee? {#niveau=A1 #einheit=1 #pages=16-31 #sujet=salutations}`

- Chaque section thème contient TOUJOURS, dans cet ordre, ces 3 sous-parties (titres `###` exacts) :
  1. `### 🔤 Grammaire`
  2. `### 📖 Vocabulaire`
  3. `### 💬 Mise en contexte`

---

## 2. Format de la PARTIE GRAMMAIRE

Pour **chaque** point de grammaire du thème, un bloc de niveau `####` au format EXACT suivant :

```
#### G · <Nom canonique du point> {#cat=<categorie>}

**Règle.** <Explication en français, claire et détaillée.>

**Exemples.**
- <Phrase en allemand.> — *<Traduction française.>*
- <Phrase en allemand.> — *<Traduction française.>*
- <Phrase en allemand.> — *<Traduction française.>*  (3 à 5 exemples)

**Tableau.**
<un tableau markdown COMPLET — conjugaison entière, déclinaison entière, etc. Aucune case vide.>

**⚠️ Pièges.** <Exceptions et erreurs fréquentes. Si aucun : « — ».>
```

### 2.1 `#cat=` — catégorie pour le regroupement final
Choisis dans cette liste fermée (l'orchestrateur regroupera la grammaire PAR catégorie, pas par thème) :
- `groupe-nominal` (genre, articles définis/indéfinis, kein, possessifs, pronoms personnels)
- `cas` (Nominativ, Akkusativ, Dativ, Genitiv, déclinaison de l'article/nom)
- `conjugaison` (présent régulier/irrégulier, sein/haben, verbes à voyelle changeante, impératif)
- `modaux` (können, müssen, etc.)
- `verbes-particularites` (séparables, réfléchis, régime/Rektion, verbes de position)
- `temps-passe` (Perfekt, Präteritum, participe passé)
- `adjectif` (déclinaison épithète, comparatif/superlatif)
- `prepositions` (Akk, Dativ, Wechselpräpositionen)
- `syntaxe` (ordre des mots V2, questions, négation, subordonnées weil/dass/wenn, connecteurs)
- `divers`

### 2.2 Nom canonique du point de grammaire
Utilise un nom standard et stable (pour permettre le dédoublonnage A1/A2). Exemples de noms canoniques attendus :
`Le présent des verbes réguliers`, `Le présent de sein et haben`, `Les verbes à changement de voyelle (e→i/ie, a→ä)`, `L'article défini (der/die/das)`, `L'article indéfini (ein/eine) et kein`, `L'accusatif`, `Le datif`, `Les verbes de modalité`, `Les verbes à particule séparable`, `Le Perfekt (haben/sein + participe passé)`, `Le Präteritum de sein/haben/modaux`, `La déclinaison de l'adjectif épithète`, `Le comparatif et le superlatif`, `Les prépositions + accusatif`, `Les prépositions + datif`, `Les prépositions mixtes (Wechselpräpositionen)`, `La place du verbe (règle V2)`, `La négation (nicht / kein)`, `La subordonnée avec weil/dass/wenn`, `Les pronoms personnels`, `Les possessifs`, etc.

### 2.3 Exigences sur les tableaux
- **Conjugaison** : toujours les 6 personnes (ich, du, er/sie/es, wir, ihr, sie/Sie).
- **Cas / articles** : toujours les 3 genres + pluriel en colonnes, le(s) cas en lignes (ou inverse), **défini ET indéfini**.
- **Déclinaison de l'adjectif** : les 3 déclinaisons (après article défini / indéfini / sans article) si vues.
- **Prépositions** : préposition → cas gouverné → exemple.
- **Aucune case vide injustifiée.** Si une forme n'existe pas, écris « — ».

### 2.4 Marquage de progression A1→A2 (pour les agents A2 uniquement)
Si un point de grammaire d'A2 **étend** une règle déjà vue en A1 (ex. datif approfondi, Wechselpräpositionen, comparatif), commence le bloc par la ligne :
`> 🔺 **Extension A2** — approfondit la règle vue en A1.`
Cela aide l'orchestrateur à fusionner en montrant la progression.

---

## 3. Format de la PARTIE VOCABULAIRE

> ⚠️ **Exhaustivité** : relève TOUS les mots nouveaux du thème. Croise 3 sources : (1) le texte des dialogues/exercices, (2) la liste **Wortschatz / Wortfeld** de l'unité, (3) le glossaire en fin de manuel pour ce thème. Ne te limite pas au texte courant.

Quatre tableaux, dans cet ordre, avec ces titres `####` exacts. **Trie chaque tableau par ordre alphabétique.**

```
#### Verbes
| Verbe (infinitif) | Régime / particularités | Traduction |
|---|---|---|
| an\|rufen | + A (séparable) | appeler (au téléphone) |
| fahren | fährt, ist gefahren (irrég.) | aller (véhicule), conduire |
| warten | auf + A | attendre |

#### Noms
| Nom (avec article) | Pluriel | Traduction |
|---|---|---|
| der Tisch | -e | la table |
| die Wohnung | -en | l'appartement |
| das Haus | ¨-er | la maison |

#### Adjectifs & adverbes
| Mot | Comparatif/superlatif si irrég. | Traduction |
|---|---|---|
| gut | besser, am besten | bon / bien |
| teuer | — | cher |

#### Autres (prépositions, conjonctions, mots-outils, expressions)
| Mot / Expression | Catégorie | Traduction |
|---|---|---|
| weil | conjonction | parce que |
| zum Beispiel | expression | par exemple |
```

### Conventions de notation du vocabulaire
- **Noms** : toujours `der/die/das` + nom ; pluriel en notation courte (`-e`, `-en`, `-s`, `¨-er`, `¨-e`, `-` si invariable, `—` si singulier seul).
- **Verbes** : infinitif ; séparable noté avec `\|` (ex. `an\|rufen`) ; si irrégulier, donner `er-form, Perfekt` (ex. `fährt, ist gefahren`) ; régime noté `+ A`, `+ D`, `auf + A`, `mit + D`, etc.
- **Adjectifs** : forme de base ; comparaison seulement si irrégulière.
- **Traductions** : en français, concises. Si plusieurs sens, séparer par `;`.
- **Pas de doublon** à l'intérieur d'un même thème.
- Si un mot est **illisible dans le PDF/OCR**, écris la traduction `[?]` et signale-le à la fin du fichier dans une liste `<!-- INCERTAIN: ... -->`.

---

## 4. Format de la PARTIE MISE EN CONTEXTE

L'objectif : réemployer le **maximum** des mots du thème dans des situations réalistes.

```
### 💬 Mise en contexte

**Dialogue 1 — <titre court de la situation>**

> **Anna :** <réplique en allemand>
> **Ben :** <réplique en allemand>
> **Anna :** ...
> (6 à 12 répliques, naturelles et cohérentes)

*Traduction :*
> **Anna :** <traduction française>
> **Ben :** ...

**Phrases d'exemple** (réemploi ciblé du vocabulaire) :
- <Phrase allemande.> — *<Traduction.>*
- <Phrase allemande.> — *<Traduction.>*  (5 à 8 phrases)
```

- **1 à 2 dialogues** par thème, + le bloc de phrases d'exemple.
- Les dialogues doivent être **un vrai échange cohérent** (pas une suite de phrases artificielles).
- Mets en **gras** les mots-clés du thème réutilisés, pour l'œil.
- Réutilise en priorité les verbes/noms/adjectifs listés au §3.

---

## 5. Fin de fichier
Termine chaque fichier par :
```
<!-- FIN — agent=<a1p1|a1p2|a2p1|a2p2> ; thèmes traités=<n> ; mots de vocabulaire ≈ <N> -->
<!-- INCERTAIN: liste éventuelle des mots/pages douteux -->
```

---

## 6. Rappel de pied de page (info, pas à inclure par les agents)
Le PDF final portera en pied de page le nom du créateur **« Khalil Nacef »** + la pagination. Les agents n'ont rien à faire pour ça ; c'est géré à la mise en forme finale.
