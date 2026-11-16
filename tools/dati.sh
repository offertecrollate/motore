#!/usr/bin/env bash
# Storico prezzi nel ramo "dati", cifrato con il segreto DB_PASS (l'archivio è pubblico, i dati no).
#   bash tools/dati.sh carica          -> prezzi.db
#   bash tools/dati.sh salva "messaggio"
set -e
case "$1" in
  carica)
    git fetch -q origin dati 2>/dev/null || { echo "Primo avvio: storico vuoto"; exit 0; }
    if git cat-file -e origin/dati:prezzi.db.gz.enc 2>/dev/null; then
      git show origin/dati:prezzi.db.gz.enc | openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:DB_PASS | gunzip > prezzi.db
    else
      git show origin/dati:prezzi.db.gz | gunzip > prezzi.db
    fi
    ls -la prezzi.db ;;
  salva)
    [ -f prezzi.db ] || exit 0
    rm -rf /tmp/dati && mkdir -p /tmp/dati
    if [ -n "$DB_PASS" ]; then
      f=prezzi.db.gz.enc
      gzip -c prezzi.db | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:DB_PASS > /tmp/dati/$f
    else
      f=prezzi.db.gz; echo "ATTENZIONE: manca il segreto DB_PASS, storico salvato non cifrato"
      gzip -c prezzi.db > /tmp/dati/$f
    fi
    ls -la /tmp/dati
    cd /tmp/dati && git init -q -b dati
    git config user.name "Offerte Crollate"; git config user.email "offertecrollate@gmail.com"
    git add $f && git commit -qm "Storico prezzi $(date -u +%F_%H%M) ${2:-}"
    git push -q -f "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" dati ;;
  *) echo "uso: carica | salva"; exit 2 ;;
esac
