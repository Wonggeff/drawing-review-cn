# -*- coding: utf-8 -*-
"""Extract text from a .docx (and .xls via nothing) for review cross-checks."""
import sys, zipfile, re, os
sys.stdout.reconfigure(encoding="utf-8")
p = sys.argv[1]
z = zipfile.ZipFile(p)
names = [n for n in z.namelist() if n.endswith("document.xml")]
if not names:
    print("no document.xml"); sys.exit(1)
xml = z.read(names[0]).decode("utf-8", errors="replace")
# paragraph split
xml = xml.replace("</w:p>", "\n")
xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
txt = re.sub(r"<[^>]+>", "", xml)
txt = txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
lines = [l.strip() for l in txt.splitlines()]
out = "\n".join(l for l in lines if l)
outp = sys.argv[2] if len(sys.argv) > 2 else None
if outp:
    open(outp, "w", encoding="utf-8").write(out)
    print("wrote", outp, len(out), "chars")
else:
    print(out)
