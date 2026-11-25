"""
Mo hinh BACAP time-invariant (MILP), giai bang HiGHS qua scipy.optimize.milp.

Dung dung ky hieu trong tai lieu BACAP (tab "BACAP_MILP_time-invariant"):
  u  : unit cau cang, danh so tu 0 (moi unit dai DELTA m)
  t  : o gio, danh so tu 0 (moi o 1 gio, tinh tu thoi diem bat dau ke hoach t0)
  k  : so cau
  x[i,u,t,k] = 1 neu tau i do tu unit u, bat dau gio t, dung k cau

Rang buoc:
  (1) moi tau dung mot phuong an
  (2),(3),(6) duoc ap ngay khi tao danh sach phuong an hop le
  (4) moi o (u', t') co toi da mot tau
  (5) tong so cau dang dung o moi gio t' <= Q
"""
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


@dataclass
class Params:
    quay_length_m: float = 2000   # L
    delta_m: float = 100          # Delta, do dai mot unit
    Q: int = 22                   # tong so cau bo cua PNC
    rho: float = 25               # nang suat mot cau (luot/gio)
    k_min: int = 2                # K_i = {k_min, ..., k_max} cho moi tau
    k_max: int = 5
    step_h: int = 1               # do dai mot o thoi gian (gio); 1 = dung nhu tai lieu
    max_delay_h: Optional[int] = None   # None = mo hinh goc, khong gioi han cho; so = D_max (gio)
    horizon_h: Optional[int] = None     # H (gio), bat buoc khi max_delay_h = None
    time_limit_s: float = 300
    mip_gap: float = 0.0

    @property
    def M(self):
        return int(self.quay_length_m // self.delta_m)


def crane_range(p: Params):
    """K_i = {k_min, ..., k_max}, giong nhau cho moi tau."""
    return list(range(p.k_min, p.k_max + 1))


def build_and_solve(vessels: pd.DataFrame, fixed: pd.DataFrame, t0, p: Params, verbose=True):
    """
    vessels: tau can xep lich (cot: code, name, operator, service, etb, loa_m, W, dis, load, shift)
    fixed  : tau dang nam ben luc t0 (cot them: berth_start_m, etd, k_fixed)
    Tra ve DataFrame lich: moi tau mot dong (u, t, k, h, vi tri m, gio bat dau/ket thuc).
    """
    M = p.M
    hrs = lambda ts: (ts - t0).total_seconds() / 3600 / p.step_h   # tinh theo so o

    # ---- Tham so suy ra: a_i, s_i, K_i, h_ik --------------------------------
    V = []
    for _, r in vessels.iterrows():
        a = max(0, math.ceil(hrs(r["etb"])))
        s = math.ceil(r["loa_m"] / p.delta_m)
        K = crane_range(p)
        h = {k: math.ceil(r["W"] / (k * p.rho * p.step_h)) for k in K}
        V.append(dict(row=r, a=a, s=s, K=K, h=h, w=1.0))

    # khoang lap ke hoach H
    if p.max_delay_h is None:
        # mo hinh goc: khong gioi han cho, H do nguoi dung dat
        if p.horizon_h is None:
            raise ValueError("max_delay_h = None thi phai dat horizon_h (H, gio).")
        H = math.ceil(p.horizon_h / p.step_h)
        dmax = None
    else:
        # co gioi han cho D_max: H = max_i (a_i + D_max + max_k h_ik)
        dmax = p.max_delay_h // p.step_h
        H = max(v["a"] + dmax + max(v["h"].values()) for v in V)
    for _, r in fixed.iterrows():
        H = max(H, math.ceil(hrs(r["etd"])))

    # ---- O va cau da bi tau dang nam ben chiem ------------------------------
    occ = np.zeros((M, H), dtype=int)
    cranes_used = np.zeros(H, dtype=int)
    for _, r in fixed.iterrows():
        u0 = int(r["berth_start_m"] // p.delta_m)
        s = math.ceil(r["loa_m"] / p.delta_m)
        end = min(H, math.ceil(hrs(r["etd"])))
        occ[u0:u0 + s, 0:end] = 1
        cranes_used[0:end] += int(r["k_fixed"])

    # ---- Danh sach phuong an hop le (rang buoc 2, 3, 6) ---------------------
    cols = []   # (i, u, t, k)
    cost = []
    for i, v in enumerate(V):
        for k in v["K"]:                                       # (6) k thuoc K_i
            h = v["h"][k]
            t_hi = H if dmax is None else v["a"] + dmax
            for t in range(v["a"], t_hi + 1):                    # (2) t >= a_i
                if t + h > H:                                    # (3) t + h <= H
                    break
                for u in range(0, M - v["s"] + 1):               # (6) u <= M - s_i
                    # bo qua phuong an dam vao tau dang nam ben (giam kich thuoc)
                    if occ[u:u + v["s"], t:t + h].any():
                        continue
                    cols.append((i, u, t, k))
                    cost.append(v["w"] * (t + h - v["a"]) * p.step_h)  # thoi gian o cang (gio)
    n = len(cols)
    if verbose:
        print(f"  Tau: {len(V)} | unit M = {M} | H = {H} o x {p.step_h} gio | so bien x = {n:,}")

    # ---- Ma tran rang buoc --------------------------------------------------
    rows, cidx, vals = [], [], []
    lb, ub = [], []
    r_id = 0
    # (1) moi tau mot phuong an
    for i in range(len(V)):
        for j, c in enumerate(cols):
            if c[0] == i:
                rows.append(r_id); cidx.append(j); vals.append(1)
        lb.append(1); ub.append(1); r_id += 1

    # (4) moi o (u', t') toi da 1 tau ; (5) tong cau moi gio <= Q
    cell_row = {}
    crane_row = {}
    for j, (i, u, t, k) in enumerate(cols):
        s, h = V[i]["s"], V[i]["h"][k]
        for uu in range(u, u + s):
            for tt in range(t, t + h):
                key = (uu, tt)
                if key not in cell_row:
                    cell_row[key] = r_id; r_id += 1
                    lb.append(-np.inf); ub.append(1 - occ[uu, tt])
                rows.append(cell_row[key]); cidx.append(j); vals.append(1)
        for tt in range(t, t + h):
            if tt not in crane_row:
                crane_row[tt] = r_id; r_id += 1
                lb.append(-np.inf); ub.append(p.Q - cranes_used[tt])
            rows.append(crane_row[tt]); cidx.append(j); vals.append(k)

    A = coo_matrix((vals, (rows, cidx)), shape=(r_id, n)).tocsr()
    if verbose:
        print(f"  So rang buoc = {r_id:,} | so phan tu khac 0 = {A.nnz:,}")

    res = milp(
        c=np.array(cost, dtype=float),
        constraints=LinearConstraint(A, lb, ub),
        integrality=np.ones(n),
        bounds=Bounds(0, 1),
        options={"time_limit": p.time_limit_s, "mip_rel_gap": p.mip_gap, "disp": False},
    )
    if res.x is None:
        raise RuntimeError(f"Khong tim duoc loi giai: {res.message}")
    if verbose:
        gap = getattr(res, "mip_gap", None)
        gap_txt = f"{gap * 100:.2f}%" if gap is not None and np.isfinite(gap) else "n/a"
        print(f"  Trang thai: {res.message} | Z = {res.fun:.0f} gio | MIP gap = {gap_txt}")

    # ---- Doc loi giai -------------------------------------------------------
    out = []
    for j in np.where(res.x > 0.5)[0]:
        i, u, t, k = cols[j]
        v = V[i]; r = v["row"]; h = v["h"][k]
        out.append(dict(
            code=r["code"], name=r["name"], operator=r["operator"], service=r["service"],
            terminal=r.get("terminal", ""), etb=r["etb"],
            dis=r["dis"], load=r["load"], shift=r["shift"], W=r["W"], loa_m=r["loa_m"],
            a=v["a"], u=u, t=t, k=k, h=h * p.step_h, s=v["s"],
            start_m=u * p.delta_m, end_m=(u + v["s"]) * p.delta_m,
            start=t0 + pd.Timedelta(hours=t * p.step_h), end=t0 + pd.Timedelta(hours=(t + h) * p.step_h),
            wait_h=(t - v["a"]) * p.step_h, stay_h=(t + h - v["a"]) * p.step_h, fixed=False,
        ))
    sched = pd.DataFrame(out).sort_values("start").reset_index(drop=True)

    # them tau dang nam ben de ve chung tren mot hinh
    fx = []
    for _, r in fixed.iterrows():
        fx.append(dict(code=r["code"], name=r["name"], operator=r["operator"], service=r["service"],
                       dis=r["dis"], load=r["load"], shift=r["shift"], W=r["W"], loa_m=r["loa_m"],
                       k=int(r["k_fixed"]), start_m=r["berth_start_m"],
                       end_m=r["berth_start_m"] + math.ceil(r["loa_m"] / p.delta_m) * p.delta_m,
                       start=r["etb"], end=r["etd"], fixed=True))
    sched = pd.concat([pd.DataFrame(fx), sched], ignore_index=True)
    return sched, res, H
