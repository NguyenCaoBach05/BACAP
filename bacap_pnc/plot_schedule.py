"""
Ve lich tau theo kieu "Vessel Schedule (Graph)" cua PNC:
truc ngang la thoi gian (ngay, gio 6/12/18/24), truc doc la vi tri doc cau cang,
moi tau la mot hinh chu nhat ghi ma tau, ten, hang/tuyen, D/L/S va so cau.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd

# mau theo hang tau (giong cach PNC to mau)
OP_COLOR = {
    "MAE": "#22e6f0", "MSC": "#e3d769", "MCC": "#4cf05a", "HLC": "#f79b0a",
    "ONE": "#f3a3d3", "OOL": "#c3a3d9", "COS": "#e0e0e0", "KMD": "#9ec5ff", "XPR": "#ffb3a7",
    # hang tau trong du lieu BCT
    "SKR": "#b8e986", "HAS": "#ffd59e", "PCL": "#a0e7e5", "ILN": "#d7bde2", "COH": "#f5b7b1", "EMC": "#abebc6",
}
BERTHS = ["B4", "B5", "B6", "B7", "B8"]


def plot(sched: pd.DataFrame, t_from, t_to, title, path, quay_len=2000, Q=None):
    t_from, t_to = pd.Timestamp(t_from), pd.Timestamp(t_to)
    days = (t_to - t_from).days
    fig_h = 7.5 if Q is None else 9.5
    fig = plt.figure(figsize=(max(14, 2.6 * days), fig_h), dpi=130)
    if Q is None:
        ax = fig.add_subplot(111)
    else:
        gs = fig.add_gridspec(2, 1, height_ratios=[4.3, 1], hspace=0.08)
        ax = fig.add_subplot(gs[0]); axq = fig.add_subplot(gs[1], sharex=ax)

    berth_len = quay_len / len(BERTHS)
    # dai ben xen ke mau
    for b, name in enumerate(BERTHS):
        ax.axhspan(b * berth_len, (b + 1) * berth_len, color="#f4f6fa" if b % 2 else "white", zorder=0)
        ax.text(1.006, (b + 0.5) * berth_len, name, transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=11, fontweight="bold", color="#555")

    for _, r in sched.iterrows():
        x0, x1 = mdates.date2num(r["start"]), mdates.date2num(r["end"])
        y0, y1 = r["start_m"], r["end_m"]
        col = OP_COLOR.get(r["operator"], "#cccccc")
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=col,
                               edgecolor="#333", lw=0.6, alpha=0.55 if r.get("fixed") else 0.95,
                               hatch="//" if r.get("fixed") else None, zorder=2))
        tag = f" [{r['terminal']}]" if "terminal" in r and isinstance(r["terminal"], str) else ""
        label = (f"{r['code']}{tag}\n{r['name']}\n{r['operator']} / {r['service']}\n"
                 f"D:{int(r['dis'])} L:{int(r['load'])} S:{int(r['shift'])}\n"
                 f"{int(r['k'])} cranes")
        ax.text(max(x0, mdates.date2num(t_from)) + 0.01, y0 + 6, label, fontsize=6.3, va="top", ha="left", zorder=3,
                clip_on=True, linespacing=1.15)

    ax.set_ylim(quay_len, 0)          # ben dau o tren, giong PNC
    ax.set_xlim(mdates.date2num(t_from), mdates.date2num(t_to))
    ax.set_ylabel("Position along quay (m)")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%a"))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%H"))
    ax.tick_params(axis="x", which="minor", labelsize=7, colors="#777")
    ax.xaxis.tick_top(); ax.xaxis.set_label_position("top")
    ax.grid(axis="x", which="major", color="#888", lw=0.8)
    ax.grid(axis="x", which="minor", color="#ddd", lw=0.5)
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=34)

    if Q is not None:
        hours = pd.date_range(t_from, t_to, freq="h")
        used = [sched[(sched.start <= h) & (sched.end > h)]["k"].sum() for h in hours]
        axq.step(hours, used, where="post", color="#2b6fd6", lw=1.4, label="Cranes in use")
        axq.axhline(Q, color="#d33a3a", ls="--", lw=1.2, label=f"Q = {Q}")
        axq.set_ylim(0, Q + 3); axq.set_ylabel("Cranes")
        axq.legend(loc="upper right", fontsize=8); axq.grid(alpha=0.3)
        plt.setp(axq.get_xticklabels(), visible=False)

    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
