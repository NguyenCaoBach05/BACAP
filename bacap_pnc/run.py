"""
Chay mot case BACAP tren lich tau PNC va so voi ke hoach that cua PNC.

Cach dung: sua khoi CAU HINH ben duoi roi chay  python run.py
(hoac ghi de nhanh:  python run.py --start 2026-11-27 --days 3)

Moi lan chay:
  - Mo 2 bieu do tuong tac trong trinh duyet: lich do mo hinh xep, va ke hoach that cua PNC.
  - Tu kiem tra loi giai.
  - KHONG luu file nao, tru khi SAVE_RESULTS = True. Khi do luu vao output/:
      model_<case>.xlsx  (sheet: schedule, comparison, fixed_vessels, pnc_plan, parameters)
      model_<case>.png, model_<case>.html   lich cua mo hinh
      pnc_<case>.png, pnc_<case>.html       ke hoach that cua PNC
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # luon chay trong thu muc chua file nay (bam Run o dau cung dung)
import argparse
import math
import time

import pandas as pd

from bacap_milp import Params, build_and_solve, crane_range
from check_solution import check, report
from interactive_chart import show_schedule
from plot_schedule import plot
from save_results import save_results

# ============================ CAU HINH — sua o day ============================
START        = "2026-11-25" # ngay bat dau ke hoach
DAYS         = 4            # so ngay
SAVE_RESULTS = False        # True = luu Excel + anh + html vao output/; False = chi xem bieu do

Q          = 22             # tong so cau bo
RHO        = 25             # nang suat mot cau (luot/gio)
DELTA_M    = 100            # do dai mot unit cau cang (m)
STEP_H     = 2              # do dai mot o thoi gian (gio)
MAX_DELAY  = 24             # tau duoc cho toi da bao nhieu gio
TIME_LIMIT = 120            # gioi han thoi gian giai (giay)
# ==============================================================================


def est_cranes(r, p):
    """So cau uoc luong cho tau trong ke hoach PNC (PNC khong cong bo so cau)."""
    hours = (r.etd - r.etb).total_seconds() / 3600
    return min(max(crane_range(r.loa_m, p)), max(p.k_min, math.ceil(r.W / (p.rho * hours))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=START)
    ap.add_argument("--days", type=int, default=DAYS)
    args = ap.parse_args()

    p = Params(delta_m=DELTA_M, rho=RHO, Q=Q, max_delay_h=MAX_DELAY,
               time_limit_s=TIME_LIMIT, step_h=STEP_H)
    t0 = pd.Timestamp(args.start)
    t_end = t0 + pd.Timedelta(days=args.days)
    case = f"{t0:%m%d}_{args.days}d"

    df = pd.read_csv("data/vessels_clean.csv", parse_dates=["etb", "etd"])
    df = df[df["usable"] & (df["terminal"] == "PNC")]   # chi dung tau PNC de so voi ke hoach PNC

    vessels = df[(df.etb >= t0) & (df.etb < t_end)].copy()        # tau can xep lich
    fixed = df[(df.etb < t0) & (df.etd > t0)].copy()               # tau dang nam ben luc t0
    fixed["k_fixed"] = [est_cranes(r, p) for r in fixed.itertuples()]

    print(f"Case {case}: {len(vessels)} tau can xep, {len(fixed)} tau dang nam ben luc {t0}")
    tic = time.time()
    sched, res, H = build_and_solve(vessels, fixed, t0, p)
    print(f"  Thoi gian giai: {time.time() - tic:.1f} giay")

    model = sched[~sched.fixed]
    fixed_rows = sched[sched.fixed]

    # so sanh voi ke hoach PNC (ETB -> ETD)
    pnc = vessels.set_index("code")
    cmp = model.set_index("code")[["name", "k", "wait_h", "stay_h"]].copy()
    cmp["pnc_stay_h"] = ((pnc["etd"] - pnc["etb"]).dt.total_seconds() / 3600).round(1)
    print("\nSo sanh thoi gian o ben (gio): mo hinh vs ke hoach PNC")
    print(cmp.to_string())
    print(f"\nTong: mo hinh {cmp.stay_h.sum():.0f} gio | PNC {cmp.pnc_stay_h.sum():.0f} gio")

    report(check(model, dict(zip(vessels.code, vessels.etb)), p.Q, p.quay_length_m, fixed=fixed_rows))

    # ---- Bieu do tuong tac ---------------------------------------------------------
    t_plot_end = max(model["end"].max(), t_end).ceil("D")
    title_m = f"Vessel schedule from the BACAP model — PNC, from {t0:%d/%m/%Y} ({args.days} days)"
    fig_m = show_schedule(sched, t0, t_plot_end, title_m, quay_len=p.quay_length_m, Q=p.Q)

    pv = pd.concat([fixed, vessels])
    pv = pv.assign(start=pv.etb, end=pv.etd, start_m=pv.berth_start_m,
                   end_m=pv.berth_start_m + pv.loa_m, fixed=pv.etb < t0,
                   k=[est_cranes(r, p) for r in pv.itertuples()])
    title_p = "Actual PNC plan — same period (crane counts are estimates)"
    fig_p = show_schedule(pv, t0, t_plot_end, title_p, quay_len=p.quay_length_m)

    # ---- Luu file (chi khi SAVE_RESULTS = True) ------------------------------------
    if SAVE_RESULTS:
        params = dict(START=args.start, DAYS=args.days, Q=p.Q, rho=p.rho, delta_m=p.delta_m,
                      step_h=p.step_h, max_delay_h=p.max_delay_h, quay_length_m=p.quay_length_m,
                      Z_model_hours=float(cmp.stay_h.sum()), Z_pnc_hours=float(cmp.pnc_stay_h.sum()),
                      solve_status=res.message)
        save_results(f"model_{case}", model.drop(columns=["fixed"]), params,
                     extra_sheets={"comparison": cmp.reset_index(), "fixed_vessels": fixed_rows,
                                   "pnc_plan": pv},
                     fig=fig_m,
                     png=dict(sched=sched, t_from=t0, t_to=t_plot_end, title=title_m,
                              quay_len=p.quay_length_m, Q=p.Q))
        plot(pv, t0, t_plot_end, title_p, f"output/pnc_{case}.png", quay_len=p.quay_length_m)
        fig_p.write_html(f"output/pnc_{case}.html", include_plotlyjs="cdn")
        print(f"Da luu them: output/pnc_{case}.png, output/pnc_{case}.html")
    else:
        print("\n(Khong luu file. Muon luu Excel + anh: dat SAVE_RESULTS = True o dau file roi chay lai.)")


if __name__ == "__main__":
    main()
