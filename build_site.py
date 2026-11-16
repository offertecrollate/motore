"""Rigenera le pagine dei due domini con le offerte salvate (deals.json di ogni cartella).
offertecrollate.it -> site_it/   offertecrollate.ch -> site_ch/ (cartelle in config: site.countries.*.out_dir)"""
import os, yaml
from engine import site as S

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))["site"]
for country, ccfg in cfg["countries"].items():
    out = S.country_dir(cfg, country)
    os.makedirs(out, exist_ok=True)
    S.render_country(S._load(os.path.join(out, "deals.json")), country, ccfg, out)
    S.render_extras(cfg, country)
