# -*- coding: utf-8 -*-
"""
Builds index-local.html: a self-contained copy of index.html with local-data.csv
baked in, so it opens by double-clicking (no server, no network).

WORKFLOW
    1. Edit the Headline column in local-data.csv (opens fine in Excel/Sheets).
    2. python build-local.py --offline
    3. Refresh index-local.html in your browser.

    python build-local.py            # pull fresh sheet data, KEEPING your headlines
    python build-local.py --offline  # just rebuild from local-data.csv (use while editing)

A plain fetch merges your Headline column back in by casino name, so refreshing the
sheet data never costs you your edits. Never edit index-local.html directly.
"""
import csv, io, os, sys

SHEET_CSV_URL = ("https://docs.google.com/spreadsheets/d/e/"
                 "2PACX-1vShE116l54ijfP1yQXXXgjnpK0ApBAhECrvztVYaTZF2-aH35tI-vl2S4VwB7XPpM5vgvL_-74U15xl"
                 "/pub?gid=333041365&single=true&output=csv")

HERE     = os.path.dirname(os.path.abspath(__file__))
SRC      = os.path.join(HERE, 'index.html')
SNAPSHOT = os.path.join(HERE, 'local-data.csv')
OUT      = os.path.join(HERE, 'index-local.html')
OFFLINE  = '--offline' in sys.argv


def read_csv(path):
    return list(csv.reader(io.open(path, encoding='utf-8')))


def write_csv(path, rows):
    f = io.open(path, 'w', encoding='utf-8', newline='')
    csv.writer(f, quoting=csv.QUOTE_MINIMAL).writerows(rows)
    f.close()


# --- 1. Refresh the snapshot, carrying the Headline column across ---
if OFFLINE:
    if not os.path.exists(SNAPSHOT):
        sys.exit("No local-data.csv yet. Run without --offline once while online.")
    print("Using local-data.csv as-is (offline).")
else:
    import urllib.request
    print("Fetching fresh sheet data...")
    req = urllib.request.Request(SHEET_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    fresh = list(csv.reader(io.StringIO(urllib.request.urlopen(req).read().decode('utf-8'))))

    # Preserve headlines from the previous snapshot, keyed by casino name.
    saved, prev_names = {}, set()
    if os.path.exists(SNAPSHOT):
        old = read_csv(SNAPSHOT)
        if 'Headline' in old[0]:
            iH, iN = old[0].index('Headline'), old[0].index('Casino Name')
            for r in old[1:]:
                if len(r) > max(iH, iN):
                    prev_names.add(r[iN])
                    if r[iH].strip():
                        saved[r[iN]] = r[iH]

    hdr = fresh[0]
    iName = hdr.index('Casino Name')
    if 'Headline' in hdr:                       # sheet gained the column -> it wins
        iH = hdr.index('Headline')
        merged = fresh
        print("Sheet now has its own Headline column; using it.")
    else:
        pos = hdr.index('Notes') if 'Notes' in hdr else len(hdr)
        merged = [hdr[:pos] + ['Headline'] + hdr[pos:]]
        for r in fresh[1:]:
            merged.append(r[:pos] + [saved.get(r[iName], '')] + r[pos:])
        iH = pos

    write_csv(SNAPSHOT, merged)
    names = set(r[iName] for r in merged[1:])
    added, gone = names - prev_names, prev_names - names
    if added: print("  new in sheet:  %s" % ", ".join(sorted(added)))
    if gone:  print("  removed:       %s" % ", ".join(sorted(gone)))
    blank = [r[iName] for r in merged[1:] if not r[iH].strip()]
    if blank: print("  NO HEADLINE:   %s" % ", ".join(blank))
    print("Saved local-data.csv (%d rows, headlines preserved)." % (len(merged) - 1))

csv_text = io.open(SNAPSHOT, encoding='utf-8').read()
if '</script' in csv_text.lower():
    sys.exit("Sheet data contains '</script' and cannot be embedded safely.")

# --- 2. Swap the network fetch for the embedded snapshot ---
html = io.open(SRC, encoding='utf-8').read()
old_fetch = """                const csvText = await loadSheetCsv();"""
new_fetch = """                // LOCAL BUILD: read the baked-in snapshot instead of fetching anything.
                const csvText = document.getElementById('localSheetData').textContent;"""
if html.count(old_fetch) != 1:
    sys.exit("Could not find the loadSheetCsv() call in index.html - did loadAndInit() change?")
html = html.replace(old_fetch, new_fetch)

# --- 3. Inject data + a banner so this is never mistaken for the live site ---
banner = """
<div style="background:#b45309;color:#fff;font:600 13px/1.4 Inter,system-ui,sans-serif;
            padding:8px 16px;text-align:center;letter-spacing:.01em;">
  LOCAL TEST BUILD &mdash; reading local-data.csv, not the live sheet.
  Edit headlines there, then re-run
  <code style="background:rgba(0,0,0,.25);padding:1px 5px;border-radius:3px;">python build-local.py --offline</code>
</div>
<script type="text/plain" id="localSheetData">""" + csv_text + """</script>
"""
if html.count('<body') != 1:
    sys.exit("Expected exactly one <body> tag.")
i = html.index('>', html.index('<body')) + 1
html = html[:i] + banner + html[i:]
html = html.replace('<title>', '<title>[LOCAL] ', 1)

io.open(OUT, 'w', encoding='utf-8', newline='').write(html)
print("Wrote index-local.html -> double-click to open.")
