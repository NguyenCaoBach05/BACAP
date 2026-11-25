"""
Thu thap lich tau tu nhieu terminal Busan va gop vao kho du lieu chung.

Cach dung (trong venv da cai requirements):
    python collect_data.py                  # cao tat ca terminal bat trong CONFIG
    python collect_data.py --only PNC,HJNC  # chi cao vai terminal
    python collect_data.py --manual         # chi doc file Excel/CSV tai thu cong trong data/manual/
    python collect_data.py --no-web         # khong len mang, chi gop lai file raw + manual

Luong chay:
  1. Moi terminal -> mot ham "cao" tra ve bang theo CHUNG MOT schema (SCHEMA ben duoi).
  2. Moi lan cao luu nguyen ban vao data/raw/<TML>_<YYYYMMDD_HHMM>.csv (khong bao gio ghi de).
  3. Gop vao data/vessels_master.csv theo khoa  terminal + code (code = ma tau/chuyen day du).
       - chuyen chua co      -> them moi, first_seen = bay gio
       - chuyen da co        -> lay ban MOI NHAT (ETB/ETD/khoi luong co the doi), cap nhat last_updated
       - chuyen khong con trong lan cao nay -> GIU NGUYEN (tau da roi bang van la du lieu that)
     Cao 10 lan trong ngay cung khong sinh ban sao.
  4. Ghi nhat ky vao data/collect_log.csv (moi lan: bao nhieu dong moi / cap nhat / khong doi).
  5. Sau do chay  python prepare_data.py  de tao vessels_clean.csv cho mo hinh.

Terminal nao loi (mang, trang doi cau truc) chi in canh bao, cac terminal con lai van chay.
BCT la trang Nexacro, khong cao tu dong duoc: bam "Excel저장" tren trang, bo file vao data/manual/
(ten file bat dau bang BCT, vi du BCT_1125.xlsx) roi chay  python collect_data.py --manual
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # luon chay trong thu muc chua file nay
import argparse
import glob
import io
import json
import re
import sys
import time
from datetime import datetime, timedelta

import pandas as pd

# ============================ CONFIG (sua o day) ============================
TERMINALS = ["PNC", "HJNC", "PNIT", "HPNT"]  # BCT di qua file Excel thu cong (xem --manual)
DAYS_BACK = 1          # lay tu (hom nay - DAYS_BACK) ...
DAYS_AHEAD = 10        # ... den (hom nay + DAYS_AHEAD)
PAUSE_S = 2.0          # nghi giua cac trang cho lich su
TIMEOUT_S = 30
# ===========================================================================

SCHEMA = ["terminal", "code", "name", "operator", "service", "etb", "etd",
          "berth", "dis", "load", "shift"]
MASTER = "data/vessels_master.csv"
MASTER_COLS = SCHEMA + ["first_seen", "last_updated"]
KEY = ["terminal", "code"]

URL = {
    "PNC": "https://svc.pncport.com/eng/CMS/Ship/Info.pnc?mCode=MN014",
    "HJNC": "https://www.hjnc.co.kr/esvc/vessel/berthScheduleT/data",
    "PNIT": "https://www.pnitl.com/infoservice/vessel/vslScheduleList.jsp",
    "HPNT": "https://www.hpnt.co.kr/infoservice/vessel/vslScheduleListEng.jsp",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (student research; BACAP project)"}


# ------------------------------ tien ich chung ------------------------------
def to_int(x):
    """'1,316' -> 1316; rong/loi -> 0."""
    try:
        s = str(x).replace(",", "").strip()
        return int(float(s)) if s not in ("", "nan", "None", "-") else 0
    except ValueError:
        return 0


def parse_dt(s, ref):
    """Doc gio tu nhieu dang: '2026-11-24 00:01', '2026/11/24 00:01', '11-24 00:01', '24/11 00:01'.
    Neu thieu nam thi lay nam cua ngay tham chieu `ref` (xu ly qua Tet: thang nho hon ref thang 6+ -> nam sau)."""
    s = str(s).strip()
    if not s or s in ("nan", "None", "-"):
        return pd.NaT
    s = re.sub(r"\s+", " ", s.replace("/", "-").replace(".", "-"))
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?: (\d{1,2}):(\d{2}))?", s)
    if m:
        y, mo, d, h, mi = m.groups()
    else:
        m = re.match(r"^(\d{1,2})-(\d{1,2})(?: (\d{1,2}):(\d{2}))?", s)
        if not m:
            return pd.NaT
        a, b, h, mi = m.groups()
        a, b = int(a), int(b)
        mo, d = (a, b) if a <= 12 else (b, a)          # '11-24' = thang-ngay
        y = ref.year
        if mo < ref.month - 6:
            y += 1
    try:
        return pd.Timestamp(int(y), int(mo), int(d), int(h or 0), int(mi or 0))
    except ValueError:
        return pd.NaT


def finish(df, terminal):
    """Dua bang ve dung SCHEMA: gia tri chuan, bo dong khong co code/ETB."""
    for c in SCHEMA:
        if c not in df.columns:
            df[c] = "" if c not in ("dis", "load", "shift") else 0
    df["terminal"] = terminal
    for c in ["dis", "load", "shift"]:
        df[c] = df[c].map(to_int)
    for c in ["code", "name", "operator", "service", "berth"]:
        df[c] = df[c].astype(str).str.strip().replace({"nan": "", "None": ""})
    df = df[(df["code"] != "") & df["etb"].notna()].copy()
    df["etb"] = pd.to_datetime(df["etb"]).dt.strftime("%Y-%m-%d %H:%M")
    df["etd"] = pd.to_datetime(df["etd"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M").fillna("")
    return df[SCHEMA].drop_duplicates(KEY, keep="last").reset_index(drop=True)


def find_col(cols, *needles):
    """Tim ten cot chua mot trong cac tu khoa (khong phan biet hoa thuong / khoang trang)."""
    norm = {c: re.sub(r"[\s_()]+", "", str(c)).lower() for c in cols}
    for n in needles:
        n = re.sub(r"[\s_()]+", "", n).lower()
        for c, v in norm.items():
            if n in v:
                return c
    return None


def window(today=None):
    today = today or datetime.now()
    return (today - timedelta(days=DAYS_BACK)).date(), (today + timedelta(days=DAYS_AHEAD)).date()


# ------------------------------- cac scraper --------------------------------
def tables_from_html(html):
    return pd.read_html(io.StringIO(html), flavor="lxml")


def parse_pnc_html(html, ref):
    """Bang PNC: NAME, CODE, Voyage, operator, Service, Alongside, ETB, ETD, Berth No., CCT, Dis, Load, Shift."""
    for t in tables_from_html(html):
        t.columns = [" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
        cn, cc, cv, ce = (find_col(t.columns, k) for k in ("name", "code", "voyage", "etb"))
        if not (cn and cc and ce):
            continue
        out = pd.DataFrame({
            "name": t[cn],
            "code": t[cc].astype(str).str.strip() + (("-" + t[cv].astype(str).str.strip().str.zfill(3)) if cv else ""),
            "operator": t[find_col(t.columns, "operator", "oper")] if find_col(t.columns, "operator", "oper") else "",
            "service": t[find_col(t.columns, "service")] if find_col(t.columns, "service") else "",
            "etb": t[ce].map(lambda s: parse_dt(s, ref)),
            "etd": t[find_col(t.columns, "etd")].map(lambda s: parse_dt(s, ref)) if find_col(t.columns, "etd") else pd.NaT,
            "berth": t[find_col(t.columns, "berth")] if find_col(t.columns, "berth") else "",
            "dis": t[find_col(t.columns, "dis")] if find_col(t.columns, "dis") else 0,
            "load": t[find_col(t.columns, "load")] if find_col(t.columns, "load") else 0,
            "shift": t[find_col(t.columns, "shift")] if find_col(t.columns, "shift") else 0,
        })
        return finish(out, "PNC")
    raise RuntimeError("PNC: khong thay bang lich tau trong HTML (trang co the da doi cau truc)")


def scrape_pnc(sess, d0, d1):
    ref = datetime.now()
    r = sess.post(URL["PNC"], data={"STARTDATE": d0.strftime("%Y%m%d"), "ENDDATE": d1.strftime("%Y%m%d"),
                                    "ROWCOUNT": 500}, timeout=TIMEOUT_S)
    r.raise_for_status()
    return parse_pnc_html(r.text, ref)


def parse_hjnc_json(payload, ref):
    """JSON HJNC: payload['stringContent'] la chuoi JSON cua danh sach tau."""
    rows = payload.get("stringContent") or payload.get("content") or []
    if isinstance(rows, str):
        rows = json.loads(rows)
    out = pd.DataFrame([{
        "code": r.get("OPR_VOY") or r.get("VOY_NO"),
        "name": r.get("VSL_NM"),
        "operator": r.get("PTNR_CODE"),
        "service": r.get("OUT_LANE"),
        "etb": parse_dt(r.get("ETB"), ref),
        "etd": parse_dt(r.get("ATD") or r.get("ETD"), ref),
        "berth": r.get("BERTH_NO"),
        "dis": r.get("DIS_QTY"), "load": r.get("LOAD_QTY"), "shift": r.get("SHIFT_QTY"),
    } for r in rows])
    return finish(out, "HJNC") if len(out) else pd.DataFrame(columns=SCHEMA)


def scrape_hjnc(sess, d0, d1):
    ref = datetime.now()
    sess.get("https://www.hjnc.co.kr/esvc/vessel/berthScheduleT?lang=en", timeout=TIMEOUT_S)  # lay cookie
    frames, page = [], 1
    while True:
        r = sess.get(URL["HJNC"], params={"startDate": d0.isoformat(), "endDate": d1.isoformat(),
                                          "sort": "ETB", "dateType": "week", "route": "", "oper": "",
                                          "amount": 50, "page": page}, timeout=TIMEOUT_S)
        r.raise_for_status()
        payload = r.json()
        frames.append(parse_hjnc_json(payload, ref))
        if not payload.get("hasNext") or page >= 20:
            break
        page += 1
        time.sleep(PAUSE_S)
    return pd.concat(frames, ignore_index=True).drop_duplicates(KEY, keep="last")


def parse_gwangyang_style_html(html, terminal, ref):
    """PNIT / HPNT: Berth, OPR, VVD, Line VVD, Vessel name, ROUTE, ..., ATB(ETB), ATD(ETD), Dis, Load, Shift."""
    for t in tables_from_html(html):
        t.columns = [" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
        cvvd, cn = find_col(t.columns, "vvd"), find_col(t.columns, "vesselname", "vessel")
        cb = find_col(t.columns, "atb", "etb")
        if not (cvvd and cn and cb):
            continue
        cd = find_col(t.columns, "atd", "etd")
        out = pd.DataFrame({
            "code": t[cvvd],
            "name": t[cn],
            "operator": t[find_col(t.columns, "opr")] if find_col(t.columns, "opr") else "",
            "service": t[find_col(t.columns, "route")] if find_col(t.columns, "route") else "",
            "etb": t[cb].map(lambda s: parse_dt(s, ref)),
            "etd": t[cd].map(lambda s: parse_dt(s, ref)) if cd else pd.NaT,
            "berth": t[find_col(t.columns, "berth")] if find_col(t.columns, "berth") else "",
            "dis": t[find_col(t.columns, "dis")] if find_col(t.columns, "dis") else 0,
            "load": t[find_col(t.columns, "load")] if find_col(t.columns, "load") else 0,
            "shift": t[find_col(t.columns, "shift")] if find_col(t.columns, "shift") else 0,
        })
        return finish(out, terminal)
    raise RuntimeError(f"{terminal}: khong thay bang lich tau trong HTML")


def scrape_gwangyang_style(sess, d0, d1, terminal, tmn):
    ref = datetime.now()
    last_err = None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):      # trang co the nhan mot trong cac dang ngay
        params = {"tmnCod": tmn, "isSearch": "Y", "page": 1,
                  "strdStDate": d0.strftime(fmt), "strdEdDate": d1.strftime(fmt), "route": ""}
        try:
            r = sess.get(URL[terminal], params=params, timeout=TIMEOUT_S)
            r.raise_for_status()
            df = parse_gwangyang_style_html(r.text, terminal, ref)
            if len(df):
                return df
        except Exception as e:                           # thu dang ngay tiep theo
            last_err = e
        time.sleep(PAUSE_S)
    raise RuntimeError(f"{terminal}: khong lay duoc bang ({last_err})")


SCRAPERS = {
    "PNC": scrape_pnc,
    "HJNC": scrape_hjnc,
    "PNIT": lambda s, a, b: scrape_gwangyang_style(s, a, b, "PNIT", "P"),
    "HPNT": lambda s, a, b: scrape_gwangyang_style(s, a, b, "HPNT", "H"),
}


# ----------------------- doc file Excel/CSV tai thu cong ---------------------
def read_manual(path):
    """Doc file xuat tu trang terminal (Excel/CSV). Terminal lay tu tien to ten file: BCT_xxx.xlsx.
    Nhan dien cot bang tu khoa tieng Anh / tieng Han."""
    terminal = re.match(r"([A-Za-z]+)", os.path.basename(path)).group(1).upper()
    t = pd.read_csv(path) if path.lower().endswith(".csv") else pd.read_excel(path)
    ref = datetime.now()
    c = lambda *k: find_col(t.columns, *k)
    code = c("모선/항차", "vvd", "code")
    name, etb = c("모선명", "vesselname", "name"), c("접안예정", "etb", "atb")
    if not (code and name and etb):
        raise RuntimeError(f"{os.path.basename(path)}: khong nhan ra cot ma tau / ten tau / ETB. Cot hien co: {list(t.columns)}")
    out = pd.DataFrame({
        "code": t[code], "name": t[name],
        "operator": t[c("선사", "operator", "opr")] if c("선사", "operator", "opr") else "",
        "service": t[c("route", "service")] if c("route", "service") else "",
        "etb": t[etb].map(lambda s: parse_dt(s, ref)),
        "etd": t[c("출항예정", "etd", "atd")].map(lambda s: parse_dt(s, ref)) if c("출항예정", "etd", "atd") else pd.NaT,
        "berth": t[c("선석", "berth")] if c("선석", "berth") else "",
        "dis": t[c("양하", "dis")] if c("양하", "dis") else 0,
        "load": t[c("적하", "load")] if c("적하", "load") else 0,
        "shift": t[c("이적", "shift")] if c("이적", "shift") else 0,
    })
    return finish(out, terminal)


# ------------------------------- gop du lieu -------------------------------
def load_master():
    if os.path.exists(MASTER):
        return pd.read_csv(MASTER, dtype=str, keep_default_na=False)
    # lan dau: nap du lieu cu (2 file raw ban dau) de khong mat gi
    frames = []
    for tml, f in (("PNC", "data/pnc_schedule_raw.csv"), ("BCT", "data/bct_schedule_raw.csv")):
        if os.path.exists(f):
            d = pd.read_csv(f).assign(terminal=tml)
            frames.append(d[SCHEMA])
    if not frames:
        return pd.DataFrame(columns=MASTER_COLS)
    m = pd.concat(frames, ignore_index=True).astype(str)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    m["first_seen"] = m["last_updated"] = now
    print(f"[master] chua co {MASTER}: nap {len(m)} chuyen tu 2 file raw cu")
    return m[MASTER_COLS]


def merge_into_master(master, new):
    """Tra ve (master moi, so dong them, so dong cap nhat, so dong khong doi). Ban moi nhat thang."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new = new.astype(str)
    idx = {(r.terminal, r.code): i for i, r in master.iterrows()}
    added = updated = same = 0
    rows = master.to_dict("records")
    for r in new.to_dict("records"):
        k = (r["terminal"], r["code"])
        if k not in idx:
            rows.append({**r, "first_seen": now, "last_updated": now})
            idx[k] = len(rows) - 1
            added += 1
        else:
            old = rows[idx[k]]
            if any(str(old[c]) != r[c] for c in SCHEMA):
                rows[idx[k]] = {**r, "first_seen": old["first_seen"], "last_updated": now}
                updated += 1
            else:
                same += 1
    out = pd.DataFrame(rows, columns=MASTER_COLS)
    return out.sort_values(["etb", "terminal"]).reset_index(drop=True), added, updated, same


def save_snapshot(df, tag):
    os.makedirs("data/raw", exist_ok=True)
    path = f"data/raw/{tag}_{datetime.now():%Y%m%d_%H%M}.csv"
    df.to_csv(path, index=False)
    return path


def log_run(tml, n, added, updated, same, note=""):
    row = pd.DataFrame([{"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "terminal": tml,
                         "rows": n, "added": added, "updated": updated, "unchanged": same, "note": note}])
    row.to_csv("data/collect_log.csv", mode="a", header=not os.path.exists("data/collect_log.csv"), index=False)


# ----------------------------------- main -----------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="vd: PNC,HJNC")
    ap.add_argument("--manual", action="store_true", help="chi doc file trong data/manual/")
    ap.add_argument("--no-web", action="store_true", help="khong len mang")
    a = ap.parse_args()

    os.makedirs("data", exist_ok=True)
    os.makedirs("data/manual", exist_ok=True)
    master = load_master()
    todo = []                                    # (ten, DataFrame)
    problems = []

    if not (a.manual or a.no_web):
        import requests
        sess = requests.Session()
        sess.headers.update(HEADERS)
        d0, d1 = window()
        wanted = [t.strip().upper() for t in a.only.split(",")] if a.only else TERMINALS
        print(f"Khoang ngay: {d0} -> {d1}")
        for t in wanted:
            try:
                df = SCRAPERS[t](sess, d0, d1)
                print(f"[{t}] lay duoc {len(df)} chuyen")
                todo.append((t, df))
            except Exception as e:
                problems.append(f"{t}: {e}")
                print(f"[{t}] LOI: {e}")
            time.sleep(PAUSE_S)

    # file tai thu cong (BCT, hoac bat ky terminal nao khac)
    if not a.no_web or a.manual:
        for f in sorted(glob.glob("data/manual/*.xlsx") + glob.glob("data/manual/*.xls") + glob.glob("data/manual/*.csv")):
            if os.path.exists(f + ".done"):
                continue
            try:
                df = read_manual(f)
                print(f"[manual] {os.path.basename(f)}: {len(df)} chuyen ({df.terminal.iloc[0] if len(df) else '?'})")
                todo.append((df.terminal.iloc[0] if len(df) else "MANUAL", df))
                open(f + ".done", "w").write(datetime.now().isoformat())   # danh dau da nap, khong nap lai
            except Exception as e:
                problems.append(f"{os.path.basename(f)}: {e}")
                print(f"[manual] LOI {os.path.basename(f)}: {e}")

    for tml, df in todo:
        if df.empty:
            continue
        save_snapshot(df, tml)
        master, add, upd, same = merge_into_master(master, df)
        log_run(tml, len(df), add, upd, same)
        print(f"  -> {tml}: them {add}, cap nhat {upd}, khong doi {same}")

    master.to_csv(MASTER, index=False)
    print(f"\nKho tong: {len(master)} chuyen -> {MASTER}")
    print(master.groupby("terminal").size().to_string())
    if problems:
        print("\nCan chu y:")
        for p in problems:
            print(" -", p)
    print("\nBuoc tiep theo:  python prepare_data.py")


if __name__ == "__main__":
    main()
