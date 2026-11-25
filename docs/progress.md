# BACAP — Progress Log

File này ghi tiến độ dự án để Claude trên claude.ai (Project "Seminar") đọc được. Mỗi lần làm xong một việc thì thêm một mục mới ở đầu danh sách.

---

## 25/11/2026 — Biểu đồ tương tác + chỉ lưu file khi cần (Claude, claude.ai)

### Đã làm
1. File mới `interactive_chart.py` (Plotly): mỗi lần chạy `run.py` / `random_case.py`, biểu đồ tự mở trong trình duyệt. Rê chuột vào tàu xem tên, mã, terminal, hãng/tuyến, D/L/S, vị trí, giờ, số cẩu, giờ chờ; kéo để phóng to; bấm tên hãng để ẩn/hiện. Bên dưới là số cẩu đang dùng so với Q.
2. `SAVE_RESULTS = False` trong khối CẤU HÌNH của `run.py` và `random_case.py`: mặc định không lưu gì (để test nhiều lần). Đặt `True` thì `save_results.py` lưu `output/<tag>.xlsx` (nhiều sheet, có sheet `parameters`), `.png` (matplotlib) và `.html` (bản tương tác).
3. `run.py` có khối CẤU HÌNH (START, DAYS, Q, RHO, ...), mở 2 biểu đồ: lịch mô hình và kế hoạch PNC.
4. `check_solution.py` thành hàm `check()`, tự chạy sau mỗi lần giải; kiểm thêm "mỗi tàu đúng một lần" và tính cả cẩu của tàu đang nằm bến. Chạy riêng thì đọc file `.xlsx` đã lưu: `python check_solution.py model_1125_4d`.
5. `requirements.txt` thêm `plotly`, `openpyxl` → cần chạy lại `pip install -r requirements.txt`.

### Kiểm tra
- Chạy cả hai kịch bản ở hai chế độ lưu/không lưu: kết quả như cũ (random n10 seed42: Z = 142 giờ; case 1125_4d: 288 giờ), kiểm tra thỏa.
- Cố tình làm sai lịch (2 tàu đè nhau, 30 cẩu): `check()` bắt đủ lỗi.
- Phần Plotly chỉ kiểm tra được bằng bản giả lập trên máy ảo (không có thư viện plotly); **cần chạy thử thật trên laptop** để xem biểu đồ.

---

## 25/11/2026 — Thêm dữ liệu BCT và chức năng bốc ngẫu nhiên N tàu (Claude, claude.ai)

### Đã làm
1. Lấy lịch tàu BCT (info.bct2-4.com, 선석 배정현황 (목록)): 18 chuyến 23/11–30/11/2026, đủ ETB, ETD, Dis/Load/Shift, tên, hãng, tuyến (không có LOA, giống PNC). Lưu `data/bct_schedule_raw.csv`.
2. `prepare_data.py` gộp PNC + BCT thành kho tàu `data/vessels_clean.csv`, thêm cột `terminal` (ghi đúng nguồn). Kho: 52 chuyến, 49 đủ dữ liệu (PNC 31, BCT 18). LOA tuyến chưa biết ước lượng theo khối lượng hàng.
3. File mới `random_case.py`: khối CẤU HÌNH ở đầu file (N_VESSELS, SEED, DATE_FROM, DATE_TO, TERMINALS). Bốc ngẫu nhiên có seed, giờ đến giữ nguyên ETB thật, xếp trên cầu cảng PNC (2.000 m, Q = 22) như kịch bản giả định.
4. `run.py` giờ chỉ lấy tàu PNC (để so với kế hoạch PNC); `check_solution.py` kiểm tra được cả `random_*`; hình ghi nhãn [PNC]/[BCT].

### Kết quả thử `random_case.py` (N = 10, seed = 42, 25/11–30/11)
| Mục | Giá trị |
|:---|:---|
| Kho trong khoảng ngày | 33 tàu (PNC 17, BCT 16) |
| Đã bốc | 10 tàu (PNC 5, BCT 5) |
| Số biến x / phần tử khác 0 | 6.422 / 403.052 |
| HiGHS | Optimal, 7,4 giây |
| Z | 142 giờ, tổng giờ chờ 0 |
| `check_solution.py random_n10_seed42` | Tất cả ràng buộc đều thỏa |

- Như dự đoán: giữ giờ đến thật thì 10 tàu rải trong 5 ngày ít khi gặp nhau, không tàu nào phải chờ. Muốn bài toán "tranh" chỗ và cẩu hơn: tăng N hoặc thu hẹp DATE_FROM/DATE_TO.
- Case PNC cũ (`run.py`) chạy lại vẫn Z = 288 giờ, thỏa ràng buộc.

---

## 25/11/2026 — Dọn cấu trúc thư mục và chạy lại case 25/11 (Claude Code, VS Code)

### Đã làm
1. Đọc `CLAUDE.md` và `docs/BACAP_model.md`. Mô hình toán giữ nguyên, không sửa.
2. Gỡ lớp thư mục bị lồng: toàn bộ code chuyển từ `bacap_pnc/bacap_pnc/` lên `bacap_pnc/`. Không sửa code, vì mọi đường dẫn trong code (`data/...`, `output/...`) tính từ thư mục đang chạy, nên vẫn đúng khi chạy trong `bacap_pnc/`.
   - Còn sót `bacap_pnc/bacap_pnc/data/pnc_schedule_raw.csv`: lúc chuyển, file đang được một chương trình khác mở (Excel hoặc VS Code) nên không xóa được. Bản dùng thật đã nằm ở `bacap_pnc/data/`. Bách đóng file đó rồi xóa thư mục `bacap_pnc/bacap_pnc/`.
3. Tạo môi trường ảo `bacap_pnc/.venv` (Python 3.14.2) và cài `requirements.txt`: numpy 2.5.5, scipy 1.18.1, pandas 3.1.1, matplotlib 3.11.2.
4. Chạy `prepare_data.py`, `run.py`, `check_solution.py 1125_4d`. Không có lỗi.

### Kết quả case 1125_4d (25/11/2026, 4 ngày; Δ = 100 m, bước 2 giờ, chờ tối đa 24 giờ, Q = 22, ρ = 25)

| Mục | Giá trị |
|:---|:---|
| Tàu cần xếp / tàu đang nằm bến lúc t0 | 13 / 5 |
| Lưới | M = 20 unit × H = 96 ô (mỗi ô 2 giờ) |
| Số biến x | 10.240 |
| Số ràng buộc / số phần tử khác 0 | 1.823 / 791.821 |
| Trạng thái HiGHS | Optimal |
| Thời gian giải | 37,5 giây (lần trước ghi ~27 s; khác máy/phiên bản) |
| Z (tổng thời gian ở cảng) | **288 giờ** (kế hoạch PNC: 417 giờ) |
| `check_solution.py` | Tất cả ràng buộc đều thỏa |

- Lịch xếp ra (`output/schedule_model_1125_4d.csv`) giống hệt bản cũ, chỉ khác ký tự xuống dòng của file.
- Chỉ một tàu phải chờ: GUSTAV MAERSK chờ 2 giờ. 12 tàu còn lại vào bến ngay.
- Ghi chú dữ liệu khi chạy `prepare_data.py`: MAERSK SANA có Dis âm (−500) nên đặt bằng 0; COSCO HAMBURG, MSC CORINNA III, X-PRESS CASSIOPEIA chưa có khối lượng hàng (W = 0) nên bị loại.
- Vẫn chưa kết luận mô hình "tốt hơn PNC": mô hình bỏ qua lashing, di chuyển cẩu, safety distance.

### Cách chạy từ giờ
```bash
cd "F:/Bach/Lab/3. BACAP/bacap_pnc"
.venv\Scripts\activate
python prepare_data.py
python run.py
python check_solution.py 1125_4d
```

## 2026-11-25 (Claude chat) — collect_data.py
- Them `bacap_pnc/collect_data.py`: cao PNC (POST), HJNC (JSON), PNIT/HPNT (HTML GET); BCT doc tu Excel tai tay trong data/manual/ (--manual).
- Ban tho luu data/raw/<TML>_<ngay_gio>.csv; kho tong data/vessels_master.csv, khoa terminal+code, ban moi nhat thang, co first_seen/last_updated; log data/collect_log.csv.
- `prepare_data.py` doc vessels_master.csv (fallback 2 file raw cu) + data/loa_lookup.csv (name,loa_m) tuy chon.
- requirements.txt them requests, lxml. Da test parser tren HTML/JSON mau va dedup (chay 2 lan, ETB/khoi luong doi); CHUA test cao that tren mang cua Bach.
