"""
Buoc 1: chuan hoa lich tau PNC thanh du lieu dau vao cho mo hinh BACAP.

Doc  : data/vessels_master.csv    (kho tau gop do collect_data.py tao; cot "terminal" ghi nguon that)
       data/loa_lookup.csv        (tuy chon: cot name,loa_m -> chieu dai tau that, uu tien hon uoc luong)
       Neu chua co vessels_master.csv thi doc 2 file raw cu (pnc_schedule_raw.csv, bct_schedule_raw.csv).
Ghi  : data/vessels_clean.csv     (du lieu da chuan hoa cho mo hinh)

Cot quan trong trong file ket qua:
  etb, etd      : gio cap / gio roi theo ke hoach PNC
  berth_start_m : vi tri dau tau theo ke hoach PNC (quy doi tu so ben B4..B8)
  loa_m         : chieu dai tau (m)
  terminal      : terminal goc cua du lieu (PNC hoac BCT)
  loa_source    : "web" = tra tren mang; "est" = uoc luong (can thay bang so that)
  W             : khoi luong lam hang (luot) = Dis + Load + Shift
  usable        : True neu du du lieu de dua vao mo hinh
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # luon chay trong thu muc chua file nay (bam Run o dau cung dung)
import math
import pandas as pd

# --- Thong so ben PNC -------------------------------------------------------
QUAY_LENGTH_M = 2000          # PNC: 5 ben, cau cang 2.000 m (DP World, Busan city)
BERTHS = ["B4", "B5", "B6", "B7", "B8"]
BERTH_LEN_M = QUAY_LENGTH_M / len(BERTHS)   # gia dinh 5 ben dai bang nhau: 400 m

# --- Chieu dai tau ------------------------------------------------------------
# LOA tra duoc tren mang (VesselFinder / MarineTraffic / Hafen Hamburg)
LOA_WEB = {
    "GERDA MAERSK": 367,
    "GUSTAV MAERSK": 366,
    "GUNVOR MAERSK": 367,
    "ANE MAERSK": 351,
}
# Uoc luong theo loai tuyen (GIA DINH, nen thay bang LOA that khi co)
SERVICE_CLASS_LOA = {
    # tuyen chinh xuyen Thai Binh Duong / A-Au: tau lon
    "GUSEC2E": 366, "GUSEC3": 366, "GUSWC2E": 366, "GUSWC4E": 366, "GUSWC5E": 366,
    "JADE": 366, "PHOENIX": 366, "AE19": 351, "AC3E": 367,
    # tuyen trung binh
    "CIX3": 300, "AC2S": 300, "ORIGAMI R": 300, "ORIENT E": 300, "GLX": 300,
    "ADD": 300, "KAGUYA": 300,
    # noi A / feeder
    "A14N": 200, "A14W": 200, "IA5N": 200, "IA88S": 200, "HP2": 200,
    "ANZL": 200, "A05": 200, "FI3W": 200,
}


def main():
    if os.path.exists("data/vessels_master.csv"):
        df = pd.read_csv("data/vessels_master.csv", keep_default_na=False)
        for c in ["dis", "load", "shift"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        df = df.replace({"etd": {"": pd.NA}})
    else:
        pnc = pd.read_csv("data/pnc_schedule_raw.csv").assign(terminal="PNC")
        bct = pd.read_csv("data/bct_schedule_raw.csv").assign(terminal="BCT")
        df = pd.concat([pnc, bct], ignore_index=True)
    df = df[df["etb"].astype(str) != ""].reset_index(drop=True)
    # LOA that do ban tu tra: data/loa_lookup.csv (name,loa_m)
    loa_user = {}
    if os.path.exists("data/loa_lookup.csv"):
        lk = pd.read_csv("data/loa_lookup.csv")
        loa_user = {str(n).strip().upper(): int(v) for n, v in zip(lk["name"], lk["loa_m"]) if pd.notna(v)}
    df["etb"] = pd.to_datetime(df["etb"])
    df["etd"] = pd.to_datetime(df["etd"])

    # vi tri ben theo ke hoach PNC (chi co nghia voi tau PNC; tau BCT de trong)
    df["berth_start_m"] = df["berth"].map(lambda b: BERTHS.index(b) * BERTH_LEN_M if b in BERTHS else None)

    # chieu dai tau
    def loa(row):
        if str(row["name"]).strip().upper() in loa_user:
            return loa_user[str(row["name"]).strip().upper()], "web"
        if row["name"] in LOA_WEB:
            return LOA_WEB[row["name"]], "web"
        if row["service"] in SERVICE_CLASS_LOA:
            return SERVICE_CLASS_LOA[row["service"]], "est"
        # tuyen chua biet: uoc luong theo khoi luong hang cua chuyen
        W = row["dis"] + row["load"] + row["shift"]
        return (150 if W < 500 else 200 if W < 1500 else 300), "est"
    df[["loa_m", "loa_source"]] = df.apply(lambda r: pd.Series(loa(r)), axis=1)

    # khoi luong lam hang
    df["loa_m"] = df["loa_m"].astype(int)
    notes = []
    for c in ["dis", "load", "shift"]:
        neg = df[c] < 0
        if neg.any():
            notes += [f"{n}: {c} am ({v}), dat = 0" for n, v in zip(df.loc[neg, "name"], df.loc[neg, c])]
            df.loc[neg, c] = 0
    df["W"] = df["dis"] + df["load"] + df["shift"]
    df["usable"] = df["W"] > 0
    for n in df.loc[~df["usable"], "name"]:
        notes.append(f"{n}: chua co khoi luong hang (W = 0), loai khoi mo hinh")

    # thong ke tham khao tu ke hoach PNC
    df["pnc_berth_hours"] = (df["etd"] - df["etb"]).dt.total_seconds() / 3600
    df["pnc_moves_per_hour"] = (df["W"] / df["pnc_berth_hours"]).round(1)

    df.to_csv("data/vessels_clean.csv", index=False)
    print(df[["terminal", "code", "name", "berth", "etb", "loa_m", "loa_source", "W",
              "pnc_berth_hours", "pnc_moves_per_hour"]].to_string(index=False))
    print("\nGhi chu du lieu:")
    for n in notes:
        print(" -", n)
    print(f"\nKho tau: {len(df)} chuyen, {int(df.usable.sum())} chuyen du du lieu "
          f"({', '.join(f'{t} {int((df.usable & (df.terminal == t)).sum())}' for t in sorted(df.terminal.unique()))})")
    pnc_ok = df.usable & (df.terminal == "PNC")
    if pnc_ok.any():
        print(f"Nang suat ben trung vi theo ke hoach PNC: {df.loc[pnc_ok, 'pnc_moves_per_hour'].median():.0f} luot/gio")


if __name__ == "__main__":
    main()
