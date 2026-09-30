from bs4 import BeautifulSoup
import re
from .land_math import fraction_value, parse_area

FRACTION_RE=re.compile(r'(\d+)\s*/\s*(\d+)\s*भाग')
AREA_RE=re.compile(r'^\s*\d+\s*-\s*\d+(?:\s*-\s*\d+)?')
IGNORE_OWNER_BITS=("वासी","वासीदेह","हर दो समभाग","हर तीन समभाग","हर चार समभाग","हर पांच समभाग","हर पाँच समभाग")

def clean(s):
    return " ".join(str(s or "").replace("\xa0"," ").split())

def extract_fraction(text):
    m=FRACTION_RE.search(text)
    return f"{m.group(1)}/{m.group(2)}" if m else ""

def parse_html(path):
    soup=BeautifulSoup(open(path,"r",encoding="utf-8",errors="ignore"),"html.parser")
    tables=soup.find_all("table")
    if len(tables)<2:
        raise ValueError("Jamabandi table was not found.")
    trs=tables[1].find_all("tr")
    rows=[]
    for tr in trs[1:]:
        cells=[clean(c.get_text(" ",strip=True)) for c in tr.find_all(["td","th"])]
        cells += [""]*(12-len(cells))
        rows.append(cells[:12])

    # Header metadata
    page_text=clean(soup.get_text(" ",strip=True))
    village=""
    mv=re.search(r'गांव\s*:\s*([^ ]+)', page_text)
    if mv: village=mv.group(1)

    owners=[]
    buf=[]
    for i,r in enumerate(rows, start=2):
        t=r[3]
        if not t: continue
        frac=extract_fraction(t)
        if frac:
            name=clean(" ".join(buf))
            name=re.sub(r'\bवासीदेह?\b','',name)
            name=re.sub(r'\bवासी\b','',name)
            name=re.sub(r'\bहर (?:दो|तीन|चार|पांच|पाँच) समभाग\b','',name)
            name=clean(name)
            if name:
                owners.append({"source_row":i,"name":name,"fraction":frac})
            buf=[]
        else:
            buf.append(t)

    # Cultivator/Khatauni groups. A new c2 starts a khatauni block.
    starts=[i for i,r in enumerate(rows) if r[1]]
    if not starts:
        starts=[0]
    cultivators=[]
    for si,start in enumerate(starts):
        end=starts[si+1] if si+1<len(starts) else len(rows)
        khatauni=clean(rows[start][1])
        group_rows=rows[start:end]
        # Skip the first group only if it has no meaningful cultivation data.
        current=None
        for local,jr in enumerate(group_rows):
            src=start+local+2
            c5,c7,c8=jr[4],jr[6],jr[7]
            if c5:
                frac=extract_fraction(c5)
                # Status/name marker. Keep every meaningful c5 line.
                txt=clean(c5)
                current={"khatauni":khatauni,"source_row":src,"text":txt,
                         "fraction":frac,"khasra":"","area":"","status":txt,
                         "deduct":False,"owner":""}
                cultivators.append(current)
            # Attach following khasra/area to the latest cultivation entry.
            if current and c7 and c8 and AREA_RE.match(c8):
                if not current["khasra"]:
                    current["khasra"]=clean(c7)
                    current["area"]=clean(c8)
            elif current and c7 and c8 and not current["area"]:
                # retain a specific-number row even when area formatting varies
                if c7 not in ("-----------------","कुल मजरुआ","कुल गैर मजरुआ"):
                    current["khasra"]=clean(c7)
                    current["area"]=clean(c8)
        # A c5 fraction line often follows the names it belongs to. It is useful
        # as a deduction candidate only when the user confirms it.

    # Remove obvious structural/status-only entries from the ledger.
    usable=[]
    for x in cultivators:
        t=x["text"]
        if t in {"हिस्सेदार","हिस्सेदारान","हक दहिन्दगान","हक गरिन्दा","काशत","वासीदेह",
                 "गैर मौरूसी","गैर मौरूसीयान","मुशत्रीयान","मालकान","मकबूजा"}:
            # Keep buyer status because it is evidence, but don't make it a standalone
            # deduction row without a name/area.
            if t=="मुशत्रीयान":
                continue
            continue
        usable.append(x)

    # Add buyer/status context from nearby rows.
    for x in usable:
        # conservative: only automatic deductions where purchaser status is present
        block=[z["text"] for z in cultivators if z["khatauni"]==x["khatauni"]]
        x["buyer_status"]="मुशत्रीयान" if "मुशत्रीयान" in block else ""
        x["deduct"]=bool(x["buyer_status"])
    return {"village":village,"owners":owners,"cultivators":usable}
