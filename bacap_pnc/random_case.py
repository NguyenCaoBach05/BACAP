"""
Boc ngau nhien N tau tu kho tau, cho mo hinh BACAP xep vi tri / gio / so cau, roi ve lich.

Cach dung:
  1. Sua khoi CAU HINH ngay ben duoi (so tau, seed, khoang ngay).
  2. Chay:  python random_case.py
     (hoac ghi de nhanh tren dong lenh:  python random_case.py --n 15 --seed 7)

Moi lan chay:
  - Bieu do tuong tac tu mo trong trinh duyet (re chuot vao tau de xem thong tin).
  - Tu kiem tra loi giai (khong chong lan, khong vuot Q, ...).
  - KHONG luu file nao, tru khi SAVE_RESULTS = True. Khi do luu vao output/:
      random_n10_seed42.xlsx  (sheet: schedule, selected, parameters)
      random_n10_seed42.png   (anh cho bao cao)
      random_n10_seed42.html  (bieu do tuong tac, mo lai bang trinh duyet)

Ghi chu:
  - Kho tau gom du lieu that cua 2 terminal o Busan New Port: PNC va BCT (cot "terminal").
    Tat ca tau duoc xep tren cau cang cua PNC (2.000 m, 22 cau) nhu mot kich ban gia dinh.
  - Gio den giu nguyen gio that (ETB). Chi boc tau co ETB trong [DATE_FROM, DATE_TO].
  - Cung N, SEED, DATE_FROM, DATE_TO va cung file du lieu => boc ra dung nhung tau do.
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # luon chay trong thu muc chua file nay (bam Run o dau cung dung)
import argparse
import time

import numpy as np
import pandas as pd

from bacap_milp import Params, build_and_solve
from check_solution import check, report
from interactive_chart import show_schedule
from save_results import save_results

# ============================ CAU HINH — sua o day ============================
N_VESSELS = 15              # so tau boc ngau nhien
SEED      = 42              # cung seed = boc ra dung nhung tau do (chay lai ra ket qua cu)
DATE_FROM = "2026-11-25"    # chi boc tau co gio cap (ETB) tu ngay nay ...
DATE_TO   = "2026-11-27"    # ... den truoc ngay nay
TERMINALS = ["PNC", "BCT", "HJNC", "PNIT", "HPNT"]  # lay tau tu terminal nao, vi du ["PNC"] neu chi muon tau PNC
SAVE_RESULTS = False        # True = luu Excel + anh + html vao output/; False = chi xem bieu do

# Thong so cang va mo hinh (de nguyen neu khong can phan tich do nhay)
Q          = 22             # tong so cau bo
RHO        = 25             # nang suat mot cau (luot/gio)
DELTA_M    = 100            # do dai mot unit cau cang (m)
STEP_H     = 1              # do dai mot o thoi gian (gio)
MAX_DELAY  = 24             # tau duoc cho toi da bao nhieu gio; None = khong gioi han (mo hinh goc)
HORIZON_H  = None           # H (gio); chi can khi MAX_DELAY = None, vi du 168
TIME_LIMIT = 300            # gioi han thoi gian giai (giay)
# ==============================================================================


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N_VESSELS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--date-from", default=DATE_FROM)
    ap.add_argument("--date-to", default=DATE_TO)
    args = ap.parse_args()

    df = pd.read_csv("data/vessels_clean.csv", parse_dates=["etb", "etd"])
    pool = df[df["usable"] & df["terminal"].isin(TERMINALS)
              & (df.etb >= pd.Timestamp(args.date_from)) & (df.etb < pd.Timestamp(args.date_to))]
    print(f"Kho tau trong khoang {args.date_from} -> {args.date_to}: {len(pool)} tau "
          f"({', '.join(f'{t} {int((pool.terminal == t).sum())}' for t in TERMINALS)})")
    if args.n > len(pool):
        raise SystemExit(f"Chi co {len(pool)} tau trong kho, khong boc duoc {args.n} tau. "
                         f"Giam N hoac mo rong DATE_FROM/DATE_TO.")

    # ---- Boc ngau nhien (co seed) ----------------------------------------------
    rng = np.random.default_rng(args.seed)
    idx = rng.choice(pool.index.to_numpy(), size=args.n, replace=False)
    picked = pool.loc[sorted(idx)].sort_values("etb").copy()
    tag = f"random_n{args.n}_seed{args.seed}"
    print(f"\nDa boc {args.n} tau (seed = {args.seed}):")
    print(picked[["terminal", "code", "name", "etb", "loa_m", "W"]].to_string(index=False))

    # ---- Giai mo hinh ------------------------------------------------------------
    p = Params(Q=Q, rho=RHO, delta_m=DELTA_M, step_h=STEP_H,
               max_delay_h=MAX_DELAY, horizon_h=HORIZON_H, time_limit_s=TIME_LIMIT)
    t0 = picked.etb.min().floor("D")          # bat dau ke hoach tu 0h ngay tau dau tien den
    no_fixed = picked.iloc[0:0].assign(k_fixed=[])   # khong co tau dang nam ben
    print(f"\nGiai mo hinh (t0 = {t0}) ...")
    tic = time.time()
    sched, res, H = build_and_solve(picked, no_fixed, t0, p)
    print(f"  Thoi gian giai: {time.time() - tic:.1f} giay")

    sched = sched.drop(columns=["fixed"])
    print("\nLich xep:")
    print(sched[["terminal", "code", "name", "start_m", "end_m", "start", "end", "k", "wait_h", "stay_h"]]
          .to_string(index=False))
    print(f"\nZ = {sched.stay_h.sum():.0f} gio | tong gio cho = {sched.wait_h.sum():.0f} gio")

    # ---- Kiem tra doc lap -----------------------------------------------------------
    report(check(sched, dict(zip(picked.code, picked.etb)), p.Q, p.quay_length_m))

    # ---- Bieu do tuong tac -------------------------------------------------------------
    t_end = sched["end"].max().ceil("D")
    title = f"BACAP — {args.n} randomly selected vessels (seed {args.seed}), scheduled on the PNC quay"
    fig = show_schedule(sched.assign(fixed=False), t0, t_end, title, quay_len=p.quay_length_m, Q=p.Q)

    # ---- Luu file (chi khi SAVE_RESULTS = True) ------------------------------------------
    if SAVE_RESULTS:
        params = dict(N_VESSELS=args.n, SEED=args.seed, DATE_FROM=args.date_from, DATE_TO=args.date_to,
                      TERMINALS=",".join(TERMINALS), Q=p.Q, rho=p.rho, delta_m=p.delta_m, step_h=p.step_h,
                      max_delay_h=p.max_delay_h, horizon_h=p.horizon_h, quay_length_m=p.quay_length_m,
                      Z_hours=float(sched.stay_h.sum()), solve_status=res.message)
        save_results(tag, sched, params, extra_sheets={"selected": picked}, fig=fig,
                     png=dict(sched=sched.assign(fixed=False), t_from=t0, t_to=t_end, title=title,
                              quay_len=p.quay_length_m, Q=p.Q))
    else:
        print("\n(Khong luu file. Muon luu Excel + anh: dat SAVE_RESULTS = True o dau file roi chay lai.)")


if __name__ == "__main__":
    main()
