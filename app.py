import streamlit as st
import requests
import re
import json
import unicodedata
from bs4 import BeautifulSoup
import classla

st.set_page_config(page_title="Hrvatski naglasci", page_icon="🇭🇷")
st.title("Hrvatski naglasci")

@st.cache_resource
def ucitaj_model():
    return classla.Pipeline('hr', processors='tokenize,pos,lemma')

@st.cache_resource
def ucitaj_bazu():
    with open(r"C:\Users\stipe\AppData\Local\Programs\Microsoft VS Code\hjp_baza.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ── POMOĆNE FUNKCIJE ─────────────────────────────────────────────────
def ukloni_dijakritike(rijec):
    zamjene = {
        'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': '',
        'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': '',
        ' ': '-'
    }
    return ''.join(zamjene.get(c, c) for c in rijec)

def ukloni_sve_dijakritike(tekst):
    zamjene = {
        'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': '',
        'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': ''
    }
    tekst = ''.join(zamjene.get(c, c) for c in tekst)
    tekst = unicodedata.normalize('NFD', tekst)
    tekst = ''.join(c for c in tekst if unicodedata.category(c) != 'Mn')
    return tekst.lower()

def ima_naglasak(tekst):
    zamjene = {
        'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': '',
        'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': ''
    }
    tekst = ''.join(zamjene.get(c, c) for c in tekst)
    nfd = unicodedata.normalize('NFD', tekst)
    return any(unicodedata.category(c) == 'Mn' for c in nfd)

def prepisni_naglasak(izvorna, naglasena_natuknica):
    naglasci_po_slogu = {}
    slog_brojac = 0
    for c in naglasena_natuknica:
        cisto = ukloni_sve_dijakritike(c)
        if cisto in "aeiour":
            slog_brojac += 1
            nfd = unicodedata.normalize('NFD', c)
            if len(nfd) > 1:
                naglasci_po_slogu[slog_brojac] = nfd[1:]
    if not naglasci_po_slogu:
        return izvorna
    rezultat = ""
    slog_brojac = 0
    for c in izvorna:
        cisto = ukloni_sve_dijakritike(c)
        if cisto in "aeiour":
            slog_brojac += 1
            if slog_brojac in naglasci_po_slogu:
                rezultat += unicodedata.normalize('NFC', c + naglasci_po_slogu[slog_brojac])
                continue
        rezultat += c
    return rezultat

def dohvati_naglasak(rijec):
    baza = ucitaj_bazu()
    rijec_url = ukloni_dijakritike(rijec)
    r = requests.get(f"https://rjecnik.hr/mreznik/{rijec_url}",
                     headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.find("h1")
        if h1 and "nije pronađena" not in h1.get_text():
            div = soup.find("div", class_="post-inner")
            if div:
                tekst = div.get_text().strip().split("\n")[0].strip()
                if ima_naglasak(tekst):
                    return tekst.split()[0]
    rezultat = baza.get(rijec_url)
    if rezultat:
        return rezultat["naglasak"]
    rezultat = baza.get(rijec)
    if rezultat:
        return rezultat["naglasak"]
    for i in range(1, 5):
        rezultat = baza.get(rijec_url + str(i))
        if rezultat:
            return rezultat["naglasak"]
        rezultat = baza.get(rijec + str(i))
        if rezultat:
            return rezultat["naglasak"]
    return None

bez_naglaska = {"se", "si", "ga", "mu", "ju", "joj", "ih", "im",
                "me", "mi", "te", "ti", "nas", "vas", "i", "u",
                "a", "na", "za", "od", "do", "po", "iz",
                "s", "sa", "k", "ka", "o", "ob", "pri", "kroz",
                "su", "je", "ću", "ćeš", "će", "ćemo", "ćete"}

rucni_rjecnik = {
    "bio": "bîo", "bila": "bíla", "bilo": "bílo", "bili": "bíli", "bile": "bíle",
    "budem": "bȕdem", "budeš": "bȕdeš", "bude": "bȕde", "budemo": "bȕdemo",
    "budete": "bȕdete", "budu": "bȕdu",
    "nisam": "nísam", "nisi": "nísi", "nije": "níje", "nismo": "nísmo",
    "niste": "níste", "nisu": "nísu",
    "jesam": "jȅsam", "jesi": "jȅsi", "jest": "jȅst", "jesmo": "jȅsmo",
    "jeste": "jȅste", "jesu": "jȅsu",
    "puno": "pȕno", "ali": "ȁli", "što": "štȍ", "ako": "ȁko",
    "tada": "tàdā", "tad": "tȁd",
    "sav": "sȁv", "sva": "svȁ", "sve": "svȅ", "svega": "svèga",
    "svemu": "svèmu", "svem": "svȅm", "svim": "svîm", "svime": "svíme", "svima": "svíma",
    "on": "ȏn", "ona": "ȏnā", "ono": "ȍnō", "oni": "ȏnī", "one": "ȏnē",
    "njega": "njȅga", "njemu": "njȅmu", "njim": "njîm", "njime": "njîme",
    "nju": "njȗ", "njih": "njȉh", "njima": "njȉma",
    "hrvatski": "hȑvātskī", "hrvatska": "Hȑvātskā", "hrvatsku": "Hȑvātskū",
    "hrvatskog": "hȑvātskōg", "hrvatskoj": "Hȑvātskōj",
    "zapošljavanje": "zapošljávanje", "vrijeme": "vrijéme",
    "zovem": "zòvēm", "zoveš": "zòvēš", "zove": "zòvē",
    "zovemo": "zòvēmo", "zovete": "zòvēte", "zovu": "zòvū",
    "strpljiv": "strpljiv", "strpljiva": "strpljiva",
    "strpljivi": "strpljivi", "strpljivo": "strpljivo",
    "četrnaest": "četr̀naest", "dvadeset": "dvádeset",
    "zahtijeva": "zahtijéva", "zahtijevam": "zahtijévam",
    "zahtijevaš": "zahtijévaš", "zahtijevamo": "zahtijévamo",
    "zahtijevaju": "zahtijévaju",
    "stresan": "strȅsan", "stresna": "strȅsna", "stresni": "strȅsnī", "stresnih": "strȅsnīh",
    "zapamtiti": "zàpāmtiti", "zapamtim": "zàpāmtīm", "zapamtiš": "zàpāmtīš",
    "zapamti": "zàpāmtī", "zapamtimo": "zàpāmtīmo", "zapamtite": "zàpāmtīte",
    "zapamte": "zàpāmtē", "zapamtio": "zàpāmtio", "zapamtila": "zàpāmtila",
    "zapamtilo": "zàpāmtilo", "zapamtili": "zàpāmtili", "zapamtile": "zàpāmtile",
}

def naglasi_tekst(tekst):
    nlp = ucitaj_model()
    doc = nlp(tekst)
    rezultat = []
    for sent in doc.sentences:
        for word in sent.words:
            if word.upos == "PUNCT":
                rezultat.append(word.text)
                continue
            if word.upos == "PROPN":
                rezultat.append(word.text)
                continue
            if word.text.lower() in rucni_rjecnik:
                naglasena = rucni_rjecnik[word.text.lower()]
                if ukloni_sve_dijakritike(naglasena.split()[0]) == ukloni_sve_dijakritike(word.text.lower()):
                    rezultat.append(naglasena.split()[0])
                else:
                    rezultat.append(prepisni_naglasak(word.text, naglasena))
                continue
            if word.text.lower() in bez_naglaska:
                rezultat.append(word.text)
                continue
            if word.upos == "AUX" and word.text.lower() in {"sam", "si", "je", "smo", "ste", "su", "bih", "bi", "bismo", "biste"}:
                rezultat.append(word.text)
                continue
            naglasak = dohvati_naglasak(word.lemma)
            if naglasak:
                naglasena = naglasak.split()[0]
                naglasena_cista = re.sub(r'\d+$', '', ukloni_sve_dijakritike(naglasena))
                if naglasena_cista == ukloni_sve_dijakritike(word.lemma):
                    rezultat.append(prepisni_naglasak(word.text, re.sub(r'\d+$', '', naglasena)))
                    continue
            if word.upos == "VERB":
                naglasak3 = dohvati_naglasak(word.lemma + " se")
                if naglasak3:
                    naglasena3 = naglasak3.split()[0]
                    naglasena3_cista = re.sub(r'\d+$', '', ukloni_sve_dijakritike(naglasena3))
                    if naglasena3_cista == ukloni_sve_dijakritike(word.lemma):
                        rezultat.append(prepisni_naglasak(word.text, re.sub(r'\d+$', '', naglasena3)))
                        continue
            naglasak2 = dohvati_naglasak(word.text.lower())
            if naglasak2:
                naglasena2 = naglasak2.split()[0]
                naglasena2_cista = re.sub(r'\d+$', '', ukloni_sve_dijakritike(naglasena2))
                if naglasena2_cista == ukloni_sve_dijakritike(word.text.lower()):
                    rezultat.append(prepisni_naglasak(word.text, re.sub(r'\d+$', '', naglasena2)))
                    continue
            rezultat.append(word.text)
    return " ".join(rezultat)

# ── SUČELJE ──────────────────────────────────────────────────────────
tekst = st.text_area("Unesite tekst:", height=200)

if st.button("Naglasi"):
    if tekst.strip():
        with st.spinner("Obrađujem..."):
            rezultat = naglasi_tekst(tekst)
        st.subheader("Rezultat:")
        st.write(rezultat)
    else:
        st.warning("Unesite tekst.")