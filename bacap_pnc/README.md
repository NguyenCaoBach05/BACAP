# BACAP trên dữ liệu thật ở Busan New Port (PNC + BCT)

Mô hình BACAP time-invariant (MILP) chạy trên lịch tàu PNC, rồi vẽ lịch theo kiểu
"Vessel Schedule (Graph)" của PNC để so với kế hoạch thật.

## 1. Cài đặt (một lần)

1. Cài **Python 3.10+** và **VS Code** (kèm extension *Python* của Microsoft).
2. Giải nén thư mục này, mở bằng VS Code: *File → Open Folder*.
3. Mở Terminal trong VS Code (*Ctrl + `*) rồi chạy:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Không cần cài solver riêng: `scipy` đã có sẵn bộ giải **HiGHS** (`scipy.optimize.milp`).

## 2. Chạy

```bash
python prepare_data.py           # chuẩn hóa data/pnc_schedule_raw.csv -> data/vessels_clean.csv
python run.py                    # case mặc định: 25/11/2026, 4 ngày
python check_solution.py model_1125_4d   # kiểm tra lại một kết quả ĐÃ LƯU (file .xlsx)
```

Mỗi lần chạy `run.py` hoặc `random_case.py`: **biểu đồ tương tác tự mở trong trình duyệt**
(rê chuột vào tàu để xem thông tin, kéo để phóng to, nhấp đúp để trở về, bấm tên hãng để ẩn/hiện),
và lời giải được **tự kiểm tra**. Mặc định **không lưu file**. Muốn lưu thì đặt `SAVE_RESULTS = True`
trong khối CẤU HÌNH ở đầu file. Khi đó kết quả nằm trong `output/`:

| File | Nội dung |
|---|---|
| `model_<case>.xlsx` | Sheet `schedule`, `comparison`, `fixed_vessels`, `pnc_plan`, `parameters` |
| `model_<case>.png` / `.html` | Lịch do mô hình xếp (ảnh cho báo cáo / bản tương tác) |
| `pnc_<case>.png` / `.html` | Kế hoạch thật của PNC, cùng kiểu vẽ để so sánh |
| `random_n10_seed42.xlsx` / `.png` / `.html` | Kết quả `random_case.py` (sheet `schedule`, `selected`, `parameters`) |

Đổi case hoặc tham số:

```bash
python run.py --start 2026-11-27 --days 3
python run.py --step 1 --delta 50 --time-limit 600   # sát tài liệu hơn nhưng chậm hơn nhiều
python run.py --rho 30 --Q 20                         # phân tích độ nhạy
```

## 2b. Bốc ngẫu nhiên N tàu: `random_case.py`

Sửa khối **CẤU HÌNH** ở đầu file `random_case.py`:

```python
N_VESSELS = 10              # số tàu bốc ngẫu nhiên
SEED      = 42              # cùng seed = bốc ra đúng những tàu đó
DATE_FROM = "2026-11-25"    # chỉ bốc tàu có ETB trong khoảng này
DATE_TO   = "2026-11-30"
TERMINALS = ["PNC", "BCT"]  # lấy tàu từ terminal nào
```

rồi chạy `python random_case.py` (hoặc nhanh: `python random_case.py --n 15 --seed 7`).
Biểu đồ tự mở; đặt `SAVE_RESULTS = True` để lưu `output/random_n10_seed42.xlsx`, `.png`, `.html`.

Giờ đến giữ nguyên giờ thật (ETB). Tất cả tàu, kể cả tàu BCT, được xếp trên cầu cảng của PNC
(2.000 m, 22 cẩu) như một kịch bản giả định. Khi viết báo cáo, ghi rõ: dữ liệu tàu lấy từ hai terminal
ở Busan New Port (PNC và BCT).

## 3. Dữ liệu và tham số

| Tham số | Giá trị | Nguồn |
|---|---|---|
| Chiều dài cầu cảng L | 2.000 m, 5 bến B4–B8 | DP World, Busan Metropolitan City |
| Số cẩu bờ Q | 22 | pncport.com, mục Equipment |
| Độ sâu | 17 m | pncport.com |
| Năng suất một cẩu ρ | 25 lượt/giờ | Giả định; khớp với năng suất bến trung vị 78 lượt/giờ trong kế hoạch PNC (khoảng 3 cẩu) |
| Lịch tàu PNC | 34 chuyến, 24/11–04/12/2026 | svc.pncport.com, Vessel Schedule (Text) |
| Lịch tàu BCT | 18 chuyến, 23/11–30/11/2026 | info.bct2-4.com, 선석 배정현황 (목록) |
| Kho tàu gộp | 52 chuyến, 49 chuyến đủ dữ liệu (PNC 31, BCT 18) | `data/vessels_clean.csv`, cột `terminal` |
| Chiều dài tàu LOA | 4 tàu tra trên mạng; còn lại ước lượng theo tuyến, tuyến chưa biết thì theo khối lượng hàng (<500 lượt: 150 m, <1.500: 200 m, còn lại 300 m) | Cột `loa_source`: `web` hoặc `est` |
| Số cẩu cho phép K_i | 2 đến min(6, LOA/60) | Giả định |
| Unit Δ, bước thời gian | 100 m, 2 giờ | Để mô hình giải được trong khoảng 30 giây |

Xử lý dữ liệu:
- `a_i` lấy bằng ETB của PNC (giờ sớm nhất được cập), vì lịch PNC không công bố giờ tàu đến neo.
- Tàu đang nằm bến lúc bắt đầu kế hoạch được giữ nguyên vị trí và giờ rời theo PNC.
- Tàu có khối lượng hàng bằng 0 (chưa khai báo) bị loại; giá trị Dis âm được đặt bằng 0.
- Bến B4–B8 quy đổi thành vị trí 0, 400, 800, 1.200, 1.600 m (giả định 5 bến dài bằng nhau).

**Nên cải thiện:** thay LOA ước lượng (`est`) trong `prepare_data.py` bằng LOA thật
(tra VesselFinder theo tên tàu), và hiệu chỉnh ρ nếu có số liệu năng suất cẩu của PNC.

## 4. Cấu trúc code

| File | Việc |
|---|---|
| `collect_data.py` | Cào lịch tàu PNC, HJNC, PNIT, HPNT (+ đọc Excel BCT tải tay), lưu bản thô, gộp vào `data/vessels_master.csv`, xử lý trùng |
| `prepare_data.py` | Chuẩn hóa kho tổng thành `vessels_clean.csv` cho mô hình |
| `bacap_milp.py` | Mô hình: sinh phương án hợp lệ (ràng buộc 2, 3, 6), dựng ràng buộc (1), (4), (5), giải bằng HiGHS |
| `plot_schedule.py` | Vẽ lịch kiểu PNC |
| `run.py` | Chạy một case chỉ với tàu PNC, so sánh với kế hoạch PNC |
| `random_case.py` | Bốc ngẫu nhiên N tàu (có seed) từ kho PNC + BCT, giải và vẽ |
| `check_solution.py` | Kiểm tra độc lập: mỗi tàu một lần, không chồng lấn, không vượt Q (tính cả tàu đang nằm bến), không cập trước giờ đến. Tự chạy sau mỗi lần giải |
| `interactive_chart.py` | Biểu đồ tương tác (Plotly), mở trong trình duyệt |
| `save_results.py` | Xuất Excel + ảnh + html khi `SAVE_RESULTS = True` |


## 5. Thu thập dữ liệu nhiều terminal (`collect_data.py`)

```
python collect_data.py                  # cào PNC, HJNC, PNIT, HPNT + nạp file tải tay trong data/manual/
python collect_data.py --only PNC,HJNC  # chỉ vài terminal
python collect_data.py --manual         # chỉ đọc Excel/CSV trong data/manual/
python prepare_data.py                  # bước sau: tạo data/vessels_clean.csv
```

- Mỗi lần cào lưu nguyên bản vào `data/raw/<TERMINAL>_<ngày_giờ>.csv`, không bao giờ ghi đè.
- Kho tổng `data/vessels_master.csv` có khóa `terminal + code`. Chuyến đã có thì lấy bản mới nhất (ETB/ETD/khối lượng) và cập nhật `last_updated`; chuyến mới thì thêm với `first_seen`; chuyến không còn trên trang thì giữ nguyên. Cào nhiều lần trong ngày không sinh bản sao.
- `data/collect_log.csv` ghi mỗi lần chạy: số dòng thêm / cập nhật / không đổi.
- **BCT** là trang Nexacro, không cào tự động được: vào info.bct2-4.com, mục 선석 배정현황 (목록), chọn khoảng ngày, bấm Excel저장, đổi tên file bắt đầu bằng `BCT` (ví dụ `BCT_1125.xlsx`), bỏ vào `data/manual/`, rồi chạy `python collect_data.py --manual`. File đã nạp được đánh dấu `.done` để không nạp lại.
- LOA thật: thêm file `data/loa_lookup.csv` (cột `name,loa_m`); `prepare_data.py` ưu tiên số này hơn ước lượng.
- Nếu một terminal đổi cấu trúc trang thì chỉ terminal đó báo lỗi, các terminal khác vẫn chạy.
