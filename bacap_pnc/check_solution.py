"""
Kiem tra doc lap mot lich xep tau (khong dung lai cong thuc cua mo hinh):
  - (1) moi tau xuat hien dung mot lan
  - (2) khong cap truoc gio den (ETB)
  - (4) khong co hai tau chiem cung cho trong cung luc
  - (5) khong gio nao dung qua Q cau (tinh ca tau dang nam ben tu truoc)
  - (6) tau nam gon tren cau cang

run.py va random_case.py tu goi ham check() sau moi lan giai.
Co the chay rieng tren mot ket qua da luu:
  python check_solution.py random_n10_seed42      (doc output/random_n10_seed42.xlsx)
  python check_solution.py model_1125_4d          (doc output/model_1125_4d.xlsx)
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # luon chay trong thu muc chua file nay (bam Run o dau cung dung)
import sys

import pandas as pd


def check(sched: pd.DataFrame, etb: dict, Q=22, quay_len=2000, fixed: pd.DataFrame = None):
    """sched: lich do mo hinh xep. etb: {code: gio den}. fixed: tau dang nam ben (start, end, k).
    Tra ve danh sach vi pham (rong = hop le)."""
    bad = []
    dup = sched["code"][sched["code"].duplicated()].tolist()
    if dup:
        bad.append(f"Tau xuat hien hon mot lan: {dup}")
    for _, r in sched.iterrows():
        if pd.Timestamp(r["start"]) < pd.Timestamp(etb[r["code"]]).floor("h"):
            bad.append(f"Cap truoc gio den: {r['code']}")
        if r["start_m"] < 0 or r["end_m"] > quay_len:
            bad.append(f"Nho ra ngoai cau cang: {r['code']}")
    rows = sched[["code", "start_m", "end_m", "start", "end"]].values.tolist()
    if fixed is not None and len(fixed):
        rows += fixed[["code", "start_m", "end_m", "start", "end"]].values.tolist()
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                bad.append(f"Chong lan: {a[0]} va {b[0]}")
    allk = pd.concat([sched[["start", "end", "k"]],
                      fixed[["start", "end", "k"]] if fixed is not None and len(fixed) else None])
    for h in pd.date_range(sched["start"].min(), sched["end"].max(), freq="h"):
        used = allk[(allk["start"] <= h) & (allk["end"] > h)]["k"].sum()
        if used > Q:
            bad.append(f"Vuot Q luc {h}: {used} cau")
    return bad


def report(bad):
    if bad:
        print("KIEM TRA: CO VI PHAM")
        for b in bad:
            print("  -", b)
    else:
        print("KIEM TRA: tat ca rang buoc deu thoa (khong chong lan, khong vuot Q, khong cap truoc gio den, nam gon tren cau cang).")


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "random_n10_seed42"
    xls = pd.ExcelFile(f"output/{case}.xlsx")
    sched = pd.read_excel(xls, "schedule", parse_dates=["start", "end"])
    params = dict(pd.read_excel(xls, "parameters").values)
    fixed = pd.read_excel(xls, "fixed_vessels", parse_dates=["start", "end"]) if "fixed_vessels" in xls.sheet_names else None
    v = pd.read_csv("data/vessels_clean.csv", parse_dates=["etb"])
    etb = dict(zip(v["code"], v["etb"]))
    report(check(sched, etb, int(params.get("Q", 22)), float(params.get("quay_length_m", 2000)), fixed))
