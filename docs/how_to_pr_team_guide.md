# Pull Request (PR) Team Guide (for dummies)

Syfte: En enkel steg-för-steg guide för hur vi gör en ändring och får in den i `main` via Pull Request.

**Huvudregel:** Vi jobbar ALDRIG direkt på `main`.

---

## Superviktig regel (läs detta en gång och tatuera in i hjärnan)
Ändringar syns först i PR när de är:

1) **staged** (`git add ...`)  
2) **committed** (`git commit ...`)  
3) **pushed** (`git push`)

Om du hoppar över en av dem 'inget händer' (och det är normalt).

---

## Steg 0 Kolla läget (innan du gör något)
Kör alltid detta först:

```
git status
git branch
```
**Målet:** du ska se att du är på rätt branch och att din working tree är clean (eller åtminstone att du förstår vad som är ändrat)

## Förutsättningar (innan du börjar)
- Du har klonat repot och står i reporoten. 
- Din working tree är clean.  
**kör** `git status`

## Steg 1 Uppdatera `main`
Gå till `main` och hämta senaste från github:
```
git checkout main
git pull origin main
```
**Varför?**
- Du vill ALLTID utgå från senaste 'sanningen'


## Steg 2 Skapa ny branch
**Skapa en branch med ett tydligt namn:**  
`git checkout -b <typ>/<kort-beskrivning>`

**Exempel:**
- `docs/update-readme`
- `feat/clean-ads-keywords`
- `fix/null-title-bug`

## Steg 3 Gör din ändring
**Ändra filer, skapa nya filer etc etc**
**(PRO TIP: Kolla vad du faktiskt har gjort!)
```
git status
git diff
```

## Steg 4 Stage (Lägg till det du MENAR)
- A) Du har ändrat en befintlig fil (rekommenderat)  
`git add -p`  
**Varför?**   
- Du undviker att 'råka' lägga med skräp(data, secrets, random filer etc)  

- B) Du har skapat en NY fil(untracked)  
`git add -p` visar inte alltid nya filer. Lägg då till filen direkt:
```
git add path/to/new_file
```
**Exempel:**
```
git add docs/my_new_doc.md
git status
```

## Steg 5 Commit
**Commit-meddelandet ska vara kort och tydligt och följa vår standard (se team_workflow_and_rules.md)**
```
git commit -m "docs(scope): short description"
```

**Exempel:**
- docs(readme): clarify setup steps

- feat(clean): add keyword tagging

- fix(parser): handle empty description

## Steg 6 Pusha din branch
**Första gången du pushar branchen:**  
`git push -u origin <branch-namn>`  

**Exempel:**  
`git push -u origin docs/update-readme`

## Steg 7 Skapa Pull Request (PR) på Github
- Gå till github -> repo -> Pull requests - New pull request.  
- Base: `main`, Compare: din branch
- Fyll i PR mallen/checklistan: `pull_requests_checklist.md`
- Request review (som står i `team_workflow_and_rules.md`)

## Steg 8 Merge(Vi använder SQUASH)
**När PR är OK:**
- Välj Squash and merge
- Radera branchen (Delete branch)  

**Varför?**
- Squash = flera commits i branchen blir 1 commit på main -> ren historik.

## Steg 9 Synka lokalt och städa
**Efter merge:**
```
git checkout main
git pull origin main
```
**Radera din lokala branch:**
```
git branch -d <branch-namn>
```
**Städa remote-spår (Valfritt men cleant!)**  
```
git fetch --prune
```


### Vanliga problem och snabbfixar:
```
'No changes' när jag kör git add -p

Du har troligen bara nya (untracked) filer.

Kör:

git status
git add path/to/file

'Everything up-to-date' men jag ser inte min ändring på github

Du har troligen:

inte committat än, eller

du står på fel branch, eller

du pushade innan commit

Kolla:

git status
git branch
git log --oneline -n 5

'rejected (fetch first)' vid push

Remote har commits du saknar.

Kör:

git pull --rebase origin main


Försök sen pusha igen.

Jag råkade ändra på main

Skapa en branch direkt och fortsätt där:

git checkout -b fix/move-work-off-main
```

# THE END