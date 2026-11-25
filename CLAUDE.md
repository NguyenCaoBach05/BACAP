# BACAP project — context for Claude Code

Đây là bối cảnh dự án do Claude (claude.ai, Project "Seminar") viết lại để Claude Code trong VS Code nắm được.
Đọc file này trước khi làm bất cứ việc gì trong thư mục này.

## Người dùng
- Bách, sinh viên Logistics & Supply Chain Management (không học kỹ thuật). Chat bằng tiếng Việt, xưng "bạn".
- Mục tiêu khi hỏi là HIỂU. Giải thích trực quan, từ dễ, có ví dụ số; KHÔNG dịch/nhắc lại tài liệu từng dòng.
- Văn phong giải thích ưa thích (học từ ChatGPT): mở bằng chỗ đang vướng → hình dung trước, công thức sau →
  mục có tiêu đề dạng câu hỏi → mỗi mục một ví dụ số với ký hiệu ghi rõ giá trị → ca đúng và ca sai →
  chốt một câu cần nhớ và điều dễ nhầm.
- Văn bản gửi giáo sư: tiếng Việt trang trọng. Tiêu đề trong tài liệu: tiếng Anh.

## Đề tài
"Development and Performance Evaluation of a MILP Algorithm for the Berth Allocation and Quay Crane Assignment
Problem (BACAP)", bản time-invariant. Báo cáo tuần cho lab của giáo sư.

Tài liệu chính (bản mới nhất, 25/11/2026): Google Doc "Lab", tab "BACAP_MILP_time-invariant"
https://docs.google.com/document/d/1BluX82gqHnzYNzRTN-CdCMByDeJsfhpqhhCGlhhmthg/edit?tab=t.zcnonlvr2shm
Bản sao nội dung (markdown + LaTeX): `docs/BACAP_model.md`. Các file .docx ở `F:/Bach/Lab` là bản cũ (u đánh số từ 1).

Góp ý của giáo sư (24/11): đừng rút gọn bài toán quá sớm; phải nêu toàn cảnh khó khăn thực tế
(ví dụ safety distance và non-crossing của quay crane) rồi mới chọn mức đơn giản. Tài liệu đã được viết lại theo
cấu trúc: tổng quan → khó khăn thực tế (5 nhóm) → literature → 5 level → chọn Level 1 + giả định → mô hình.

## Quy ước mô hình (phải giữ đúng)
- u: unit cầu cảng, **đánh số từ 0** (U = {0..M-1}); t: ô giờ từ 0 (T = {0..H-1}); tàu i đánh số từ 1.
- x[i,u,t,k] ∈ {0,1}: tàu i đỗ từ unit u, bắt đầu ô giờ t, dùng k cẩu (cố định suốt thời gian làm hàng).
- s_i = ceil(l_i/Δ); h_ik = ceil(W_i/(k·ρ)). **h_ik (giờ làm hàng) ≠ H (độ dài khoảng lập kế hoạch).**
- Mục tiêu: min Σ_i w_i Σ_u Σ_t Σ_k (t + h_ik − a_i)·x.
- Ràng buộc: (1) mỗi tàu đúng một phương án; (2) t ≥ a_i; (3) t + h_ik ≤ H;
  (4) mỗi ô (u',t') tối đa một tàu, cận max(0, u'−s_i+1)..u' và max(0, t'−h_ik+1)..t'; (5) Σ k·x ≤ Q mỗi giờ;
  (6) x nhị phân, k ∈ K_i, u ≤ M − s_i. (2),(3),(6) áp khi sinh phương án; chỉ (1),(4),(5) đưa vào solver.
- Ví dụ chuẩn trong tài liệu: M=10, H=24, Δ=50, L=500, Q=6, ρ=30; tàu A: a=2, l=250 (s=5), W=360,
  K={2,3,4} → h=6,4,3; x_{A,2,4,3}=1 nghĩa là unit 2–6, giờ 4–7, C_A=8; tàu A có 336 phương án hợp lệ.

## Code: `bacap_pnc/`, môi trường ảo `bacap_pnc/.venv` (chạy trên dữ liệu thật PNC, Busan New Port)
| File | Việc |
|---|---|
| `prepare_data.py` | `data/pnc_schedule_raw.csv` → `data/vessels_clean.csv` (thêm LOA, W, vị trí bến) |
| `bacap_milp.py` | Mô hình, giải bằng HiGHS qua `scipy.optimize.milp` (không cần solver riêng) |
| `plot_schedule.py` | Vẽ lịch kiểu "Vessel Schedule (Graph)" của PNC + biểu đồ số cẩu |
| `run.py` | Chạy một case chỉ với tàu PNC: `python run.py --start 2026-11-25 --days 4` |
| `random_case.py` | Bốc ngẫu nhiên N tàu (khối CẤU HÌNH đầu file: N_VESSELS, SEED, DATE_FROM, DATE_TO, TERMINALS, SAVE_RESULTS) |
| `interactive_chart.py` | Biểu đồ tương tác Plotly, tự mở trong trình duyệt mỗi lần chạy |
| `save_results.py` | Lưu Excel + PNG + HTML vào output/ khi SAVE_RESULTS = True (mặc định False, không lưu gì) |
| `check_solution.py` | Kiểm tra độc lập: không chồng lấn, không vượt Q, không cập trước ETB |

Dữ liệu PNC (lấy 25/11/2026 từ svc.pncport.com, Vessel Schedule (Text)): 34 chuyến 24/11–04/12/2026,
cột ETB, ETD, bến B4–B8, Dis/Load/Shift. Thông số: cầu cảng 2.000 m, 5 bến (giả định 400 m mỗi bến),
Q = 22 cẩu bờ (pncport.com), sâu 17 m, ρ = 25 lượt/giờ (giả định; năng suất bến trung vị theo kế hoạch PNC là 78 lượt/giờ).

Dữ liệu BCT (info.bct2-4.com, 25/11/2026): 18 chuyến 23/11–30/11. Kho gộp `data/vessels_clean.csv` có cột
`terminal` = PNC/BCT, 49 chuyến đủ dữ liệu. **Luôn ghi đúng nguồn terminal; không ghi tàu BCT là của PNC.**
Trong `random_case.py`, mọi tàu được xếp trên cầu cảng PNC như kịch bản giả định; giờ đến giữ nguyên ETB thật.

Giả định/điều chỉnh khi chạy dữ liệu thật:
- a_i = ETB của PNC (lịch không có giờ tàu đến neo).
- LOA: 4 tàu tra trên mạng (Gerda 367, Gustav 366, Gunvor 367, Ane 351 m); còn lại ước lượng theo tuyến
  (cột `loa_source = est`) → nên thay bằng LOA thật (VesselFinder).
- K_i = 2..min(6, LOA/60). Tàu W = 0 bị loại; Dis âm đặt 0.
- Tàu đang nằm bến lúc t0 được cố định vị trí, giờ rời và số cẩu (ước lượng).
- Mặc định Δ = 100 m, bước thời gian 2 giờ, chờ tối đa 24 giờ (Δ=50, bước 1 giờ quá nặng: hết 120 s chưa ra lời giải tốt).

Kết quả case 25/11, 4 ngày: 13 tàu + 5 tàu đang nằm bến, ~10.000 biến, tối ưu trong ~27 s, Z = 288 giờ
(kế hoạch PNC: 417 giờ). Không kết luận "tốt hơn PNC": mô hình bỏ qua lashing, di chuyển cẩu, safety distance.

## Việc tiếp theo có thể làm
- Thay LOA ước lượng bằng LOA thật; hiệu chỉnh ρ.
- Chạy thêm case, phân tích độ nhạy theo Q, ρ, Δ, bước thời gian.
- Mở rộng Level 2 (safety distance / non-crossing) hoặc time-variant (Level 3).

## Tiến độ
- Nhật ký: `docs/progress.md`. Mỗi lần làm xong một việc trong dự án thì thêm mục mới ở đầu (ngày, đã làm gì, kết quả).
