---
title: "BACAP – From the Real-World Problem to a Time-Invariant MILP Model"
author: "Bách"
date: "25/11/2026"
lang: vi-VN
---

**Cách đọc tài liệu này.** Tài liệu đi từ bài toán thật ở cảng đến mô hình toán. Mục 1 và 2 mô tả bài toán đầy đủ cùng các khó khăn thực tế. Mục 3 và 4 tóm tắt các nghiên cứu đã có và xếp các khó khăn thành từng cấp độ. Mục 5 giải thích vì sao nghiên cứu này chọn cấp độ đơn giản nhất và mỗi giả định bỏ qua điều gì. Mục 6 đến 8 trình bày mô hình MILP. Mục 9 nêu hạn chế và hướng mở rộng.

# 1. Problem Overview

## What happens at the quay?

Hãy hình dung một cầu cảng container dài 500 m, dọc theo cầu cảng có 6 cẩu bờ (quay crane, QC) chạy trên cùng một đường ray. Trong ngày có nhiều tàu đến, mỗi tàu có chiều dài và lượng hàng khác nhau. Khi một tàu đến, người lập kế hoạch phải trả lời ba câu hỏi:

1. **Tàu đỗ ở đâu** trên cầu cảng?
2. **Tàu bắt đầu làm hàng lúc nào?**
3. **Tàu được bao nhiêu cẩu?**

BACAP (Berth Allocation and Quay Crane Assignment Problem) là bài toán trả lời đồng thời cả ba câu hỏi đó cho mọi tàu, sao cho tổng thời gian các tàu ở cảng là nhỏ nhất. Trong tài liệu nghiên cứu, hai câu hỏi đầu thuộc bài toán phân bổ cầu cảng (BAP), câu hỏi thứ ba thuộc bài toán phân bổ cẩu (QCAP). Việc quyết định cụ thể cẩu nào làm hầm hàng nào, theo thứ tự nào là một bài toán riêng gọi là lập lịch cẩu (QCSP).

## Why must the three decisions be made together?

Số cẩu quyết định thời gian làm hàng, và thời gian làm hàng quyết định tàu chiếm bến bao lâu. Ví dụ tàu A cần xếp dỡ $W_A = 360$ lượt, mỗi cẩu làm $\rho = 30$ lượt/giờ:

| Số cẩu $k$ | Năng suất tổng | Thời gian làm hàng $h_{A,k}$ |
|:---:|:---:|:---:|
| 2 | $2 \times 30 = 60$ lượt/giờ | $360 / 60 = 6$ giờ |
| 3 | $3 \times 30 = 90$ lượt/giờ | $360 / 90 = 4$ giờ |
| 4 | $4 \times 30 = 120$ lượt/giờ | $360 / 120 = 3$ giờ |

Cho tàu A thêm cẩu thì A rời bến sớm hơn, nhường chỗ cho tàu sau. Nhưng cẩu là nguồn lực chung: cẩu đưa cho A thì tàu khác đang làm cùng lúc sẽ thiếu. Nếu quyết định vị trí đỗ trước rồi mới chia cẩu, ta có thể xếp được chỗ nhưng không đủ cẩu để làm kịp. Vì vậy ba quyết định phải được giải cùng lúc.

# 2. Real-World Challenges

Mô hình nào cũng phải đơn giản hóa thực tế. Nhưng trước khi đơn giản hóa, cần thấy bài toán thật khó ở những đâu. Phần này liệt kê các khó khăn theo năm nhóm. Mỗi khó khăn đi kèm một ví dụ ở cảng và giải thích nó làm mô hình phức tạp hơn ở chỗ nào.

## 2.1 Vessel-related challenges

| Khó khăn | Ví dụ ở cảng | Mô hình phải thêm gì |
|:---|:---|:---|
| Chiều dài tàu khác nhau | Tàu feeder dài khoảng 150 m, tàu mẹ dài hơn 400 m | Mỗi tàu chiếm một đoạn cầu cảng khác nhau |
| Mớn nước (draft) khác nhau | Tàu mớn nước 15 m không cập được đoạn cầu cảng chỉ sâu 12 m | Ràng buộc độ sâu theo từng vị trí |
| Khối lượng hàng khác nhau | Tàu A cần 2.000 lượt, tàu B cần 8.000 lượt | Thời gian làm hàng phụ thuộc lượng hàng và số cẩu |
| Yêu cầu vị trí cập | Hãng tàu muốn cập gần khu bãi chứa hàng của mình | Tập vị trí cho phép riêng cho từng tàu, hoặc phạt khi lệch vị trí mong muốn |
| Số cẩu tối đa theo chiều dài tàu | Tàu dài 200 m không thể làm cùng lúc với 8 cẩu | Giới hạn số cẩu cho từng tàu |

## 2.2 Berth-related challenges

| Khó khăn | Ví dụ ở cảng | Mô hình phải thêm gì |
|:---|:---|:---|
| Cầu cảng có hạn | Cầu cảng 500 m, tổng chiều dài các tàu muốn cập cùng lúc là 600 m | Ràng buộc không chồng lấn về không gian |
| Khoảng cách an toàn giữa hai tàu | Hai tàu không được neo sát nhau để còn khoảng trống khi cập và rời bến | Thêm khoảng hở vào ràng buộc không gian |
| Cầu cảng rời rạc hay liên tục | Thực tế tàu có thể đỗ ở bất kỳ điểm nào, không chỉ ở các vạch cố định | Rời rạc dùng chỉ số vị trí; liên tục dùng biến vị trí liên tục và nhiều ràng buộc thứ tự hơn |
| Cầu cảng không đồng nhất | Mỗi đoạn có độ sâu, thiết bị khác nhau | Năng suất và khả năng cập phụ thuộc vị trí |
| Đoạn cầu cảng tạm đóng | Một đoạn đang bảo trì từ giờ 10 đến giờ 16 | Khả năng sử dụng từng vị trí thay đổi theo thời gian |

## 2.3 Quay crane challenges

Đây là nhóm giáo sư nhấn mạnh, và cũng là nhóm khác biệt nhiều nhất giữa mô hình đơn giản và thực tế.

| Khó khăn | Ví dụ ở cảng | Mô hình phải thêm gì |
|:---|:---|:---|
| Tổng số cẩu có hạn | Cảng có 6 cẩu nhưng các tàu cùng lúc cần 8 cẩu | Tổng cẩu dùng cùng lúc không vượt số cẩu hiện có |
| **Khoảng cách an toàn (safety distance)** | Hai cẩu cạnh nhau phải cách nhau tối thiểu một khoảng để không va chạm | Phải biết **vị trí** từng cẩu, không chỉ đếm số lượng |
| **Không vượt qua nhau (non-crossing)** | QC1 đứng bên trái QC2 thì luôn ở bên trái QC2, vì chung một ray | Phải giữ **thứ tự** các cẩu trên ray |
| Thời gian di chuyển cẩu | Cẩu làm xong tàu A phải chạy sang tàu B, mất thời gian | Thời điểm cẩu sẵn sàng phụ thuộc quãng đường di chuyển |
| Năng suất cẩu khác nhau | Cẩu mới làm 30 lượt/giờ, cẩu cũ làm 25 lượt/giờ | Cần biết cẩu nào làm tàu nào, không coi mọi cẩu như nhau |
| Cẩu cản trở nhau | Nhiều cẩu cùng làm một tàu thì năng suất mỗi cẩu giảm | Năng suất không còn tăng tuyến tính theo số cẩu |
| Số cẩu thay đổi theo thời gian | Tàu A có 4 cẩu buổi sáng, buổi chiều chuyển 2 cẩu sang tàu B | Số cẩu của mỗi tàu là quyết định theo từng giờ (time-variant) |

**Vì sao đếm cẩu chưa đủ?** Lấy ví dụ cảng có $Q = 6$ cẩu. Tàu A đỗ ở unit 2–6 dùng 3 cẩu, tàu B đỗ ở unit 7–9 dùng 3 cẩu, cùng làm hàng một lúc. Nếu chỉ đếm số lượng thì $3 + 3 = 6 \le 6$, phương án hợp lệ. Nhưng cẩu cuối cùng của A và cẩu đầu tiên của B có thể phải đứng rất sát nhau ở chỗ hai tàu giáp nhau. Nếu khoảng cách đó nhỏ hơn khoảng an toàn, phương án này không thực hiện được trên thực tế, dù về mặt "số lượng" là đủ.

![Ví dụ minh họa: đếm đủ số cẩu chưa có nghĩa là xếp được cẩu trên ray. Phía trên, QC3 và QC4 cách nhau 25 m, nhỏ hơn khoảng an toàn giả định d = 40 m. Phía dưới, các cẩu giữ đúng thứ tự và đủ khoảng cách.](qc_safety.png){width=100%}

Nói ngắn gọn: **ràng buộc về tổng số cẩu đảm bảo không dùng quá số cẩu, nhưng không đảm bảo các cẩu đó đứng được an toàn trên ray.** Muốn đảm bảo điều sau, mô hình phải gán từng cẩu cụ thể với vị trí của nó, và khi đó bài toán lớn hơn rất nhiều. Theo các nghiên cứu về lập lịch cẩu có ràng buộc non-crossing và safety clearance, do bài toán này khó nên phần lớn tác giả dùng heuristic để giải (Abou Kasm & Diabat, 2019).

## 2.4 Time and uncertainty challenges

| Khó khăn | Ví dụ ở cảng | Mô hình phải thêm gì |
|:---|:---|:---|
| Tàu đến không đúng giờ | Dự kiến đến lúc 8 giờ, thực tế đến lúc 10 giờ vì thời tiết | Giờ đến là đại lượng bất định |
| Thời gian làm hàng không chắc chắn | Dự kiến 10 giờ, thực tế 13 giờ vì hàng nhiều hơn khai báo | Thời gian làm hàng bất định |
| Thủy triều | Tàu mớn nước lớn chỉ vào được khi nước lên | Cửa sổ thời gian được phép cập và rời |
| Hạn rời cảng | Tàu phải rời trước 18 giờ để kịp lịch tuyến | Ràng buộc hạn hoặc chi phí trễ hạn |
| Ca làm việc, bảo trì | Cẩu dừng khi đổi ca hoặc bảo trì định kỳ | Năng lực cẩu thay đổi theo giờ |
| Sự cố và thời tiết | Gió mạnh làm dừng cẩu; một cẩu hỏng giữa chừng | Năng suất và số cẩu khả dụng không cố định |
| Tàu đến bất ngờ | Có tàu mới đến khi kế hoạch đang chạy | Phải lập lại kế hoạch (rescheduling) |

Rodrigues và Agra (2022) xếp riêng nhóm này thành một hướng nghiên cứu lớn, vì chất lượng kế hoạch cập bến bị ảnh hưởng mạnh bởi các sự kiện không lường trước. Hai nguồn bất định được quan tâm nhiều nhất là giờ tàu đến và thời gian làm hàng.

## 2.5 Objective-related challenges

Cảng không chỉ có một mục tiêu, và các mục tiêu có thể kéo về hai phía khác nhau:

| Mục tiêu | Ý nghĩa |
|:---|:---|
| Giảm thời gian chờ | Tàu đến rồi phải chờ bao lâu mới được cập |
| Giảm thời gian ở cảng (turnaround) | Từ lúc tàu đến đến lúc làm xong |
| Giảm trễ hạn rời cảng | Tàu rời muộn so với lịch |
| Tăng mức sử dụng cẩu | Hạn chế cẩu đứng không |
| Giảm chi phí vận hành | Thêm cẩu thì nhanh hơn nhưng tốn nhân công và năng lượng hơn |
| Giảm độ lệch vị trí cập | Tàu phải đỗ xa vị trí mong muốn, kéo dài quãng đường xe chở hàng ra bãi |

**Ví dụ xung đột.** Cảng có 5 cẩu, tàu A đến trước cần 2 cẩu, tàu B đến sau cần 5 cẩu. Ưu tiên A thì B phải chờ. Ưu tiên B thì A phải chờ, dù A đến trước. Không có phương án nào tốt nhất cho cả hai mục tiêu cùng lúc, nên người lập mô hình phải chọn một mục tiêu, hoặc gộp nhiều mục tiêu bằng trọng số.

# 3. Related Literature

Bảng dưới tóm tắt các nghiên cứu tiêu biểu, xếp theo khó khăn mà mỗi nghiên cứu tập trung giải quyết.

| Nghiên cứu | Nội dung chính | Khó khăn liên quan |
|:---|:---|:---|
| Bierwirth & Meisel (2010) | Survey nền tảng, đề xuất cách phân loại các bài toán BAP, QCAP, QCSP và các cách tích hợp | Khung phân loại chung |
| Bierwirth & Meisel (2015) | Survey tiếp theo, phân loại hơn 120 nghiên cứu mới sau 2009 | Xu hướng nghiên cứu |
| Türkoğulları và cộng sự (2014) | Phân bổ cầu cảng kết hợp phân bổ cẩu **time-invariant** | Gần nhất với mô hình của nghiên cứu này |
| Türkoğulları và cộng sự (2016) | Phân bổ cẩu **time-variant**, có chi phí thiết lập cẩu (setup) | Số cẩu thay đổi theo thời gian |
| Agra & Oliveira (2018) | MIP cho bài toán tích hợp BACAP và lập lịch cẩu, cẩu không đồng nhất, rời rạc hóa không gian và thời gian | Cẩu khác nhau; cách rời rạc hóa |
| Li, Sheu & Gao (2015) | Cầu cảng liên tục, gán cẩu cụ thể có xét phạm vi hoạt động của từng cẩu | Vị trí cẩu cụ thể |
| Abou Kasm & Diabat (2019) | Lập lịch cẩu cho một tàu có ràng buộc non-crossing và safety clearance, giải chính xác | Safety distance, non-crossing |
| Xiang & Liu (2021) | Mô hình almost robust cho BACAP khi giờ đến và lượng hàng bất định | Bất định |
| Rodrigues & Agra (2022) | Survey các nghiên cứu BACAP có xét bất định | Bất định |
| Nghiên cứu về thủy triều (2018), Discrete Dynamics in Nature and Society | Cầu cảng liên tục, cẩu time-variant, có ảnh hưởng của thủy triều ở luồng vào cảng | Thủy triều |

Các nghiên cứu trên không cùng giải một phiên bản bài toán. Có bài chỉ xét lập lịch cẩu cho một tàu, có bài xét cả ba bài toán BAP, QCAP và QCSP. Vì vậy khi trích dẫn cần nói rõ phạm vi của từng bài.

# 4. Levels of Problem Complexity

Từ các khó khăn ở mục 2, có thể xếp BACAP thành năm cấp độ, mỗi cấp thêm một nhóm khó khăn vào cấp trước. Đây là cách phân cấp đề xuất để xác định phạm vi nghiên cứu, không phải một phân loại chuẩn trong tài liệu, và các cấp có thể kết hợp với nhau (ví dụ Level 2 kèm thủy triều của Level 4).

| Cấp độ | Thêm khó khăn gì | Mô hình thay đổi thế nào |
|:---|:---|:---|
| **Level 1: Basic deterministic BACAP** (nghiên cứu này) | Cầu cảng và thời gian rời rạc, lịch tàu biết trước, số cẩu cố định, năng suất tuyến tính, chỉ giới hạn tổng số cẩu | Một biến nhị phân cho mỗi phương án (vị trí, giờ bắt đầu, số cẩu) |
| **Level 2: Spatial and crane safety** | Khoảng cách an toàn giữa tàu, safety distance và non-crossing của cẩu, giới hạn số cẩu theo chiều dài tàu, cầu cảng không đồng nhất | Thêm vị trí và thứ tự của từng cẩu |
| **Level 3: Detailed crane operations** | Số cẩu thay đổi theo thời gian, thời gian di chuyển và setup của cẩu, năng suất cẩu khác nhau, lập lịch theo hầm hàng | Số cẩu thành quyết định theo từng giờ; gán cẩu cụ thể |
| **Level 4: Time-dependent physical conditions** | Thủy triều, mớn nước, thời tiết, đoạn cầu cảng tạm đóng | Cửa sổ thời gian cập và rời; năng lực thay đổi theo giờ |
| **Level 5: Uncertainty** | Giờ đến, lượng hàng, năng suất bất định; cẩu hỏng | Mô hình robust, stochastic, hoặc lập lại kế hoạch |

# 5. Research Scope and Assumptions

## Why start at Level 1?

Nghiên cứu này chọn Level 1, vì ba lý do:

1. **Có mô hình gốc để kiểm chứng.** Đây là lần đầu xây dựng mô hình BACAP. Mô hình đơn giản cho phép kiểm tra từng ràng buộc bằng tay trên ví dụ nhỏ trước khi thêm độ phức tạp.
2. **Các cấp cao hơn xây trên Level 1.** Ba quyết định cốt lõi (vị trí, giờ bắt đầu, số cẩu) và hai ràng buộc cạnh tranh (chỗ trên cầu cảng, số cẩu) ở Level 1 vẫn giữ nguyên ở các cấp sau. Mỗi cấp chỉ thêm ràng buộc hoặc thay một giả định.
3. **Có nghiên cứu tương đương để so sánh.** Bài toán phân bổ cầu cảng kết hợp phân bổ cẩu time-invariant đã được nghiên cứu (Türkoğulları và cộng sự, 2014), nên có cơ sở đối chiếu kết quả.

## Decisions, Inputs and Outputs

| | Nội dung |
|:---|:---|
| Quyết định | Vị trí đỗ (unit đầu tiên tàu chiếm), giờ bắt đầu làm hàng, số cẩu $k$ (cố định trong suốt thời gian làm hàng) |
| Đầu vào | Chiều dài cầu cảng $L$, tổng số cẩu $Q$, năng suất một cẩu $\rho$; mỗi tàu có giờ đến, chiều dài, lượng hàng, các mức số cẩu cho phép, trọng số ưu tiên |
| Đầu ra | Mỗi tàu: vị trí đỗ, giờ bắt đầu, số cẩu, giờ làm xong; tổng thời gian các tàu ở cảng |

## Assumptions and what each one leaves out

Mỗi giả định dưới đây là một lựa chọn có chủ ý: nó bỏ qua một khó khăn cụ thể ở mục 2, và có thể được nới ra ở một cấp độ cao hơn.

| Mã | Giả định | Bỏ qua khó khăn nào | Nới ra ở |
|:---|:---|:---|:---|
| A1 | Lịch tàu đến và lượng hàng biết trước, không có yếu tố ngẫu nhiên | Tàu trễ, lượng hàng thay đổi, tàu đến bất ngờ (2.4) | Level 5 |
| A2 | Số cẩu mỗi tàu cố định từ lúc bắt đầu đến lúc xong (time-invariant) | Chuyển cẩu giữa các tàu trong lúc làm hàng (2.3) | Level 3 |
| A3 | Cẩu giống nhau, tổng $Q$ cẩu; chỉ đếm số lượng, không xét cẩu nào làm tàu nào | **Safety distance, non-crossing**, thời gian di chuyển cẩu, năng suất cẩu khác nhau (2.3) | Level 2, 3 |
| A4 | Năng suất tăng tuyến tính theo số cẩu | Cẩu cản trở nhau khi cùng làm một tàu (2.3) | Level 3 |
| A5 | Cầu cảng dài $L$ chia thành $M$ unit, mỗi unit dài $\Delta = 50$ m; tàu dài $l$ chiếm $\lceil l/\Delta \rceil$ unit liền nhau | Cầu cảng liên tục, khoảng cách an toàn giữa tàu, cầu cảng không đồng nhất (2.2) | Level 2 |
| A6 | Thời gian rời rạc theo bước 1 giờ trong khoảng lập kế hoạch $H$; thời gian làm hàng làm tròn lên | Thời gian liên tục, độ chính xác dưới một giờ | Chia bước nhỏ hơn |
| A7 | Tàu không cập trước giờ đến, được làm hàng liên tục một lần, và phải xong trong $H$ | Tạm dừng giữa chừng, hạn rời cảng riêng của từng tàu (2.4) | Level 3, 4 |
| A8 | Bỏ qua thời gian vào và rời bến, thủy triều, mớn nước, thời tiết | Điều kiện vật lý thay đổi theo thời gian (2.1, 2.4) | Level 4 |

Làm tròn lên ở A5 và A6 có nghĩa là mô hình luôn dành dư một chút chỗ và thời gian. Lời giải vì vậy luôn làm được, chỉ có thể lãng phí một phần cầu cảng.

## Running example

Toàn bộ các mục sau dùng chung một ví dụ:

| Tham số | Giá trị |
|:---|:---|
| Cầu cảng | $L = 500$ m, $\Delta = 50$ m, nên $M = 10$ unit, đánh số $0, 1, \dots, 9$ |
| Khoảng lập kế hoạch | $H = 24$ giờ, các ô giờ $t = 0, 1, \dots, 23$ |
| Cẩu | $Q = 6$ cẩu, mỗi cẩu $\rho = 30$ lượt/giờ |
| Tàu A | Đến lúc $a_A = 2$, dài $l_A = 250$ m, hàng $W_A = 360$ lượt, $K_A = \{2, 3, 4\}$, $w_A = 1$ |
| Tàu B | Dài $l_B = 150$ m nên $s_B = 3$ unit, làm hàng $h_B = 4$ giờ (dùng trong ví dụ ràng buộc (4), (5)) |

# 6. Notation

## Sets and Indices

| Ký hiệu | Ý nghĩa | Ví dụ |
|:---|:---|:---|
| $i \in V = \{1, \dots, N\}$ | Tàu | Tàu A, tàu B |
| $t \in T = \{0, \dots, H-1\}$ | Ô giờ, mỗi ô dài 1 giờ; ô $t$ là khoảng $[t, t+1)$ | $t = 0, \dots, 23$ |
| $u \in U = \{0, \dots, M-1\}$ | Unit cầu cảng, $M = L / \Delta$; đánh số từ 0 như ô giờ | $u = 0, \dots, 9$ |
| $k \in K_i = \{k_i^{\min}, \dots, k_i^{\max}\}$ | Các mức số cẩu được phép cho tàu $i$ | $K_A = \{2, 3, 4\}$ |

## Input Parameters

| Ký hiệu | Ý nghĩa | Đơn vị | Tàu A |
|:---|:---|:---|:---|
| $a_i$ | Giờ tàu $i$ đến, đã quy về ô giờ | giờ | $a_A = 2$ |
| $l_i$ | Chiều dài tàu $i$ | m | $l_A = 250$ |
| $W_i$ | Lượng hàng cần xếp dỡ của tàu $i$ | lượt | $W_A = 360$ |
| $w_i$ | Trọng số ưu tiên của tàu $i$ (mặc định 1) | — | $w_A = 1$ |
| $\rho$ | Năng suất một cẩu | lượt/giờ | $30$ |
| $Q$ | Tổng số cẩu của cảng | cẩu | $6$ |
| $L$, $\Delta$ | Chiều dài cầu cảng; chiều dài một unit | m | $500$; $50$ |

Giờ đến được ký hiệu $a_i$ (arrival) thay vì $t_i$, vì $t$ đã dùng cho giờ bắt đầu làm hàng, là thứ mô hình phải quyết định. Giờ đến là dữ liệu cho trước, giờ bắt đầu là lựa chọn của mô hình, và $t - a_i$ chính là thời gian tàu phải chờ.

## Derived Parameters

Hai tham số được tính sẵn từ dữ liệu đầu vào:

$$s_i = \left\lceil \frac{l_i}{\Delta} \right\rceil, \qquad h_{ik} = \left\lceil \frac{W_i}{k\,\rho} \right\rceil$$

- $s_i$ là số unit tàu $i$ chiếm. Với tàu A: $s_A = \lceil 250 / 50 \rceil = 5$ unit.
- $h_{ik}$ là số giờ làm hàng của tàu $i$ khi dùng $k$ cẩu. Với tàu A: $h_{A,2} = 6$, $h_{A,3} = 4$, $h_{A,4} = 3$ giờ (bảng ở mục 1).

**Dễ nhầm:** $h_{ik}$ là số giờ một tàu làm hàng, còn $H$ là độ dài toàn bộ khoảng lập kế hoạch. Ví dụ $h_{A,3} = 4$ giờ, còn $H = 24$ giờ.

## Decision Variables

**Mô hình chọn phương án từ một danh sách.** Thay vì để mô hình tự tính ra vị trí, giờ và số cẩu như ba con số riêng, mỗi tàu được liệt kê sẵn mọi phương án có thể (vị trí $u$, giờ bắt đầu $t$, số cẩu $k$). Mỗi phương án có một biến nhị phân:

$$x_{iutk} \in \{0,1\}$$

$x_{iutk} = 1$ nghĩa là tàu $i$ chọn phương án đó: đỗ từ unit $u$ (chiếm các unit $u, u+1, \dots, u+s_i-1$), bắt đầu làm hàng ở ô giờ $t$, và dùng $k$ cẩu trong suốt $h_{ik}$ giờ. Ngược lại $x_{iutk} = 0$.

**Đọc một biến thành lời.** $x_{A,2,4,3} = 1$ đọc là "tàu A, đỗ từ unit 2, bắt đầu giờ 4, dùng 3 cẩu":

| Chỉ số | Giá trị | Ý nghĩa |
|:---|:---|:---|
| $i$ | A | Tàu A |
| $u$ | 2 | Chiếm unit 2, 3, 4, 5, 6 (vì $s_A = 5$) |
| $t$ | 4 | Làm hàng các ô giờ 4, 5, 6, 7 (vì $h_{A,3} = 4$) |
| $k$ | 3 | Dùng 3 cẩu, xong lúc $C_A = t + h_{A,3} = 4 + 4 = 8$ |

Tàu chờ $t - a_A = 4 - 2 = 2$ giờ, rồi làm hàng 4 giờ, nên ở cảng tổng cộng $C_A - a_A = 8 - 2 = 6$ giờ.

**Chỉ tạo biến cho phương án hợp lệ.** Một phương án chỉ được đưa vào danh sách khi thỏa cả ba điều kiện:

- $u \le M - s_i$: tàu không nhô ra khỏi cầu cảng;
- $t \ge a_i$: không cập trước giờ đến;
- $t + h_{ik} \le H$: làm xong trong khoảng lập kế hoạch.

Ba điều kiện này chính là các ràng buộc (6), (2), (3) ở mục 8.

# 7. Objective Function

$$\min \; Z = \sum_{i \in V} w_i \sum_{u}\sum_{t}\sum_{k \in K_i} \bigl( t + h_{ik} - a_i \bigr)\, x_{iutk}$$

Biểu thức $(t + h_{ik} - a_i)$ là thời gian tàu ở cảng: chờ $(t - a_i)$ cộng làm hàng $h_{ik}$. Câu hỏi thường gặp là: **đã có biến $x$ rồi, sao vẫn cần ba dấu tổng theo $u$, $t$, $k$?**

**Bước 1. Mỗi phương án có một chi phí riêng.** Xét ba phương án của tàu A ($a_A = 2$):

| Phương án | $u$ | $t$ | $k$ | $h_{A,k}$ | Chi phí $t + h_{A,k} - a_A$ |
|:---|:---:|:---:|:---:|:---:|:---|
| $x_{A,2,4,3}$ | 2 | 4 | 3 | 4 | $4 + 4 - 2 = 6$ giờ |
| $x_{A,0,2,4}$ | 0 | 2 | 4 | 3 | $2 + 3 - 2 = 3$ giờ |
| $x_{A,5,9,2}$ | 5 | 9 | 2 | 6 | $9 + 6 - 2 = 13$ giờ |

**Bước 2. Biến $x$ là công tắc bật hoặc tắt.** $u$, $t$, $k$ chỉ là nhãn của phương án, không phải con số mô hình tự điền vào. Vì vậy không thể viết thẳng $t + h_{ik} - a_i$ cho tàu A. Thay vào đó, ba dấu tổng duyệt qua toàn bộ danh sách phương án và nhân chi phí của mỗi phương án với $x$ của nó. Nếu mô hình chọn $x_{A,2,4,3} = 1$:

$$6 \cdot 1 + 3 \cdot 0 + 13 \cdot 0 + \dots = 6$$

Phương án được chọn giữ nguyên chi phí, các phương án khác nhân 0 nên biến mất. Kết quả đúng bằng thời gian tàu A ở cảng.

**Bước 3. Dấu tổng ngoài cùng cộng các tàu.** $\sum_i$ cộng thời gian ở cảng của mọi tàu, mỗi tàu nhân trọng số $w_i$. Ví dụ tàu A ở cảng 6 giờ và tàu B ở cảng 5 giờ, cả hai có $w = 1$, thì $Z = 6 + 5 = 11$. Tàu quan trọng hơn có $w_i$ lớn hơn, nên mỗi giờ nó phải chờ bị tính nặng hơn.

**Hàm mục tiêu "đấu" với ràng buộc ra sao?** Nếu chỉ có tàu A, mô hình sẽ chọn phương án 3 giờ ($t = 2$, 4 cẩu). Nhưng khi tàu B cũng cần cẩu hoặc cần chỗ cùng lúc, các ràng buộc (4) và (5) có thể cấm phương án đó. Mô hình khi ấy phải chọn phương án đắt hơn cho tàu này để tàu kia không chờ quá lâu, sao cho tổng $Z$ nhỏ nhất.

**Điểm cần nhớ:** ba dấu tổng $\sum_u \sum_t \sum_k$ duyệt qua mọi phương án của một tàu; biến $x$ quyết định phương án nào thực sự được tính; $\sum_i$ cộng tất cả các tàu lại.

# 8. Constraints

Có sáu ràng buộc, chia thành hai nhóm. Nhóm **riêng từng tàu** (1), (2), (3), (6) chỉ yêu cầu mỗi tàu chọn một phương án hợp lệ. Nhóm **giữa các tàu** (4), (5) làm các tàu phụ thuộc lẫn nhau, vì chúng tranh nhau chỗ trên cầu cảng và tranh nhau cẩu. Đây là phần cốt lõi của bài toán.

| Mã | Ràng buộc | Nhóm | Ý nghĩa ngắn |
|:---|:---|:---|:---|
| (1) | Mỗi tàu một phương án | Riêng từng tàu | Chọn đúng một bộ (vị trí, giờ bắt đầu, số cẩu) |
| (2) | Không cập trước giờ đến | Riêng từng tàu | Loại phương án bắt đầu khi tàu chưa đến |
| (3) | Làm xong trong khoảng lập kế hoạch | Riêng từng tàu | Loại phương án xong sau giờ $H$ |
| (4) | Không chồng lấn không gian–thời gian | Giữa các tàu | Mỗi ô (unit, giờ) có tối đa một tàu |
| (5) | Giới hạn tổng số cẩu | Giữa các tàu | Tổng cẩu dùng cùng lúc $\le Q$ |
| (6) | Miền biến | Riêng từng tàu | $x$ là 0 hoặc 1; $k$ thuộc $K_i$; tàu nằm gọn trên cầu cảng |

## (1) Each Vessel Is Served Exactly Once

$$\sum_{u}\sum_{t}\sum_{k \in K_i} x_{iutk} = 1 \qquad \forall i \in V$$

**Ràng buộc này chống điều gì?** Tổng các biến của một tàu bằng 1 nghĩa là tàu chọn đúng một phương án. Tổng bằng 0 là tàu không được phục vụ; tổng bằng 2 là tàu đỗ ở hai nơi cùng lúc. Nếu bỏ ràng buộc này, mô hình có thể đặt mọi $x = 0$ để có $Z = 0$, tức không phục vụ tàu nào mà vẫn "tối ưu".

**Ví dụ.** Sau khi lọc bằng (2), (3), (6), tàu A còn $6 \times 56 = 336$ phương án hợp lệ (6 vị trí, 56 cặp giờ bắt đầu và số cẩu; cách đếm ở ràng buộc (3)). Ràng buộc (1) bắt đúng một trong 336 biến bằng 1, ví dụ $x_{A,2,4,3} = 1$, còn 335 biến bằng 0.

## (2) No Berthing Before Arrival Time

$$x_{iutk} = 0 \qquad \text{nếu } t < a_i$$

**Ý nghĩa.** Tàu chưa đến thì chưa thể bắt đầu làm hàng. Mọi phương án có giờ bắt đầu sớm hơn giờ đến bị ép bằng 0, tức bị gạch khỏi danh sách. Ràng buộc (2) là bước lọc; ràng buộc (1) chọn một phương án trong số còn lại.

**Ví dụ.** $a_A = 2$, nên tàu A chỉ có thể bắt đầu ở $t = 2, 3, 4, \dots$

| Giờ bắt đầu | Kết quả | Lý do |
|:---|:---|:---|
| $t = 1$ | Bị loại | Tàu A chưa đến |
| $t = 2$ | Hợp lệ | Vào bến ngay, chờ 0 giờ |
| $t = 5$ | Hợp lệ | Chờ $5 - 2 = 3$ giờ |

Các phương án có $t = 0$ hoặc $t = 1$ bị loại: $2$ giờ $\times$ $3$ mức số cẩu $\times$ $6$ vị trí $= 36$ phương án.

## (3) Service Completes Within the Planning Horizon

$$x_{iutk} = 0 \qquad \text{nếu } t + h_{ik} > H$$

**Ý nghĩa.** Mô hình chỉ nhìn thấy $H$ giờ, nên phương án nào làm xong sau giờ $H$ bị loại. Giờ bắt đầu muộn nhất là $t = H - h_{ik}$.

**Ví dụ.** Với $H = 24$, kết hợp với (2) là $t \ge 2$:

| Số cẩu $k$ | $h_{A,k}$ | Điều kiện | Giờ bắt đầu hợp lệ | Số lựa chọn |
|:---:|:---:|:---|:---|:---:|
| 2 | 6 | $t + 6 \le 24$ nên $t \le 18$ | $t = 2, \dots, 18$ | 17 |
| 3 | 4 | $t + 4 \le 24$ nên $t \le 20$ | $t = 2, \dots, 20$ | 19 |
| 4 | 3 | $t + 3 \le 24$ nên $t \le 21$ | $t = 2, \dots, 21$ | 20 |

Tổng $17 + 19 + 20 = 56$ cặp (giờ bắt đầu, số cẩu). Kiểm tra: $k = 2$, $t = 18$ thì $18 + 6 = 24 \le 24$, hợp lệ; $t = 19$ thì $19 + 6 = 25 > 24$, bị loại. Lưu ý "2 đến 18" là các giờ **bắt đầu** có thể chọn, không phải khoảng thời gian làm hàng.

## (4) No Space–Time Overlap Between Vessels

$$\sum_{i \in V}\sum_{k \in K_i}\;\sum_{u=\max(0,\,u'-s_i+1)}^{u'}\;\sum_{t=\max(0,\,t'-h_{ik}+1)}^{t'} x_{iutk} \le 1 \qquad \forall u' \in U,\; t' \in T$$

**Ràng buộc này chống điều gì?** Hai tàu có thể làm hàng cùng lúc nếu đỗ ở hai đoạn khác nhau, nhưng không thể cùng chiếm một đoạn cầu cảng trong cùng một giờ. Hãy hình dung một tấm lưới: trục ngang là các unit, trục dọc là các giờ. Mỗi tàu là một hình chữ nhật trên lưới, rộng $s_i$ unit, cao $h_{ik}$ giờ. Các hình chữ nhật không được đè lên nhau.

![Ràng buộc (4) trên lưới unit × giờ. Bên trái, A và B cùng phủ ô (5, 6) nên vi phạm. Bên phải, B dời sang unit 7–9 nên không ô nào có hai tàu.](grid.png){width=100%}

**Không cần đọc cả công thức một lúc.** Ràng buộc chỉ làm một việc: **chọn một ô cố định, rồi đếm xem có bao nhiêu phương án được chọn đang phủ ô đó.** Ô đang kiểm tra ký hiệu là $(u', t')$. Dấu phẩy trên dùng để phân biệt với $(u, t)$ là nơi một tàu bắt đầu; $(u', t')$ không thuộc về tàu nào.

| Dấu tổng | Đang làm gì |
|:---|:---|
| $\sum_{i}$ | Xét lần lượt từng tàu |
| $\sum_{k}$ | Xét các mức số cẩu của tàu đó (vì $h_{ik}$ phụ thuộc $k$) |
| $\sum_{u}$ | Xét các vị trí bắt đầu khiến tàu phủ tới unit $u'$ |
| $\sum_{t}$ | Xét các giờ bắt đầu khiến tàu phủ tới giờ $t'$ |

**Cận dưới đến từ đâu?** Lấy ô $(u', t') = (5, 6)$ và tàu A ($s_A = 5$, $h_{A,3} = 4$).

- *Theo không gian:* A phủ unit 5 khi nó bắt đầu ở $u = 1$ (chiếm 1–5), $u = 2$ (2–6), $u = 3$, $u = 4$, hoặc $u = 5$ (5–9). Bắt đầu ở $u = 0$ chỉ chiếm 0–4, không tới unit 5. Vậy $u$ chạy từ $1 = 5 - 5 + 1 = u' - s_A + 1$ đến $5 = u'$.
- *Theo thời gian:* A làm hàng ở giờ 6 khi nó bắt đầu ở $t = 3$ (làm 3–6), $4$, $5$, hoặc $6$. Vậy $t$ chạy từ $3 = 6 - 4 + 1 = t' - h_{A,3} + 1$ đến $6 = t'$.

Liệt kê bằng tay và công thức cho cùng một kết quả.

**Vì sao có $\max(0, \dots)$?** Ở ô gần mép lưới, cận dưới có thể ra số âm. Ví dụ ô $(2, 1)$: $u' - s_A + 1 = 2 - 5 + 1 = -2$ và $t' - h_{A,3} + 1 = 1 - 4 + 1 = -2$. Không có unit hay giờ âm, nên lấy $\max(0, -2) = 0$.

**Ví dụ một ô vi phạm.** A chọn $x_{A,2,4,3} = 1$: phủ unit 2–6, giờ 4–7. B ($s_B = 3$, $h_B = 4$) bắt đầu ở unit 5, giờ 6: phủ unit 5–7, giờ 6–9. Ô $(5, 6)$ bị cả hai phủ, tổng $= 1 + 1 = 2 > 1$, vi phạm. B có hai lối ra:

- **Đổi chỗ:** sang unit 7–9, vẫn bắt đầu giờ 6. Ô $(5, 6)$ chỉ còn A, tổng $= 1$, hợp lệ.
- **Đổi giờ:** giữ unit 5 nhưng chờ đến giờ 8, khi A đã xong.

**Hai tàu nối tiếp nhau có tính là chồng lấn không?** Không. A làm các ô giờ 4–7 và xong lúc $C_A = 8$, B bắt đầu ở ô giờ 8. Viết thành hai khoảng thì A chiếm $[4, 8)$, B chiếm $[8, 12)$, không giao nhau. Nếu B bắt đầu ở giờ 7 thì cả hai cùng chiếm ô giờ 7, vi phạm.

## (5) Total Cranes in Use Cannot Exceed $Q$

$$\sum_{i \in V}\sum_{k \in K_i}\sum_{u}\;\sum_{t=\max(0,\,t'-h_{ik}+1)}^{t'} k\, x_{iutk} \le Q \qquad \forall t' \in T$$

**Ràng buộc này chống điều gì?** Ràng buộc (4) chỉ lo các tàu không đè nhau trên cầu cảng. Nhưng hai tàu ở hai đoạn khác nhau vẫn dùng chung một đội cẩu. Ràng buộc (5) đảm bảo tại mỗi giờ, tổng số cẩu đang làm việc không vượt $Q$.

**Đọc theo từng bước:**

1. Chọn một giờ $t'$ để kiểm tra (giống $(u', t')$ ở ràng buộc (4), $t'$ không thuộc tàu nào).
2. Tìm các tàu đang làm hàng ở giờ $t'$: tàu bắt đầu ở $t$ thì làm hàng các giờ $t, \dots, t + h_{ik} - 1$, nên cần $t' - h_{ik} + 1 \le t \le t'$. Đây là cùng logic với cận thời gian ở (4).
3. Nhân $k$ với $x_{iutk}$: phương án được chọn đóng góp đúng $k$ cẩu, phương án không chọn đóng góp 0.
4. Cộng lại và so với $Q$.

$\sum_u$ không có cận vì theo giả định A3, cẩu chỉ được đếm số lượng, không gắn với vị trí: tàu đỗ ở unit nào cũng lấy cẩu từ cùng một đội.

**Ví dụ.** $Q = 6$, A chọn $x_{A,2,4,3} = 1$ (3 cẩu, giờ 4–7):

| Giờ $t'$ | Tàu đang làm hàng | Tổng cẩu | Kết quả |
|:---|:---|:---:|:---|
| 3 | Chưa có (A bắt đầu giờ 4) | 0 | Hợp lệ |
| 6, B bắt đầu giờ 6 với 3 cẩu | A (3) + B (3) | 6 | Hợp lệ, $6 \le 6$ |
| 6, B bắt đầu giờ 6 với 4 cẩu | A (3) + B (4) | 7 | Vi phạm, $7 > 6$ |
| 8, B bắt đầu giờ 8 với 4 cẩu | Chỉ B (A đã xong) | 4 | Hợp lệ |

Khi bị cấm, B có hai lối ra: dùng ít cẩu hơn (làm lâu hơn), hoặc chờ A làm xong. Đây chính là chỗ "cẩu cho tàu này thì tàu kia thiếu".

**Giới hạn của ràng buộc này.** (4) và (5) độc lập với nhau: B đỗ ở unit 7–9 không chạm A nên (4) cho phép, nhưng (5) vẫn cấm nếu tổng cẩu vượt $Q$. Ngược lại, (5) cho phép $3 + 3 = 6$ cẩu nhưng không kiểm tra các cẩu đó có đứng cách nhau đủ xa hay không. Đây là khoảng trống về safety distance đã nêu ở mục 2.3.

## (6) Variable Domain and Crane Range

$$x_{iutk} \in \{0,1\}, \qquad k \in K_i, \qquad u \le M - s_i$$

**Miền biến là danh sách các giá trị mà biến được phép nhận.** Giống công tắc đèn chỉ có bật (1) hoặc tắt (0), không có "bật một nửa". Ràng buộc (6) gồm ba phần:

| Phần | Nói gì | Tàu A |
|:---|:---|:---|
| $x_{iutk} \in \{0,1\}$ | Chọn hoặc không chọn, không có $x = 0.5$ (nửa tàu đỗ một nơi) | $x_{A,2,4,3} = 1$ hoặc $0$ |
| $k \in K_i$ | Số cẩu thuộc các mức cho phép của tàu | $k \in \{2, 3, 4\}$ |
| $u \le M - s_i$ | Unit cuối $u + s_i - 1$ không vượt quá $M - 1$ | $u \le 10 - 5 = 5$, tức $u = 0, \dots, 5$ |

**Ca đúng và ca sai.**

- $x_{A,5,9,3}$: $u = 5 \le 5$, chiếm unit 5–9, sát mép cầu cảng nhưng hợp lệ; $k = 3 \in K_A$. Xong lúc $C_A = 9 + 4 = 13$.
- $x_{A,2,4,5}$: bị loại vì $5 \notin K_A$.
- $x_{A,6,4,3}$: bị loại vì $u = 6 > 5$; tàu sẽ chiếm unit 6–10 mà unit 10 không tồn tại.

**Dễ nhầm:** $Q = 6$ là tổng số cẩu của cả cảng, còn $K_A = \{2, 3, 4\}$ là các mức cẩu cho riêng tàu A. Cảng có 6 cẩu không có nghĩa tàu A được dùng bất kỳ số cẩu nào từ 1 đến 6.

**Khi lập trình.** (2), (3) và (6) được áp ngay lúc tạo danh sách phương án hợp lệ của mỗi tàu, nên không cần khai báo thành ràng buộc riêng. Chỉ (1), (4), (5) là ràng buộc thật sự cần đưa vào bộ giải.

**Quy mô mô hình.** Số biến khoảng $N \times M \times H \times |K|$. Ví dụ 15 tàu, 20 unit, 72 giờ, 4 mức số cẩu cho khoảng $15 \times 20 \times 72 \times 4 = 86.400$ biến nhị phân. Chia unit nhỏ hơn ($\Delta$ nhỏ) hoặc bước thời gian ngắn hơn đều làm mô hình nặng lên nhanh.

# 9. Limitations and Extensions

Mỗi hạn chế của mô hình ứng với một giả định ở mục 5 và một cấp độ ở mục 4. Nới một giả định nghĩa là thay một phần cụ thể của mô hình:

| Mở rộng | Nới giả định | Thay đổi trong mô hình |
|:---|:---|:---|
| Safety distance và non-crossing | A3 | Gán từng cẩu cụ thể cho tàu, thêm biến vị trí cẩu và ràng buộc khoảng cách tối thiểu giữa hai cẩu cạnh nhau |
| Khoảng cách an toàn giữa tàu | A5 | Mỗi tàu chiếm thêm một khoảng hở ở hai đầu trong ràng buộc (4) |
| Số cẩu thay đổi theo thời gian | A2 | Số cẩu của tàu trở thành biến theo từng giờ; thời gian làm hàng không còn là hằng số $h_{ik}$ |
| Năng suất phi tuyến | A4 | $h_{ik}$ tính theo năng suất giảm dần khi thêm cẩu |
| Thủy triều và mớn nước | A8 | Thêm cửa sổ thời gian được phép cập, rời cho từng tàu và từng vị trí |
| Bất định | A1 | Thay $a_i$, $W_i$ bằng tập kịch bản hoặc khoảng giá trị (robust, stochastic) |
| Bài toán lớn | — | Column Generation hoặc heuristic thay cho giải trực tiếp |

# References

- Abou Kasm, O., & Diabat, A. (2019). The quay crane scheduling problem with non-crossing and safety clearance constraints: An exact solution approach.
- Agra, A., & Oliveira, M. (2018). MIP approaches for the integrated berth allocation and quay crane assignment and scheduling problem. *European Journal of Operational Research*, 264(1), 138–148.
- Bierwirth, C., & Meisel, F. (2010). A survey of berth allocation and quay crane scheduling problems in container terminals. *European Journal of Operational Research*, 202(3), 615–627.
- Bierwirth, C., & Meisel, F. (2015). A follow-up survey of berth allocation and quay crane scheduling problems in container terminals. *European Journal of Operational Research*, 244(3), 675–689.
- Li, F., Sheu, J.-B., & Gao, Z.-Y. (2015). Solving the continuous berth allocation and specific quay crane assignment problems with quay crane coverage range. *Transportation Science*, 49(4), 968–989.
- Rodrigues, F., & Agra, A. (2022). Berth allocation and quay crane assignment/scheduling problem under uncertainty: A survey. *European Journal of Operational Research*, 303(2), 501–524.
- Türkoğulları, Y. B., Taşkın, Z. C., Aras, N., & Altınel, İ. K. (2014). Optimal berth allocation and time-invariant quay crane assignment in container terminals. *European Journal of Operational Research*, 235(1), 88–101.
- Türkoğulları, Y. B., Taşkın, Z. C., Aras, N., & Altınel, İ. K. (2016). Optimal berth allocation, time-variant quay crane assignment and scheduling with crane setups in container terminals. *European Journal of Operational Research*, 254(3), 985–1001.
- Xiang, X., & Liu, C. (2021). An almost robust optimization model for integrated berth allocation and quay crane assignment problem. *Omega*, 104, 102455.
- Integrated berth allocation and time-variant quay crane scheduling with tidal impact in approach channel. (2018). *Discrete Dynamics in Nature and Society*.
