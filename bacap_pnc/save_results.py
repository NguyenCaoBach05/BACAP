"""
Xuat ket qua ra file (chi dung khi SAVE_RESULTS = True trong run.py / random_case.py).

  output/<tag>.xlsx   cac sheet: schedule (lich xep), cac sheet them (vd. selected, fixed_vessels),
                      parameters (thong so da dung de chay)
  output/<tag>.png    anh lich (matplotlib) de dua vao bao cao
  output/<tag>.html   ban bieu do tuong tac, mo lai bang trinh duyet bat cu luc nao
"""
import pandas as pd

from plot_schedule import plot


def _excel_safe(df):
    """Excel khong nhan thoi gian co mui gio; cot thoi gian giu nguyen dang ngay-gio."""
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.tz_localize(None) if getattr(df[c].dt, "tz", None) else df[c]
    return df


def save_results(tag, sched, params: dict, extra_sheets: dict = None,
                 png=None, fig=None):
    """png: dict tham so cho plot_schedule.plot (sched, t_from, t_to, title, quay_len, Q).
    fig: hinh Plotly da tao (de luu .html)."""
    xlsx = f"output/{tag}.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        _excel_safe(sched).to_excel(w, sheet_name="schedule", index=False)
        for name, df in (extra_sheets or {}).items():
            _excel_safe(df).to_excel(w, sheet_name=name, index=False)
        pd.DataFrame(list(params.items()), columns=["parameter", "value"]).to_excel(
            w, sheet_name="parameters", index=False)
    saved = [xlsx]
    if png:
        plot(**png, path=f"output/{tag}.png")
        saved.append(f"output/{tag}.png")
    if fig is not None:
        fig.write_html(f"output/{tag}.html", include_plotlyjs="cdn")
        saved.append(f"output/{tag}.html")
    print("Da luu:", ", ".join(saved))
