# Hanoi Delivery Search — So sánh BFS, GBFS và A* trên bản đồ Hà Nội

Tìm đường ngắn nhất từ **kho** đến **danh sách khách hàng** trên bản đồ thật của Hà Nội (OpenStreetMap), áp dụng **BFS**, **Greedy Best-First Search (GBFS)** và **A\***, dùng **UCS/Dijkstra** làm đáp án chuẩn. So sánh **số nút mở rộng** và **đường đi tìm được** trên ba đồ thị: mức quận (A), mạng đường chi tiết (B1) và mạng trục chính (B2).

> Đây là bản đặc tả gốc dùng để code, giữ nguyên số mục. Những chỗ phần cài đặt khác đặc tả được liệt kê ngay dưới đây; khi hai bên mâu thuẫn, mục này và `config/` là đúng.

## Sai khác giữa cài đặt và đặc tả

| # | Đặc tả | Cài đặt | Lý do |
|---|---|---|---|
| 1 | `heuristic: euclid_utm` | `heuristic: haversine` (R = 6 371 009 m) | Chứng minh ở mục 2.2 không đúng; xem ghi chú tại mục đó. Cả hai hàm vẫn có trong `heuristics.py`. |
| 2 | `gadm_file: gadm41_VNM_2.json` | `gadm41_VNM.gpkg`, lớp `ADM_ADM_2` | Bản JSON bị đơn giản hóa nên ranh giới hai quận kề nhau không trùng khít: chỉ tìm được 14 cặp kề (thiếu cả Cầu Giấy–Ba Đình). Bản gpkg cho 26 cặp. |
| 3 | `latlon: null` (geocode tự động) | `latlon` điền tay từ đối tượng OSM cùng tên | DNS của mạng lúc code không phân giải được `nominatim.openstreetmap.org`. Mục 8.1 của đặc tả cho phép điền tay. |
| 4 | Điểm đại diện quận = UBND, không được thì polygon | Thêm `representative_source` trong `districts.yaml`, đang đặt `polygon` | Lý do như dòng 3, và từ 01/07/2025 không còn UBND quận. Chế độ `polygon` cho kết quả không phụ thuộc mạng. |
| 5 | `x, y` của nút A = điểm đại diện | `x, y, lat, lon` của nút A lấy từ nút B2 sau khi snap | Để h và trọng số đo giữa cùng hai điểm, bảo đảm weight ≥ h. |
| 6 | `force_edges: []` | `force_edges: [[NTL, BTL]]` | `inside_ratio` = 0,896, sát ngưỡng 0,90; không có cạnh này Bắc Từ Liêm bị cô lập. Đúng cơ chế ở mục 3.3. |
| 7 | `g_new < g[v]` mới tính `reopened` | `g_new < g[v] - 1e-9` | Sai số cộng dồn số thực không phải là mở lại nút. |
| 8 | `SearchGraph` id kiểu `int` | Mức B là `int`, mức A là chuỗi mã quận | Mã quận (`HM`, `TH`) là id tự nhiên khi chạy tay. |
| 9 | `run(..., heuristic_name, ...)` | `heuristic_name` nhận cả hàm `(sg, target) -> h` | Mức A cần tra bảng h. |
| 10 | Không ghi đè file cùng tên | Đã có snapshot bất kỳ của đồ thị thì bỏ qua, trừ khi `--force` | Giữ `data/raw/` bất biến khi chạy lại vào ngày khác. |
| 11 | Chọn cặp chạy tay từ `runs_A.csv` | So sánh đường trực tiếp trong notebook 02 | `runs_A.csv` không có cột đường đi. Cả hai ứng viên đều cho GBFS trùng A\*, nên notebook dùng cặp có gap(GBFS) lớn nhất: TX → CG. |
| 12 | Nền bản đồ không quy định | Esri World Light Gray | CARTO trả ảnh "API KEY REQUIRED"; tile OSM không phân giải được trên mạng lúc code. Vẫn ghi "© OpenStreetMap contributors". |
| 13 | — | Thêm `A_points.csv`, `analyze.b1_vs_b2`, `data/external/` trong `.gitignore` | Cần cho hình đồ thị A, so sánh ghép cặp B1–B2 và điều khoản GADM (mục 16). |

---

## Mục lục

1. [Bài toán và câu hỏi nghiên cứu](#1-bài-toán-và-câu-hỏi-nghiên-cứu)
2. [Khái niệm và ký hiệu](#2-khái-niệm-và-ký-hiệu)
3. [Ba đồ thị: A, B1, B2](#3-ba-đồ-thị-a-b1-b2)
4. [Kho, khách hàng và các ca thử](#4-kho-khách-hàng-và-các-ca-thử)
5. [Thước đo và quy ước đếm](#5-thước-đo-và-quy-ước-đếm)
6. [Pipeline tổng quan](#6-pipeline-tổng-quan)
7. [Cấu trúc thư mục](#7-cấu-trúc-thư-mục)
8. [Đặc tả chi tiết từng file](#8-đặc-tả-chi-tiết-từng-file)
9. [Kiểm thử](#9-kiểm-thử)
10. [Kết quả đầu ra và câu hỏi mà mỗi kết quả trả lời](#10-kết-quả-đầu-ra-và-câu-hỏi-mà-mỗi-kết-quả-trả-lời)
11. [Quy ước chung](#11-quy-ước-chung)
12. [Hạn chế](#12-hạn-chế)
13. [Những điểm đã chỉnh so với bản brainstorm](#13-những-điểm-đã-chỉnh-so-với-bản-brainstorm)
14. [Lộ trình code đề xuất](#14-lộ-trình-code-đề-xuất)
15. [Cài đặt và chạy](#15-cài-đặt-và-chạy)
16. [Giấy phép dữ liệu](#16-giấy-phép-dữ-liệu)

---

## 1. Bài toán và câu hỏi nghiên cứu

### 1.1. Bài toán

- **Đầu vào:** bản đồ đường bộ Hà Nội (OSM), một kho, một danh sách khách hàng (địa danh hoặc tọa độ).
- **Đầu ra:** với mỗi cặp (kho, khách) và mỗi thuật toán: đường đi, tổng quãng đường (mét), số cạnh, số nút mở rộng, kích thước hàng đợi lớn nhất, thời gian chạy.
- **Thuật toán:**

| Thuật toán | Hàm ưu tiên | Vai trò |
|---|---|---|
| BFS | hàng đợi FIFO (coi mọi cạnh có chi phí bằng nhau) | Đối chứng "không dùng chi phí" |
| GBFS | f(n) = h(n) | Nhanh, không bảo đảm tối ưu |
| A\* | f(n) = g(n) + h(n) | Tối ưu nếu h hợp lệ |
| UCS (Dijkstra) | f(n) = g(n) | **Đáp án chuẩn** để kiểm chứng A\* |

- **Hai mức bài toán:**
  - **Cơ bản (bắt buộc):** kho → từng khách, mỗi cặp chạy độc lập.
  - **Nâng cao (tùy chọn):** một xe xuất phát từ kho, đi qua nhiều khách rồi quay về kho. Thứ tự khách chọn bằng Nearest-Neighbor, mỗi chặng tìm đường bằng A\*.

### 1.2. Câu hỏi nghiên cứu

- **RQ1.** A\* có luôn cho đường ngắn nhất (bằng UCS) không? A\* tiết kiệm bao nhiêu nút mở rộng so với UCS và BFS?
- **RQ2.** GBFS nhanh hơn bao nhiêu và mất tối ưu bao nhiêu? Mức mất tối ưu có liên hệ với **tỉ lệ vòng** (đường bộ / chim bay) không?
- **RQ3.** Khi chi phí các cạnh không bằng nhau, đường của BFS dài hơn đường tối ưu bao nhiêu?
- **RQ4.** Khoảng cách kho–khách và độ chi tiết của bản đồ (B1 so với B2) ảnh hưởng thế nào đến số nút mở rộng?

### 1.3. Phạm vi và giả định

- Vùng nghiên cứu: **12 quận nội thành cũ** (Ba Đình, Hoàn Kiếm, Tây Hồ, Long Biên, Cầu Giấy, Đống Đa, Hai Bà Trưng, Hoàng Mai, Thanh Xuân, Hà Đông, Nam Từ Liêm, Bắc Từ Liêm) cộng vùng đệm 3 km.
  - Từ 01/07/2025 Hà Nội không còn cấp quận (còn 126 xã, phường). Project chỉ dùng ranh giới 12 quận cũ như **một vùng địa lý quen thuộc**, không mang ý nghĩa hành chính.
- Phương tiện: **ô tô con / xe van** trên B1, **xe tải nhẹ / ô tô chỉ đi trục chính** trên B2. Không mô phỏng xe máy (xem mục 12).
- Chi phí = **quãng đường (mét)**. Không xét thời gian, tắc đường, đèn tín hiệu.
- Dữ liệu OSM là ảnh chụp tại ngày tải (ghi trong `results/run_metadata.json`).

---

## 2. Khái niệm và ký hiệu

| Ký hiệu | Ý nghĩa |
|---|---|
| c(u, v) | Chi phí cạnh u → v = thuộc tính `length` (mét). Đo dọc theo hình dạng thật của con đường: tổng các đoạn great-circle nối các điểm vẽ trên OSM. |
| g(n) | Tổng chi phí các cạnh từ kho đến n trên đường đang xét |
| h(n) | Heuristic: khoảng cách Euclid (mét) từ n đến đích, tính trên tọa độ UTM 48N |
| h\*(n) | Chi phí thật **còn lại** ngắn nhất từ n đến đích |
| f(n) | Giá trị ưu tiên trong hàng đợi |
| d_road(s, t) | Quãng đường bộ ngắn nhất (theo UCS) |
| d_euclid(s, t) | Đường chim bay (Euclid UTM) |
| detour(s, t) | **Tỉ lệ vòng** = d_road / d_euclid, luôn ≥ 1 |
| gap | Mức mất tối ưu = (path_m / optimal_m − 1) × 100% |

### 2.1. Điều kiện để A\* tối ưu

- **Admissible:** h(n) ≤ h\*(n) với mọi n. (So với chi phí **còn lại** đến đích, không phải so với g(n).)
- **Consistent:** h(u) ≤ c(u, v) + h(v) với mọi cạnh (u, v). Consistent kéo theo admissible, và A\* không cần mở lại nút đã đóng.

### 2.2. Vì sao Euclid trên UTM thỏa cả hai điều kiện

1. `length` của một cạnh là tổng các đoạn great-circle dọc con đường, nên ≥ khoảng cách great-circle giữa hai đầu cạnh.
2. Hà Nội (~105,8°E) nằm cách kinh tuyến trục của UTM 48N (105°E) khoảng 85 km. Hệ số tỉ lệ ở đó ≈ 0,9997 < 1, nên khoảng cách Euclid trên UTM hơi **nhỏ hơn** khoảng cách thật.
3. Từ (1) và (2): Euclid_UTM(u, v) ≤ c(u, v). Kết hợp bất đẳng thức tam giác trên mặt phẳng: h(u) ≤ Euclid(u, v) + h(v) ≤ c(u, v) + h(v), tức là **consistent**.

> **Đính chính sau khi đo trên dữ liệu thật: lập luận trên sai ở bước (1)–(2), `euclid_utm` không consistent.**
> `length` của OSMnx tính trên **mặt cầu** R = 6 371 009 m, còn UTM chiếu từ **ellipsoid WGS84**. Ở vĩ độ 21°, bán kính cong theo hướng đông–tây của ellipsoid là ≈ 6 380 880 m, lớn hơn bán kính cầu khoảng 0,155%. Bù trừ với hệ số tỉ lệ 0,9997, trên cạnh đông–tây Euclid_UTM lớn hơn `length` khoảng 0,125%.
>
> Kết quả đo: Euclid_UTM(u, v) > c(u, v) trên 27 402 / 138 445 cạnh của B1 (19,8%) và 1 256 / 7 027 cạnh của B2 (17,9%), tỉ lệ lớn nhất 1,00128. A\* với `euclid_utm` có `reopened` > 0 ở 1 trong 60 cặp thử trên B1, vi phạm yêu cầu `reopened = 0`; trong các cặp đó chưa thấy đường nào dài hơn UCS.
>
> **Cách xử lý:** dùng `haversine` với đúng bán kính của OSMnx. `length` là tổng các đoạn great-circle trên cùng mặt cầu, nên haversine(u, v) ≤ c(u, v), cộng với bất đẳng thức tam giác trên mặt cầu cho h consistent. Đo lại: 0 cạnh vi phạm. `d_euclid` và `detour` vẫn tính bằng Euclid UTM như định nghĩa ở trên. Chiều dài và số nút mở rộng khác rất ít so với `euclid_utm` (tổng số nút mở rộng lệch khoảng 0,3–0,6% trên các cặp thử).

Điều này được kiểm chứng bằng số trong `tests/test_heuristic.py` trên mọi cạnh của đồ thị thật.

### 2.3. Nút mở rộng

Một nút được tính là **mở rộng** khi nó được **rút ra khỏi hàng đợi** và đưa vào tập Closed để xét hàng xóm. Không đếm lúc đưa vào hàng đợi. Chi tiết ở mục 5.

---

## 3. Ba đồ thị: A, B1, B2

Cả B1 và B2 đều thuộc **mức B** (đồ thị đường phố thật). Mức A là đồ thị quận, dựng **từ B2**.

| Đồ thị | Mức | Nút | Cạnh / trọng số | Nguồn | Dùng để |
|---|---|---|---|---|---|
| **A** | Quận | 12 điểm đại diện quận cũ | Quận kề nhau có đường nối trực tiếp; trọng số = quãng đường trên B2 giữa hai điểm đại diện | GADM + B2 | Chạy tay từng bước, giải thích thuật toán |
| **B1** | Đường phố chi tiết | Mọi giao lộ của mạng `drive` | `length` (m) | OSMnx | So sánh trên mạng dày đặc |
| **B2** | Đường phố trục chính | Giao lộ trên đường chính | `length` (m) | OSMnx + bộ lọc | So sánh trên mạng thưa |

### 3.1. B1 — mạng chi tiết

- `network_type="drive"`: mạng cho ô tô. Không gồm `highway=service` (muốn gồm thì dùng `drive_service`), không gồm đường cấm xe cơ giới (ví dụ cầu Long Biên).
- Mục đích: ô tô con / xe van giao hàng trong phố.

### 3.2. B2 — mạng trục chính

- Bộ lọc (một dòng, không xuống dòng):
  ```
  ["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link"]["area"!~"yes"]["access"!~"private"]["motor_vehicle"!~"no"]["motorcar"!~"no"]
  ```
- **Bắt buộc có các nhánh `*_link`**: thiếu chúng thì nút giao khác mức bị đứt và LSCC co lại rất mạnh.
- **Bắt buộc có `motorway`**: nếu Vành đai 3 trên cao được gắn tag `motorway` mà bị lọc mất thì ca C4 không còn ý nghĩa.
- Các điều kiện `access`, `motor_vehicle`, `motorcar` thay cho phần loại trừ mà preset `drive` tự làm (khi dùng `custom_filter`, preset không được áp dụng).
- Nếu sau LSCC còn **dưới 85% số nút**, bật `include_tertiary: true` (thêm `tertiary|tertiary_link`) và ghi lại quyết định này.
- Mục đích: xe tải nhẹ / ô tô chỉ đi trục chính.

### 3.3. A — đồ thị quận

- **Nút:** 12 quận cũ. Điểm đại diện = trụ sở UBND quận cũ (geocode). Nếu không geocode được thì dùng `representative_point()` của polygon quận. Sau đó snap vào nút gần nhất của B2.
- **Cạnh:** tạo cạnh giữa hai quận khi đồng thời:
  1. Hai polygon có **ranh giới chung dài > 50 m** (chạm nhau tại một điểm thì không tính).
  2. Đường ngắn nhất trên B2 giữa hai điểm đại diện **nằm phần lớn (≥ 90% chiều dài) trong hai quận đó**. Điều kiện này loại các cặp kề nhau qua sông nhưng không có cầu ô tô nối thẳng (đường đi phải vòng qua quận thứ ba).
  3. Có thể ép thêm hoặc cấm cạnh bằng `force_edges` / `forbid_edges` trong `config/districts.yaml`, sau khi xem bản đồ kiểm tra.
- **Trọng số:** w(A, B) = trung bình của d(A→B) và d(B→A) trên B2, **làm tròn lên** bội số 100 m. Lưu cả giá trị mét chính xác.
- **Heuristic trên A:** Euclid giữa hai điểm đại diện, **làm tròn xuống** bội số 100 m.
- Làm tròn lên cho trọng số và làm tròn xuống cho h giữ nguyên tính admissible và consistent, đồng thời cho số đẹp để chạy tay (đơn vị km, một chữ số thập phân).
- Đồ thị A là **vô hướng** (`nx.Graph`).

---

## 4. Kho, khách hàng và các ca thử

### 4.1. Kho

| ID | Vị trí | Vai trò |
|---|---|---|
| **K1** | Khu Bến xe Nước Ngầm, chỗ Ngọc Hồi giao Vành đai 3 | Kho chính, ven đô phía nam, xe tải vào được |
| **K2** | Khu Đức Giang, Long Biên | Kho phụ, chỉ dùng cho ca bẫy GBFS (C3) |

### 4.2. Các ca thử có tên

Mỗi ca là một **điểm** (lat/lon). Điểm được snap **riêng vào từng đồ thị** B1 và B2, để so sánh B1 với B2 trên cùng vị trí thực.

| Ca | Kho → Đích | Tính chất muốn làm nổi bật | Tiêu chí kiểm tra | Nếu không đạt |
|---|---|---|---|---|
| **C1** | K1 → Bến xe Giáp Bát (~2 km) | Ca dễ (đối chứng) | detour ≤ 1,2 | Chọn tự động nút gần địa danh nhất có detour ≤ 1,2 |
| **C2** | K1 → Quảng trường Ba Đình (~8 km) | Heuristic tốt giảm mạnh số nút mở rộng | detour ≤ 1,2 và d_euclid ≥ 6 km | Như C1 |
| **C3** | K2 → Quảng An, Tây Hồ | GBFS không tối ưu (đường thẳng cắt qua sông, xe phải vòng qua cầu) | detour ≥ 1,4 và gap(GBFS) > 0 | Thử C3b; vẫn không đạt thì chọn tự động |
| **C3b** | K1 → Phủ Tây Hồ | Dự phòng cho C3 (vướng Hồ Tây) | Như C3 | Chọn tự động |
| **C4** | K1 → Sân vận động Mỹ Đình | BFS chỉ tối ưu khi chi phí bằng nhau | km(BFS) ≥ 1,1 × km(tối ưu) | Lấy đích ngẫu nhiên có gap(BFS) lớn nhất |
| **C5a/b/c** | K1 → Giáp Bát (~2 km) / ĐH Bách khoa (~4–5 km) / Quảng trường Ba Đình (~8 km) | Ảnh hưởng của khoảng cách | Hướng của 3 đích lệch nhau ≤ 15° | Thay đích lệch hướng bằng nút cùng hướng gần nhất |

**Chọn tự động cho ca bẫy GBFS:** lấy 20 nút có detour lớn nhất trong số các nút có d_euclid ≥ 3 km tính từ kho, chạy GBFS lần lượt, chọn nút đầu tiên có gap > 0. Đánh dấu `auto_replaced = True`.

Các khoảng cách ghi trong bảng là ước lượng chim bay. Số liệu thật lấy từ `results/tables/cases.csv`.

### 4.3. Đích ngẫu nhiên R01–R50

- Lấy **50 điểm ngẫu nhiên** (lat/lon) phân bố đều trong vùng hợp của 12 quận, `seed = 42`.
- Loại điểm cách kho dưới 1 km (chim bay) và điểm snap xa hơn 300 m (rơi vào hồ, sông).
- Lấy mẫu **một lần**, sau đó snap riêng vào B1 và B2.
- Mục đích: có thống kê trung bình và trung vị để kết luận không phụ thuộc vào việc chọn ca có lợi.

### 4.4. Mức A

- Chạy **toàn bộ 132 cặp có thứ tự** (12 × 11) với 4 thuật toán.
- Cặp để chạy tay: ứng viên Long Biên → Hà Đông và Hoàng Mai → Tây Hồ. Chọn cặp mà đường của GBFS **khác** đường của A\* (đọc từ `runs_A.csv`).

### 4.5. Kịch bản nhiều điểm dừng M1 (nâng cao)

K1 → {Giáp Bát, ĐH Bách khoa, Quảng trường Ba Đình, SVĐ Mỹ Đình, Phủ Tây Hồ} → K1.

---

## 5. Thước đo và quy ước đếm

### 5.1. Thước đo cho mỗi lần chạy

| Cột | Ý nghĩa |
|---|---|
| `expanded` | Số nút mở rộng (đếm khi rút ra, xem 5.2) |
| `generated` | Số lần đưa một mục vào hàng đợi (kể cả nút nguồn và các mục trùng) |
| `stale_skipped` | Số mục cũ bị bỏ qua khi rút ra (nút đã có trong Closed) |
| `reopened` | Số lần A\* phải mở lại nút đã đóng. **Phải bằng 0** vì h consistent |
| `max_frontier` | Kích thước lớn nhất của cấu trúc hàng đợi (kể cả mục cũ) |
| `hops` | Số cạnh trên đường tìm được |
| `path_m` | Tổng `length` trên đường tìm được |
| `optimal_m` | Quãng đường tối ưu (từ UCS) |
| `gap_pct` | (path_m / optimal_m − 1) × 100 |
| `runtime_ms` | Trung vị của 5 lần chạy (sau 1 lần chạy khởi động) |

**Chỉ số chính là `expanded`, `path_m` và `gap_pct`.** `runtime_ms` phụ thuộc máy và Python nên chỉ tham khảo.

### 5.2. Quy ước đếm (áp dụng giống nhau cho cả 4 thuật toán)

1. **Đếm khi rút ra:** `expanded += 1` khi một nút được rút khỏi hàng đợi **và chưa nằm trong Closed**.
2. **Bỏ qua mục cũ:** với hàng đợi ưu tiên kiểu lazy, một nút có thể nằm trong heap nhiều lần. Rút ra một nút đã có trong Closed thì bỏ qua, **không đếm**, tăng `stale_skipped`.
3. **Kiểm tra đích khi rút ra** (không kiểm tra lúc sinh nút), kể cả với BFS, để cách đếm thống nhất. Với A\* và UCS, đây cũng là điều kiện để bảo đảm tối ưu.
4. **Phá hòa:** mục trong heap là bộ `(priority, counter, node)`; `counter` tăng dần mỗi lần push. Các mục bằng priority được rút theo thứ tự vào trước (FIFO). BFS dùng `deque` nên vốn đã là FIFO.
5. **Thứ tự hàng xóm:** luôn duyệt hàng xóm theo **id nút tăng dần** (sắp sẵn một lần khi dựng `SearchGraph`).
6. **Cạnh song song:** chỉ giữ cạnh có `length` nhỏ nhất (làm ở bước nạp đồ thị).
7. **Đồ thị có hướng:** chỉ đi theo cạnh ra (`successors`). Không bao giờ chuyển sang vô hướng ở mức B.

### 5.3. Chính sách của từng thuật toán

- **BFS:** đánh dấu `seen` khi đưa vào hàng đợi (mỗi nút vào hàng đợi đúng một lần). Cha của nút là nút phát hiện ra nó đầu tiên.
- **GBFS (graph search):** đưa một nút vào hàng đợi **chỉ lần đầu nhìn thấy**, cha cố định từ lần đó. Không cập nhật lại vì h không phụ thuộc đường đi.
- **A\*:** đưa vào (hoặc đưa lại) khi tìm được g mới nhỏ hơn; cập nhật cha. Bỏ qua hàng xóm đã nằm trong Closed. Có bộ đếm `reopened` để kiểm chứng (phải bằng 0).
- **UCS:** giống A\* với h ≡ 0.

---

## 6. Pipeline tổng quan

```
config/*.yaml
     │
     ▼
01_download ──► data/raw/B1_<ngày>.graphml, B2_<ngày>.graphml
     │            (cần data/external/ GADM để tính bbox)
     ▼
02_preprocess ──► data/processed/B1.graphml, B2.graphml   (LSCC → chiếu UTM 48N)
     │            results/tables/dataset_stats.csv
     ▼
03_build_district_graph ──► data/processed/A.graphml       (cần B2)
     │                       results/tables/A_edges.csv, A_heuristic_matrix.csv
     ▼
04_select_cases ──► results/tables/cases.csv, detour_<dataset>_<kho>.csv
     │
     ▼
05_run_benchmark ──► results/tables/runs.csv, runs_A.csv, summary*.csv
     │                results/traces/*.json
     ▼
06_make_figures ──► results/figures/*.png, results/maps/*.html
     │
     ▼
07_multi_stop (nâng cao) ──► results/tables/multistop.csv, results/maps/M1_*.html
```

Mỗi script đọc đầu vào từ bước trước và **không sửa** `data/raw/`.

---

## 7. Cấu trúc thư mục

```
hanoi-delivery-search/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   ├── datasets.yaml            # vùng nghiên cứu, CRS, bộ lọc B1/B2
│   ├── locations.yaml           # kho, đích, ca thử, đích ngẫu nhiên, kịch bản M1
│   ├── districts.yaml           # 12 quận cũ, truy vấn UBND, ép/cấm cạnh
│   └── experiment.yaml          # seed, thuật toán, quy ước, ngưỡng kiểm tra, timing
├── data/
│   ├── raw/                     # snapshot OSM gốc, KHÔNG chỉnh sửa
│   ├── external/                # GADM cấp 2 (tải tay)
│   ├── interim/                 # geocode_cache.json
│   └── processed/               # A.graphml, B1.graphml, B2.graphml
├── src/
│   ├── __init__.py
│   ├── config.py                # đọc YAML, đường dẫn chuẩn của project
│   ├── data/
│   │   ├── __init__.py
│   │   ├── study_area.py        # 12 quận cũ, vùng hợp, bbox + đệm
│   │   ├── download.py          # tải OSM → data/raw
│   │   ├── preprocess.py        # LSCC → chiếu UTM → thống kê
│   │   ├── loaders.py           # nạp đồ thị đã xử lý → SearchGraph
│   │   ├── locations.py         # geocode (cache) → chiếu → snap
│   │   └── district_graph.py    # dựng đồ thị A từ GADM + B2
│   ├── search/
│   │   ├── __init__.py          # registry tên → hàm
│   │   ├── graph.py             # SearchGraph: danh sách kề + tọa độ
│   │   ├── result.py            # SearchResult
│   │   ├── common.py            # dựng đường, tính chi phí, frontier, trace
│   │   ├── heuristics.py        # Euclid UTM, haversine, zero, bảng tra (mức A)
│   │   ├── bfs.py
│   │   ├── gbfs.py
│   │   ├── astar.py
│   │   └── ucs.py
│   ├── routing/
│   │   ├── __init__.py
│   │   └── multi_stop.py        # Nearest-Neighbor + ghép chặng A*
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── select_cases.py      # tỉ lệ vòng, kiểm tra ca, đích ngẫu nhiên
│   │   ├── benchmark.py         # chạy thuật toán × ca × đồ thị
│   │   └── analyze.py           # tổng hợp, kiểm chứng, thống kê
│   └── viz/
│       ├── __init__.py
│       ├── expansion_maps.py    # nút mở rộng + đường đi
│       ├── detour_heatmap.py    # bản đồ tỉ lệ vòng
│       └── charts.py            # biểu đồ so sánh
├── scripts/
│   ├── 01_download.py
│   ├── 02_preprocess.py
│   ├── 03_build_district_graph.py
│   ├── 04_select_cases.py
│   ├── 05_run_benchmark.py
│   ├── 06_make_figures.py
│   └── 07_multi_stop.py
├── notebooks/
│   ├── 01_explore_data.ipynb
│   ├── 02_hand_trace_level_A.ipynb
│   └── 03_results_discussion.ipynb
├── tests/
│   ├── conftest.py              # đồ thị đồ chơi dùng chung
│   ├── test_toy_graphs.py
│   ├── test_counting.py
│   ├── test_determinism.py
│   ├── test_heuristic.py
│   └── test_optimality.py
├── results/
│   ├── tables/
│   ├── traces/
│   ├── maps/
│   ├── figures/
│   └── run_metadata.json
└── docs/
    ├── design.md
    ├── limitations.md
    └── report/
```

### Bốn nguyên tắc

1. **Tách bạch dữ liệu, thuật toán, thí nghiệm, hình vẽ.** `src/search/` không import `osmnx` và không biết gì về Hà Nội. Nó chỉ nhận `SearchGraph`, nút nguồn, nút đích và hàm h. Nhờ vậy kiểm thử được trên đồ thị đồ chơi.
2. **Mọi tham số nằm trong `config/`.** Không viết cứng tọa độ, ngưỡng, seed trong code.
3. **Tái lập được.** `data/raw/` bất biến; `run_metadata.json` ghi phiên bản thư viện, ngày tải OSM, bbox, bộ lọc, seed.
4. **Một bảng kết quả gốc.** Mọi bảng tổng hợp và hình vẽ đều sinh ra từ `runs.csv` / `runs_A.csv`.

---

## 8. Đặc tả chi tiết từng file

Mỗi mục gồm: **Nhiệm vụ**, **Đầu vào / Đầu ra**, **Hàm cần viết**, **Chi tiết**, **Xong khi**.

### 8.1. `config/`

#### `config/datasets.yaml`

```yaml
study_area:
  mode: from_districts            # from_districts | manual
  gadm_file: data/external/gadm41_VNM_2.json   # hoặc .gpkg (lớp cấp 2)
  buffer_km: 3                    # đủ để chứa đầu cầu Nhật Tân phía Đông Anh
  manual_bbox: null               # [west, south, east, north] nếu mode = manual

crs:
  geographic: "EPSG:4326"
  projected: "EPSG:32648"         # UTM 48N

osmnx:
  simplify: true
  retain_all: false
  use_cache: true

datasets:
  B1:
    label: "Mạng chi tiết – ô tô con / xe van"
    network_type: drive
    custom_filter: null
  B2:
    label: "Trục chính – xe tải nhẹ / ô tô liên quận"
    network_type: null
    custom_filter: '["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link"]["area"!~"yes"]["access"!~"private"]["motor_vehicle"!~"no"]["motorcar"!~"no"]'
    include_tertiary: false       # bật nếu LSCC giữ < 85% số nút
```

#### `config/locations.yaml`

```yaml
geocoding:
  user_agent: "hanoi-delivery-search-<tên-bạn>"   # Nominatim bắt buộc
  min_delay_seconds: 1.0                           # giới hạn ~1 yêu cầu/giây
  cache_file: data/interim/geocode_cache.json
  max_snap_dist_m: 300

depots:
  K1: {query: "Bến xe Nước Ngầm, Hà Nội", latlon: null}
  K2: {query: "Đức Giang, Long Biên, Hà Nội", latlon: null}

targets:
  T_GIAPBAT:  {query: "Bến xe Giáp Bát, Hà Nội", latlon: null}
  T_BADINH:   {query: "Quảng trường Ba Đình, Hà Nội", latlon: null}
  T_QUANGAN:  {query: "Quảng An, Tây Hồ, Hà Nội", latlon: null}
  T_PHUTAYHO: {query: "Phủ Tây Hồ, Hà Nội", latlon: null}
  T_MYDINH:   {query: "Sân vận động Mỹ Đình, Hà Nội", latlon: null}
  T_BACHKHOA: {query: "Đại học Bách khoa Hà Nội", latlon: null}

cases:
  C1:  {depot: K1, target: T_GIAPBAT,  property: easy}
  C2:  {depot: K1, target: T_BADINH,   property: good_heuristic}
  C3:  {depot: K2, target: T_QUANGAN,  property: gbfs_trap, fallback: C3b}
  C3b: {depot: K1, target: T_PHUTAYHO, property: gbfs_trap}
  C4:  {depot: K1, target: T_MYDINH,   property: bfs_hop_bias}
  C5a: {depot: K1, target: T_GIAPBAT,  property: distance_scaling}
  C5b: {depot: K1, target: T_BACHKHOA, property: distance_scaling}
  C5c: {depot: K1, target: T_BADINH,   property: distance_scaling}

random_targets:
  depot: K1
  n: 50
  seed: 42
  sample_within: districts_union
  min_euclid_from_depot_m: 1000

multi_stop:
  M1:
    depot: K1
    customers: [T_GIAPBAT, T_BACHKHOA, T_BADINH, T_MYDINH, T_PHUTAYHO]
    return_to_depot: true
    order_rules: [euclid, road]     # so sánh 2 cách chọn "khách gần nhất"
```

`latlon: null` nghĩa là geocode tự động. Nếu Nominatim không tìm ra, điền tay `[lat, lon]` copy từ Google Maps.

#### `config/districts.yaml`

```yaml
districts:
  - {id: BD,  name: "Ba Đình",     ubnd_query: "Ủy ban nhân dân quận Ba Đình, Hà Nội"}
  - {id: HK,  name: "Hoàn Kiếm",   ubnd_query: "Ủy ban nhân dân quận Hoàn Kiếm, Hà Nội"}
  - {id: TH,  name: "Tây Hồ",      ubnd_query: "Ủy ban nhân dân quận Tây Hồ, Hà Nội"}
  - {id: LB,  name: "Long Biên",   ubnd_query: "Ủy ban nhân dân quận Long Biên, Hà Nội"}
  - {id: CG,  name: "Cầu Giấy",    ubnd_query: "Ủy ban nhân dân quận Cầu Giấy, Hà Nội"}
  - {id: DD,  name: "Đống Đa",     ubnd_query: "Ủy ban nhân dân quận Đống Đa, Hà Nội"}
  - {id: HBT, name: "Hai Bà Trưng", ubnd_query: "Ủy ban nhân dân quận Hai Bà Trưng, Hà Nội"}
  - {id: HM,  name: "Hoàng Mai",   ubnd_query: "Ủy ban nhân dân quận Hoàng Mai, Hà Nội"}
  - {id: TX,  name: "Thanh Xuân",  ubnd_query: "Ủy ban nhân dân quận Thanh Xuân, Hà Nội"}
  - {id: HD,  name: "Hà Đông",     ubnd_query: "Ủy ban nhân dân quận Hà Đông, Hà Nội"}
  - {id: NTL, name: "Nam Từ Liêm", ubnd_query: "Ủy ban nhân dân quận Nam Từ Liêm, Hà Nội"}
  - {id: BTL, name: "Bắc Từ Liêm", ubnd_query: "Ủy ban nhân dân quận Bắc Từ Liêm, Hà Nội"}

edge_rules:
  min_shared_boundary_m: 50
  min_inside_ratio: 0.90
overrides:
  force_edges: []                 # ví dụ [[LB, HK]]
  forbid_edges: []
```

#### `config/experiment.yaml`

```yaml
seed: 42
datasets: [B1, B2]
algorithms: [BFS, GBFS, ASTAR, UCS]
heuristic: euclid_utm              # euclid_utm | haversine

search:
  tie_break: fifo                  # (priority, counter)
  neighbor_order: node_id_asc
  goal_test: on_pop

timing:
  warmup: 1
  repeats: 5                       # báo cáo trung vị

traces:
  save_for: named_cases            # named_cases | all | none

checks:
  easy_detour_max: 1.20
  good_detour_max: 1.20
  good_min_euclid_m: 6000
  trap_detour_min: 1.40
  trap_auto_min_euclid_m: 3000
  trap_auto_top_k: 20
  bfs_gap_min_ratio: 1.10
  bearing_tol_deg: 15
  cost_tol_m: 0.01

level_A:
  weight_round_up_m: 100
  heuristic_round_down_m: 100
  hand_trace_candidates: [[LB, HD], [HM, TH]]
```

---

### 8.2. `src/config.py`

- **Nhiệm vụ:** một chỗ duy nhất để đọc cấu hình và biết đường dẫn.
- **Hàm cần viết:**
  - `load_config(name: str) -> dict` — đọc `config/<name>.yaml`.
  - `PATHS` — hằng số đường dẫn: `ROOT`, `DATA_RAW`, `DATA_EXTERNAL`, `DATA_INTERIM`, `DATA_PROCESSED`, `TABLES`, `TRACES`, `MAPS`, `FIGURES`.
  - `ensure_dirs()` — tạo các thư mục kết quả nếu chưa có.
  - `update_run_metadata(section: str, info: dict)` — gộp thông tin vào `results/run_metadata.json` (không ghi đè phần khác).
- **Xong khi:** mọi script khác chỉ lấy đường dẫn và tham số qua module này.

---

### 8.3. `src/data/`

#### `src/data/study_area.py`

- **Nhiệm vụ:** xác định vùng nghiên cứu từ ranh giới 12 quận cũ.
- **Đầu vào:** file GADM cấp 2 trong `data/external/` (tải tay từ gadm.org, Việt Nam, cấp 2).
- **Hàm cần viết:**
  - `load_districts(cfg) -> GeoDataFrame` — lọc tỉnh Hà Nội và 12 quận theo tên. So sánh tên **sau khi bỏ dấu và viết thường**, vì cách viết trong GADM có thể khác. Trả về các cột `id, name, geometry`, CRS EPSG:4326. Báo lỗi rõ ràng nếu thiếu quận nào.
  - `districts_union(gdf) -> Polygon` — vùng hợp của 12 quận.
  - `compute_bbox(cfg) -> tuple[float, float, float, float]` — `(west, south, east, north)` = biên của vùng hợp, nới thêm `buffer_km` (đổi km sang độ: 1° vĩ ≈ 111 km, 1° kinh ≈ 111·cos(21°) ≈ 104 km). Nếu `mode = manual` thì trả `manual_bbox`.
- **Lưu ý:** nếu bản GADM còn quận "Từ Liêm" chưa tách, hãy báo lỗi và hướng dẫn: dùng bản GADM mới hơn, hoặc gộp Nam/Bắc Từ Liêm thành một nút ở mức A (ghi vào hạn chế).
- **Xong khi:** in ra bbox và vẽ thử 12 polygon trong notebook 01.

#### `src/data/download.py`

- **Nhiệm vụ:** tải B1 và B2 từ OSM.
- **Đầu vào:** `datasets.yaml`, bbox từ `study_area`.
- **Đầu ra:** `data/raw/<dataset>_<YYYYMMDD>.graphml` + thông tin tải trong `run_metadata.json`.
- **Hàm cần viết:**
  - `configure_osmnx(cfg)` — `ox.settings.use_cache`, `ox.settings.log_console`.
  - `build_filter(ds_cfg) -> str | None` — trả `custom_filter`; nếu `include_tertiary` thì chèn `tertiary|tertiary_link` vào regex.
  - `download_dataset(name, cfg, force=False) -> Path` — gọi `ox.graph_from_bbox(bbox, network_type=..., custom_filter=..., simplify=True, retain_all=False)`. **OSMnx 2.x dùng thứ tự bbox `(left, bottom, right, top)` = `(west, south, east, north)`.** Không ghi đè file đã có trừ khi `force=True`.
  - Ghi metadata: thời điểm tải, phiên bản osmnx/networkx, bbox, bộ lọc, số nút, số cạnh.
- **Lưu ý:** B1 có thể mất vài phút. OSMnx tự chia vùng lớn thành nhiều truy vấn Overpass.
- Nếu Overpass trả lỗi 5xx tạm thời (ví dụ `502 Gateway Timeout`), downloader tự thử lại tối đa
  `overpass_retries` lần với thời gian chờ tăng gấp đôi, bắt đầu từ `overpass_backoff_seconds`.
  Lỗi khác vẫn được ném ra ngay để không che khuất lỗi cấu hình hoặc truy vấn.
- **Xong khi:** hai file graphml nằm trong `data/raw/` và mở lại được bằng `ox.load_graphml`.

#### `src/data/preprocess.py`

- **Nhiệm vụ:** làm sạch và chiếu đồ thị.
- **Đầu vào:** `data/raw/<dataset>_*.graphml` (bản mới nhất).
- **Đầu ra:** `data/processed/<dataset>.graphml` + `results/tables/dataset_stats.csv`.
- **Các bước, đúng thứ tự:**
  1. `ox.truncate.largest_component(G, strongly=True)` — giữ thành phần **liên thông mạnh** lớn nhất. (OSMnx mặc định chỉ giữ thành phần liên thông yếu; API cũ `ox.utils_graph.get_largest_component` đã bị bỏ ở 2.x.)
  2. Lưu `lat`, `lon` của mỗi nút (bằng `y`, `x` trước khi chiếu) nếu chưa có.
  3. `ox.project_graph(G, to_crs="EPSG:32648")` — sau bước này `x`, `y` là mét. **Không tính lại `length`** (giữ giá trị great-circle gốc).
  4. Kiểm tra mọi nút có `lat`, `lon`; mọi cạnh có `length > 0`.
- **Hàm cần viết:**
  - `largest_scc(G) -> G`
  - `ensure_latlon(G) -> G`
  - `project(G, crs) -> G`
  - `graph_stats(G) -> dict` — số nút, số cạnh, tổng chiều dài (km), số cạnh một chiều, bậc ra trung bình, phân bố tag `highway`.
  - `preprocess_dataset(name) -> Path` — chạy cả chuỗi, ghi thống kê **trước và sau LSCC** (để thay các con số ước lượng trong bản brainstorm bằng số thật).
- **Quy tắc cho B2:** nếu tỉ lệ nút giữ lại sau LSCC < 85%, in cảnh báo đề nghị bật `include_tertiary` rồi tải lại.
- **Xong khi:** `dataset_stats.csv` có đủ hai dòng B1, B2 với số liệu trước/sau.

#### `src/data/loaders.py`

- **Nhiệm vụ:** cầu nối duy nhất giữa OSMnx/NetworkX và module `search`.
- **Hàm cần viết:**
  - `load_processed(name) -> nx.MultiDiGraph` — đọc `data/processed/<name>.graphml` (dùng cho vẽ bản đồ).
  - `to_simple_digraph(G) -> nx.DiGraph` — `ox.convert.to_digraph(G, weight="length")` (giữ cạnh song song ngắn nhất), rồi xóa self-loop.
  - `load_search_graph(name) -> SearchGraph` — `SearchGraph.from_networkx(to_simple_digraph(load_processed(name)))`. Với `A` thì nạp `nx.Graph` trực tiếp.
- **Xong khi:** `load_search_graph("B2")` trả về đối tượng có số nút bằng số nút trong `dataset_stats.csv`.

#### `src/data/locations.py`

- **Nhiệm vụ:** biến địa danh thành nút trên đồ thị.
- **Hàm cần viết:**
  - `Geocoder(cfg)` — bọc `geopy.geocoders.Nominatim(user_agent=...)` với `geopy.extra.rate_limiter.RateLimiter(min_delay_seconds=1)`; đọc/ghi cache JSON `{query: [lat, lon]}`.
  - `resolve_point(entry, geocoder) -> (lat, lon)` — ưu tiên `latlon` điền tay; nếu không có thì geocode; không ra kết quả thì báo lỗi kèm hướng dẫn điền tay.
  - `to_projected(lat, lon, crs) -> (x, y)` — `pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(lon, lat)`. **Chú ý thứ tự: `always_xy=True` nhận (lon, lat).**
  - `snap(G_proj, x, y) -> (node_id, dist_m)` — `ox.distance.nearest_nodes(G_proj, X=x, Y=y, return_dist=True)`. Đồ thị đã chiếu nên OSMnx dùng cây k-d (cần `scipy`). Cảnh báo nếu `dist_m > max_snap_dist_m`.
  - `resolve_all(cfg, dataset) -> DataFrame` — cột `point_id, query, lat, lon, x, y, node, snap_dist_m`.
- **Thứ tự bắt buộc:** đồ thị đã LSCC và đã chiếu → chiếu điểm sang cùng CRS → snap.
- **Xong khi:** mọi kho và đích có `snap_dist_m` ≤ 300 m trên cả B1 và B2.

#### `src/data/district_graph.py`

- **Nhiệm vụ:** dựng đồ thị A theo mục 3.3.
- **Đầu vào:** GADM (qua `study_area`), `districts.yaml`, `data/processed/B2.graphml`.
- **Đầu ra:** `data/processed/A.graphml`, `results/tables/A_edges.csv`, `results/tables/A_heuristic_matrix.csv`.
- **Hàm cần viết:**
  - `representative_points(gdf, geocoder) -> DataFrame` — geocode UBND; nếu thất bại thì `representative_point()`; chiếu sang UTM; snap vào B2. Cột `id, name, lat, lon, x, y, b2_node, source` (`ubnd` hoặc `polygon`).
  - `adjacent_pairs(gdf_utm, min_shared_m) -> list[(id1, id2, shared_m)]` — độ dài phần ranh giới chung = `a.boundary.intersection(b.boundary).length` trên CRS mét.
  - `inside_ratio(path_nodes, G_b2, poly_union_ab) -> float` — tỉ lệ chiều dài đường nằm trong hợp của hai quận (dùng `geometry` của cạnh nếu có, nếu không thì đoạn thẳng giữa hai nút).
  - `build_edges(...) -> DataFrame` — với mỗi cặp kề: chạy UCS trên B2 hai chiều, tính `inside_ratio`, áp `force_edges`/`forbid_edges`. Cột: `u, v, shared_boundary_m, d_uv_m, d_vu_m, inside_ratio, weight_m, accepted, reason`.
  - `build_graph(points, edges) -> nx.Graph` — nút có thuộc tính `name, x, y, lat, lon, b2_node`; cạnh có `length = weight_m` (đã làm tròn lên 100 m) và `length_exact`.
  - `heuristic_matrix(points, round_down_m) -> DataFrame` — Euclid làm tròn xuống 100 m, ma trận 12 × 12.
- **Kiểm tra trong hàm:** với mọi cạnh, `weight_m ≥ heuristic(u, v)`; đồ thị A liên thông.
- **Xong khi:** vẽ được đồ thị A đè lên bản đồ 12 quận và kiểm tra bằng mắt các cạnh qua sông (Chương Dương, Vĩnh Tuy, Thanh Trì).

---

### 8.4. `src/search/`

Module này **không import osmnx**. Chỉ dùng thư viện chuẩn (`heapq`, `collections.deque`, `math`, `time`, `dataclasses`).

#### `src/search/graph.py`

- **Nhiệm vụ:** cấu trúc đồ thị tối giản, nhanh, xác định (deterministic).
- **Lớp `SearchGraph`:**
  - Thuộc tính: `adj: dict[int, list[tuple[int, float]]]` (hàng xóm đã **sắp theo id tăng dần**), `x: dict[int, float]`, `y: dict[int, float]`, tùy chọn `lat`, `lon`, `name`.
  - `from_networkx(G, weight="length")` — nhận `nx.DiGraph` hoặc `nx.Graph`; **báo lỗi nếu là multigraph** (phải chuyển ở `loaders`). Với `nx.Graph`, `G.adj[u]` cho cả hai chiều.
  - `from_edges(nodes: dict[id, (x, y)], edges: list[(u, v, w)], directed: bool)` — dùng cho test.
  - `neighbors(u)`, `edge_cost(u, v)`, `n_nodes`, `n_edges`.
- **Xong khi:** dựng được ba đồ thị đồ chơi trong `conftest.py`.

#### `src/search/result.py`

```text
@dataclass SearchResult
  algorithm: str
  source: int
  target: int
  found: bool
  path: list[int]           # [] nếu không tìm thấy
  cost_m: float             # math.inf nếu không tìm thấy
  hops: int                 # len(path) - 1, hoặc -1
  expanded: int
  generated: int
  stale_skipped: int
  reopened: int             # chỉ có nghĩa với A*
  max_frontier: int
  runtime_ms: float | None
  expanded_order: list[int] | None    # khi trace_level >= "order"
  steps: list[dict] | None            # khi trace_level == "steps" (chỉ đồ thị nhỏ)
```

#### `src/search/common.py`

- `reconstruct_path(parent, source, target) -> list[int]`
- `path_cost(sg, path) -> float` — cộng `edge_cost` dọc đường (BFS và GBFS tính chi phí bằng hàm này).
- `class PriorityFrontier` — bọc `heapq` với bộ `(priority, counter, node)`; `push(priority, node)`, `pop() -> (priority, node)`, `__len__`. `counter` tăng dần để phá hòa FIFO.
- `class Tracer(level)` — `level ∈ {"none", "order", "steps"}`. Ghi `expanded_order`; ở mức `steps` ghi mỗi bước: `{step, popped, g, h, f, frontier: [(node, f), ...] (đã sắp), closed: [...]}`. **Báo lỗi nếu dùng `steps` trên đồ thị > 200 nút.**
- `timed_run(fn, *args, warmup, repeats) -> (result, median_ms)` — chạy khởi động, đo bằng `time.perf_counter()`, lấy trung vị. Các lần đo dùng `trace_level="none"`.

#### `src/search/heuristics.py`

- `euclid_utm(sg, target) -> Callable[[int], float]` — lấy `tx, ty` một lần, trả `lambda n: math.hypot(sg.x[n] - tx, sg.y[n] - ty)`.
- `haversine(sg, target)` — dự phòng, dùng `lat`, `lon`, bán kính Trái Đất 6 371 009 m.
- `zero(sg, target)` — luôn 0 (cho UCS).
- `from_matrix(matrix, target)` — tra bảng (đồ thị A, đã làm tròn xuống).
- `get_heuristic(name)` — chọn theo `experiment.yaml`.

#### `src/search/bfs.py`

```text
bfs(sg, s, t, trace_level="none") -> SearchResult

queue ← deque([s]); seen ← {s}; parent ← {s: None}
generated ← 1; expanded ← 0
while queue:
    u ← queue.popleft()
    expanded += 1; trace(u)
    if u == t: break                       # kiểm tra đích khi rút ra
    for v, _ in sg.neighbors(u):           # id tăng dần
        if v not in seen:
            seen.add(v); parent[v] ← u
            queue.append(v); generated += 1
    max_frontier ← max(max_frontier, len(queue))
cost ← path_cost(path)                     # chi phí thật theo mét
```

#### `src/search/gbfs.py`

```text
gbfs(sg, s, t, h, trace_level="none") -> SearchResult

open.push(h(s), s); seen ← {s}; parent ← {s: None}; closed ← ∅
while open:
    _, u ← open.pop()
    if u in closed: stale_skipped += 1; continue
    closed.add(u); expanded += 1; trace(u)
    if u == t: break
    for v, _ in sg.neighbors(u):
        if v not in seen:                  # chỉ lần đầu nhìn thấy
            seen.add(v); parent[v] ← u
            open.push(h(v), v); generated += 1
    max_frontier ← max(max_frontier, len(open))
cost ← path_cost(path)
```

#### `src/search/astar.py`

```text
astar(sg, s, t, h, trace_level="none") -> SearchResult

g ← {s: 0}; parent ← {s: None}; open.push(h(s), s); closed ← ∅
while open:
    _, u ← open.pop()
    if u in closed: stale_skipped += 1; continue
    closed.add(u); expanded += 1; trace(u)
    if u == t: break
    for v, w in sg.neighbors(u):
        g_new ← g[u] + w
        if v in closed:
            if g_new < g[v]: reopened += 1      # không được xảy ra với h consistent
            continue
        if g_new < g.get(v, ∞):
            g[v] ← g_new; parent[v] ← u
            open.push(g_new + h(v), v); generated += 1
    max_frontier ← max(max_frontier, len(open))
cost ← g[t]
```

#### `src/search/ucs.py`

- `ucs(sg, s, t, trace_level="none")` = `astar` với `h = zero`, đổi tên `algorithm="UCS"`.
- `ucs_all(sg, s) -> dict[node, dist]` — Dijkstra một nguồn đến mọi nút (không dừng ở đích). Dùng cho bảng tỉ lệ vòng.

#### `src/search/__init__.py`

- `ALGORITHMS = {"BFS": bfs, "GBFS": gbfs, "ASTAR": astar, "UCS": ucs}`
- `run(name, sg, s, t, heuristic_name, trace_level)` — tự tạo h cho GBFS/A\*.

---

### 8.5. `src/routing/multi_stop.py` (nâng cao)

- **Nhiệm vụ:** kịch bản M1, một xe đi qua nhiều khách.
- **Hàm cần viết:**
  - `nearest_neighbor_order(sg, depot, customers, rule) -> list[int]`
    - `rule="euclid"`: chọn khách gần nhất theo chim bay (rẻ, như bản brainstorm).
    - `rule="road"`: chọn theo quãng đường bộ (`ucs_all` từ điểm hiện tại).
  - `route_tour(sg, order, return_to_depot, algorithm="ASTAR") -> TourResult` — ghép các chặng; `TourResult` gồm danh sách `SearchResult` từng chặng, `total_m`, `total_expanded`.
- **Đầu ra:** `results/tables/multistop.csv` — `scenario, dataset, order_rule, order, total_m, total_expanded_astar, total_expanded_ucs`.
- **Insight muốn thấy:** thứ tự theo chim bay có thể chọn khách bên kia sông trước, làm tổng quãng đường dài hơn thứ tự theo đường bộ.

---

### 8.6. `src/experiments/`

#### `src/experiments/select_cases.py`

- **Nhiệm vụ:** biến các ca có tên thành cặp nút cụ thể trên từng đồ thị, kiểm tra tiêu chí ở mục 4.2, sinh đích ngẫu nhiên.
- **Hàm cần viết:**
  - `detour_table(sg, depot_node) -> DataFrame` — chạy `ucs_all` **một lần**; với mọi nút: `node, lat, lon, d_road_m, d_euclid_m, detour, bearing_deg`. Bỏ nút có `d_euclid_m < 200` khi tính detour (tránh chia cho số rất nhỏ). Lưu `results/tables/detour_<dataset>_<kho>.csv`.
  - `bearing(sg, a, b) -> float` — góc phương vị 0–360° (bắc = 0, theo chiều kim đồng hồ) tính trên UTM.
  - `check_case(case, sg, detour_df, cfg) -> dict` — tính các chỉ số và trạng thái `PASS` / `FAIL`. C3, C4 cần chạy GBFS/BFS để biết gap.
  - `auto_replace(case, ...) -> dict` — áp quy tắc "Nếu không đạt" ở bảng 4.2, gắn `auto_replaced=True` và `original_query`.
  - `sample_random_points(union_polygon, n, seed, depot_latlon, min_dist_m) -> DataFrame` — lấy mẫu loại bỏ (rejection sampling) trong polygon, cố định seed. Chạy **một lần**, lưu `results/tables/random_points.csv`, sau đó snap riêng vào từng đồ thị và loại điểm snap > 300 m.
  - `select_all() -> DataFrame` — ghép tất cả.
- **Đầu ra:** `results/tables/cases.csv` với cột:
  `case_id, property, dataset, depot_id, depot_node, target_id, target_query, target_lat, target_lon, target_node, snap_dist_m, d_euclid_m, d_road_m, detour, bearing_deg, check_status, auto_replaced, note`
- **Xong khi:** mọi ca có `check_status` là `PASS`, hoặc đã `auto_replaced` kèm ghi chú lý do.

#### `src/experiments/benchmark.py`

- **Nhiệm vụ:** chạy toàn bộ thí nghiệm.
- **Hàm cần viết:**
  - `run_case(sg, row, algorithms, heuristic, timing_cfg, save_trace) -> list[dict]` — với mỗi thuật toán: đo thời gian bằng `timed_run`; chạy thêm một lần `trace_level="order"` nếu cần lưu trace.
  - `run_dataset(name) -> DataFrame` — đọc `cases.csv`, lọc theo dataset, chạy mọi ca (có tên + R01–R50).
  - `run_level_A() -> DataFrame` — 132 cặp × 4 thuật toán; với các cặp trong `hand_trace_candidates`, lưu thêm trace mức `steps`.
  - `sanity_checks(df)` — với mỗi ca: `UCS.cost_m` khớp `nx.shortest_path_length` (sai số ≤ `cost_tol_m`); `ASTAR.cost_m == UCS.cost_m`; `ASTAR.reopened == 0`. Vi phạm thì **dừng chương trình** và in ca lỗi.
- **Đầu ra:**
  - `results/tables/runs.csv` — cột: `dataset, case_id, property, algorithm, source, target, found, expanded, generated, stale_skipped, reopened, max_frontier, hops, path_m, optimal_m, gap_pct, runtime_ms, d_euclid_m, detour`.
  - `results/tables/runs_A.csv` — cùng cột, `dataset = "A"`.
  - `results/traces/<dataset>_<case>_<algo>.json` — `{"path": [...], "expanded_order": [...]}`; mức A có thêm `"steps"`.
- **Xong khi:** `sanity_checks` qua hết.

#### `src/experiments/analyze.py`

- **Nhiệm vụ:** biến `runs.csv` thành câu trả lời cho RQ1–RQ4.
- **Hàm cần viết:**
  - `summary(df) -> DataFrame` — theo `dataset × algorithm`: trung bình và trung vị `expanded`, tỉ lệ `expanded / expanded_UCS`, trung vị `gap_pct`, % ca tối ưu (`gap_pct == 0`), trung vị `runtime_ms`. Lưu `summary.csv`.
  - `summary_by_property(df)` — bảng cho các ca có tên. Lưu `summary_by_property.csv`.
  - `gbfs_gap_vs_detour(df)` — hệ số tương quan Spearman giữa `gap_pct` của GBFS và `detour` (RQ2).
  - `expansion_scaling(df)` — hồi quy log(expanded) theo log(d_euclid) cho từng thuật toán, trả về hệ số góc (RQ4). Kỳ vọng BFS và UCS có hệ số lớn hơn A\*.
  - `bfs_report(df)` — với C4 và các đích ngẫu nhiên: so sánh `hops` và `path_m` của BFS với UCS (RQ3).
  - `to_markdown(tables)` — xuất bảng markdown để dán vào báo cáo (`results/tables/report_tables.md`).

---

### 8.7. `src/viz/`

Mọi bản đồ dùng **EPSG:4326** để hiển thị (folium nhận `[lat, lon]`). Cạnh lấy hình dạng từ `ox.convert.graph_to_gdfs(G)` rồi `.to_crs(4326)`. Không dùng các hàm folium cũ của OSMnx (đã bị bỏ ở 2.x); dùng `folium` trực tiếp hoặc `GeoDataFrame.explore()`. Bản đồ phải ghi nguồn "© OpenStreetMap contributors".

#### `src/viz/expansion_maps.py`

- `expansion_map_html(G, traces, case_row) -> folium.Map` — `folium.Map(prefer_canvas=True)`; mỗi thuật toán một `FeatureGroup` (bật/tắt bằng `LayerControl`): nút mở rộng màu vàng (có thể tô đậm dần theo thứ tự mở rộng), đường đi màu đỏ theo hình dạng thật của cạnh, marker kho và đích. Với BFS trên B1 có thể có hàng chục nghìn điểm: vẽ thành một lớp GeoJSON điểm thay vì từng marker.
- `expansion_panels_png(G, traces, case_row)` — matplotlib, 1 × 3 ô (BFS, GBFS, A\*), cùng khung nhìn, nền là mạng đường màu xám nhạt. Dùng cho báo cáo.
- **Đầu ra:** `results/maps/<dataset>_<case>.html`, `results/figures/fig_expansions_<dataset>_<case>.png`.

#### `src/viz/detour_heatmap.py`

- `detour_map(detour_df, G)` — tô màu mỗi nút theo `detour` (cắt khoảng 1,0–2,5), đánh dấu kho và các cầu (cạnh có tag `bridge`).
- **Đầu ra:** `results/maps/detour_<dataset>_<kho>.html`, `results/figures/fig_detour_<dataset>_<kho>.png`.

#### `src/viz/charts.py`

| Hình | Nội dung | RQ |
|---|---|---|
| `fig_expanded_by_case.png` | Cột: `expanded` theo ca có tên × thuật toán, trục y log | RQ1, RQ4 |
| `fig_expanded_vs_distance.png` | Điểm: `expanded` theo `d_euclid` (C5 + R01–R50), mỗi thuật toán một màu, trục log | RQ4 |
| `fig_gbfs_gap_vs_detour.png` | Điểm: `gap_pct` của GBFS theo `detour` | RQ2 |
| `fig_bfs_hops_vs_km.png` | Cột: `hops` và `path_m` của BFS so với UCS | RQ3 |
| `fig_b1_vs_b2.png` | Cột: trung vị `expanded` trên B1 và B2 | RQ4 |
| `fig_dataset_overview.png` | Hai bản đồ B1, B2 cạnh nhau | Mô tả dữ liệu |
| `fig_levelA_graph.png` | Đồ thị A đè lên 12 quận, ghi trọng số (km) | Chạy tay |

Màu cố định cho từng thuật toán trong mọi hình (khai báo một lần trong `charts.py`).

---

### 8.8. `scripts/`

Mỗi script là một lớp mỏng: đọc tham số dòng lệnh (`argparse`), gọi hàm trong `src/`, in tóm tắt, cập nhật `run_metadata.json`.

| Script | Gọi | Tham số |
|---|---|---|
| `01_download.py` | `download.download_dataset` | `--dataset B1|B2|all`, `--force` |
| `02_preprocess.py` | `preprocess.preprocess_dataset` | `--dataset` |
| `03_build_district_graph.py` | `district_graph` | — |
| `04_select_cases.py` | `select_cases.select_all` | `--dataset` |
| `05_run_benchmark.py` | `benchmark.run_dataset`, `run_level_A`, `analyze` | `--dataset`, `--skip-A`, `--no-traces` |
| `06_make_figures.py` | `viz.*` | `--only maps|charts|all` |
| `07_multi_stop.py` | `routing.multi_stop` | `--scenario M1` |

---

### 8.9. `notebooks/`

#### `01_explore_data.ipynb` — kiểm tra dữ liệu trước khi chạy thí nghiệm

- Vẽ 12 quận, bbox và các điểm kho/đích; xác nhận **mọi điểm nằm trong bbox**.
- Vẽ B1 và B2; in `dataset_stats.csv`.
- Kiểm tra cầu: có cầu Chương Dương, Vĩnh Tuy, Thanh Trì, Nhật Tân trong B1 và B2; **không có cầu Long Biên** trong B1 (cấm ô tô).
- Xem tag `highway` của Vành đai 3 trên cao để xác nhận bộ lọc B2 giữ được nó.
- Kiểm tra tỉ lệ nút giữ lại sau LSCC của B2 để quyết định `include_tertiary`.

#### `02_hand_trace_level_A.ipynb` — chạy tay mức A

- Vẽ đồ thị A với trọng số (km, một chữ số thập phân) và bảng h.
- Với cặp đã chọn, in bảng từng bước cho BFS, GBFS, A\*:

| Bước | Rút ra | g | h | f | Frontier sau bước (nút: f) | Closed |
|---|---|---|---|---|---|---|

- So sánh đường đi và số nút mở rộng của ba thuật toán trên cặp này.

#### `03_results_discussion.ipynb`

- Nạp `runs.csv`, `summary*.csv`; trả lời lần lượt RQ1–RQ4 kèm hình.
- Đối chiếu kết quả với các giả thuyết ở mục 10.

---

## 9. Kiểm thử

Chạy bằng `pytest -q`. Các test trên đồ thị thật tự `skip` nếu chưa có `data/processed/`.

### 9.1. `tests/conftest.py` — đồ thị đồ chơi

Toàn bộ là **vô hướng** trừ `toy_stale`. Tọa độ tính bằng mét; mọi trọng số ≥ khoảng cách Euclid giữa hai đầu nên h hợp lệ.

**`toy_bfs_bias`** — BFS chọn đường ít cạnh nhưng dài.

| Nút | 0 (S) | 1 (P) | 2 (Q) | 3 (R) | 4 (X) | 5 (T) |
|---|---|---|---|---|---|---|
| (x, y) | (0, 0) | (75, 0) | (150, 0) | (225, 0) | (150, 400) | (300, 0) |

Cạnh: 0–1: 100, 1–2: 100, 2–3: 100, 3–5: 100, 0–4: 500, 4–5: 500.

**`toy_gbfs_trap`** — "con sông": nút 1 rất gần đích theo chim bay nhưng cạnh 1–4 phải vòng xa.

| Nút | 0 (S) | 1 (N) | 2 (U) | 3 (V) | 4 (T) |
|---|---|---|---|---|---|
| (x, y) | (0, 0) | (900, 0) | (0, 600) | (1000, 600) | (1000, 0) |

Cạnh: 0–1: 900, 1–4: 2000, 0–2: 600, 2–3: 1000, 3–4: 600.

**`toy_stale`** — **có hướng**, mọi nút cùng tọa độ (0, 0) nên h ≡ 0.
Cạnh: 0→1: 5, 0→2: 1, 2→1: 1, 1→3: 1, 3→4: 10.

**`toy_grid`** — lưới 3 × 3, id 0–8 theo hàng, cạnh ngang/dọc dài 100, tọa độ (100·cột, 100·hàng). Nhiều đường cùng chi phí, dùng để kiểm tra phá hòa.

### 9.2. `tests/test_toy_graphs.py` — giá trị kỳ vọng (đã tính tay)

| Đồ thị (s → t) | Thuật toán | path | cost_m | hops | expanded |
|---|---|---|---|---|---|
| `toy_bfs_bias` (0 → 5) | BFS | [0, 4, 5] | 1000 | 2 | 5 |
| | UCS | [0, 1, 2, 3, 5] | 400 | 4 | 5 |
| | A\* | [0, 1, 2, 3, 5] | 400 | 4 | 5 |
| `toy_gbfs_trap` (0 → 4) | BFS | [0, 1, 4] | 2900 | 2 | 4 |
| | GBFS | [0, 1, 4] | 2900 | 2 | 3 |
| | A\* | [0, 2, 3, 4] | 2200 | 3 | 5 |
| | UCS | [0, 2, 3, 4] | 2200 | 3 | 5 |

Đây là phiên bản thu nhỏ của C3 và C4: GBFS mở rộng ít nhất nhưng sai đường, A\* đúng đường.

### 9.3. `tests/test_counting.py`

- `toy_stale`, UCS (hoặc A\* với h ≡ 0), 0 → 4: `path = [0, 2, 1, 3, 4]`, `cost_m = 13`, `expanded = 5`, `generated = 6`, `stale_skipped = 1`, `max_frontier = 2`.
- Nguồn trùng đích: `expanded = 1`, `path = [s]`, `cost_m = 0`, `hops = 0`.
- Không tới được (đồ thị có hướng 0→1, tìm 1 → 0): `found = False`, `path = []`, `cost_m = inf`.

### 9.4. `tests/test_determinism.py`

- Chạy mỗi thuật toán hai lần trên `toy_grid` (0 → 8): `expanded_order` và `path` giống hệt nhau.
- Thứ tự hàng xóm trong `SearchGraph.adj` luôn tăng dần theo id.

### 9.5. `tests/test_heuristic.py` (đồ thị thật)

- Với 20 đích ngẫu nhiên trên B1 và B2 (seed cố định): với **mọi cạnh** (u, v), `h(u) ≤ c(u, v) + h(v) + 1e-6`.
- Với đồ thị A: `weight_m ≥ h(u, v)` cho mọi cạnh và mọi cặp đích.

### 9.6. `tests/test_optimality.py` (đồ thị thật)

- 30 cặp ngẫu nhiên trên B2 (và 10 cặp trên B1 nếu đủ thời gian): `astar.cost_m == ucs.cost_m == nx.shortest_path_length(..., weight="length")` với sai số ≤ 0,01 m; `astar.reopened == 0`; `astar.expanded ≤ ucs.expanded` (có thể lệch vài nút do phá hòa; nếu lệch, ghi cảnh báo thay vì fail).

---

## 10. Kết quả đầu ra và câu hỏi mà mỗi kết quả trả lời

### 10.1. Bảng

| File | Nội dung |
|---|---|
| `dataset_stats.csv` | Kích thước B1, B2 trước/sau LSCC |
| `A_edges.csv`, `A_heuristic_matrix.csv` | Đồ thị A để chạy tay |
| `cases.csv`, `random_points.csv`, `detour_*.csv` | Ca thử và tỉ lệ vòng |
| `runs.csv`, `runs_A.csv` | **Bảng gốc** của mọi lần chạy |
| `summary.csv`, `summary_by_property.csv` | Tổng hợp theo thuật toán, đồ thị, tính chất |
| `multistop.csv` | Kịch bản M1 |
| `report_tables.md` | Bảng markdown để dán vào báo cáo |

### 10.2. Giả thuyết cần kiểm chứng (không phải kết luận có sẵn)

- **H1 (RQ1):** `gap_pct(A*) = 0` ở mọi ca; `expanded(A*) ≤ expanded(UCS)`.
- **H2 (RQ2):** GBFS có `expanded` nhỏ nhất ở phần lớn ca; `gap_pct(GBFS)` tăng theo `detour` (tương quan dương).
- **H3 (RQ3):** `gap_pct(BFS) > 0` ở phần lớn ca; lớn nhất ở C4.
- **H4 (RQ4):** `expanded` tăng theo khoảng cách; BFS và UCS tăng nhanh hơn A\* (hệ số góc log–log lớn hơn); `expanded` trên B1 lớn hơn nhiều so với B2.
- **Hình dạng vùng mở rộng (mục 3.6 của bản brainstorm):** BFS và UCS loang rộng quanh kho; A\* thon dài về phía đích; GBFS hẹp nhưng có thể lạc hướng khi gặp vật cản. Đây là kỳ vọng, cần đối chiếu với `fig_expansions_*`.

---

## 11. Quy ước chung

- **Đơn vị:** mét ở mọi chỗ tính toán; km chỉ dùng khi hiển thị.
- **CRS:** tính toán trên **EPSG:32648**; hiển thị trên **EPSG:4326**.
- **Thứ tự tọa độ (dễ nhầm):**
  - `pyproj` với `always_xy=True`: `(lon, lat)` → `(x, y)`.
  - `ox.distance.nearest_nodes(G, X=x, Y=y)`: X là kinh độ/x, Y là vĩ độ/y.
  - `folium`: `[lat, lon]`.
  - bbox của OSMnx 2.x: `(west, south, east, north)`.
- **Tên file:** `<dataset>_<case>_<algo>` cho trace và hình; `<dataset>_<YYYYMMDD>` cho dữ liệu thô.
- **Tính tái lập:** seed trong `experiment.yaml`; ghim phiên bản thư viện trong `requirements.txt`; mọi script cập nhật `run_metadata.json`.
- **`.gitignore`:** `data/raw/`, `data/processed/`, `data/interim/`, `results/traces/`, `results/maps/`, `cache/` (thư mục cache của OSMnx), `.venv/`. Giữ lại `config/`, `results/tables/`, `results/figures/`.

---

## 12. Hạn chế

Ghi đầy đủ trong `docs/limitations.md`:

- **Cấm rẽ, cấm quay đầu không được mô hình hóa.** Đồ thị có hướng chỉ ngăn đi ngược chiều; đường tìm được có thể chứa một chỗ rẽ bị cấm.
- **Không có thời gian, tắc đường, đèn tín hiệu, giờ cấm tải.** Đích nội thành như Quảng trường Ba Đình trên thực tế hạn chế xe tải.
- **B1 là mạng ô tô, không phải xe máy:** có đường cấm xe máy, thiếu cầu Long Biên và các ngõ chỉ xe máy vào được.
- **Chất lượng OSM:** có thể thiếu đường, sai tag một chiều; dữ liệu là ảnh chụp theo ngày tải.
- **Snap vào giao lộ gần nhất:** lệch đến vài trăm mét so với vị trí thật của khách.
- **Mức A:** đi qua điểm đại diện của từng quận nên quãng đường dài hơn đường đi thẳng trên B2. Ranh giới 12 quận cũ không còn hiệu lực hành chính từ 01/07/2025.
- **Thời gian chạy** đo bằng Python thuần, phụ thuộc máy; chỉ dùng để tham khảo.

---

## 13. Những điểm đã chỉnh so với bản brainstorm

1. **Điều kiện admissible:** so h(n) với chi phí thật **còn lại** h\*(n), không so với g(n). `length` là chi phí một cạnh, g(n) là tổng các cạnh.
2. **B1 = ô tô, không phải xe máy** (để thống nhất với ca C3 dựa vào việc không có cầu Long Biên).
3. **Bộ lọc B2** thêm `motorway` và các nhánh `*_link`, cùng các điều kiện loại trừ `access`/`motor_vehicle`/`motorcar`.
4. **Snapping:** chiếu điểm sang UTM trước khi gọi `nearest_nodes`.
5. **bbox** tính tự động từ 12 quận + đệm 3 km, đủ chứa mọi kho, đích và cầu Nhật Tân.
6. **Mức A** có cách dựng cụ thể: nút, quy tắc cạnh, trọng số làm tròn lên, h làm tròn xuống.
7. **API OSMnx 2.x:** `ox.truncate.largest_component`, bbox `(west, south, east, north)`, vẽ bằng folium trực tiếp.
8. **Diễn đạt chặt hơn:** "lộ trình hợp pháp" → "không đi ngược chiều"; BFS không "sụp đổ" mà mở rộng nhiều nút và cho đường không tối ưu theo mét; ví dụ BFS dùng "tuyến trên cao ít nút giao" thay cho "đại lộ 5 km là 1 cạnh"; các con số 95–99% và 70–85% thay bằng số đo thật trong `dataset_stats.csv`; LSCC bảo đảm có đường đi, còn vòng lặp do tập Closed chặn.
9. **Quy ước đếm** bổ sung: bỏ qua mục cũ trong heap, kiểm tra đích khi rút ra, cạnh song song giữ cạnh ngắn nhất, bộ đếm `reopened`.
10. **Thiết kế thí nghiệm** bổ sung: điểm ngẫu nhiên lấy một lần rồi snap riêng vào B1 và B2; kiểm tra tự động từng ca; giả thuyết H1–H4 thay cho "kết luận có sẵn".
11. **Cấu trúc thư mục** thêm `config.py`, `study_area.py`, `loaders.py`, `search/graph.py`, `districts.yaml`, `results/traces/`, `tests/conftest.py`, `test_determinism.py` và script `07_multi_stop.py`.

---

## 14. Lộ trình code đề xuất

| Bước | Việc | Xong khi |
|---|---|---|
| 1 | `search/` (graph, result, common, heuristics, 4 thuật toán) + `conftest.py` | `test_toy_graphs`, `test_counting`, `test_determinism` đều qua. **Chưa cần dữ liệu Hà Nội.** |
| 2 | `config.py`, `study_area.py`, `download.py`, `preprocess.py`, `loaders.py` + script 01, 02 | Có `B1.graphml`, `B2.graphml`, `dataset_stats.csv`; notebook 01 qua hết các mục kiểm tra |
| 3 | `test_heuristic`, `test_optimality` trên đồ thị thật | Qua hết |
| 4 | `locations.py`, `select_cases.py` + script 04 | `cases.csv` đầy đủ, mọi ca `PASS` hoặc đã thay tự động có ghi chú |
| 5 | `benchmark.py`, `analyze.py` + script 05 (chưa cần mức A) | `runs.csv`, `summary.csv`; `sanity_checks` qua |
| 6 | `viz/` + script 06 | Có đủ hình ở mục 8.7 |
| 7 | `district_graph.py` + script 03, chạy lại 05 với mức A, notebook 02 | `runs_A.csv`, bảng chạy tay từng bước |
| 8 | `multi_stop.py` + script 07 (nâng cao) | `multistop.csv`, bản đồ M1 |
| 9 | Notebook 03, `docs/`, báo cáo | Trả lời RQ1–RQ4 bằng số liệu và hình |

---

## 15. Cài đặt và chạy

### 15.1. Yêu cầu

`requirements.txt` (ghim phiên bản cụ thể sau khi cài lần đầu bằng `pip freeze`):

```
osmnx>=2.0,<3
networkx>=3.2
geopandas>=1.0
shapely>=2.0
pyproj>=3.6
scipy
numpy
pandas
matplotlib
folium
geopy
pyyaml
pytest
jupyter
```

Python ≥ 3.10.

### 15.2. Chuẩn bị dữ liệu ngoài

Tải ranh giới hành chính Việt Nam **cấp 2** từ GADM (gadm.org → Download → Vietnam), đặt vào `data/external/` và sửa `gadm_file` trong `config/datasets.yaml` cho khớp tên file.

### 15.3. Chạy

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest -q tests/test_toy_graphs.py tests/test_counting.py tests/test_determinism.py

python scripts/01_download.py --dataset all
python scripts/02_preprocess.py --dataset all
python scripts/03_build_district_graph.py
python scripts/04_select_cases.py --dataset all
python scripts/05_run_benchmark.py --dataset all
python scripts/06_make_figures.py --only all
python scripts/07_multi_stop.py --scenario M1      # tùy chọn

pytest -q                                           # chạy toàn bộ test
```

---

## 16. Giấy phép dữ liệu

- **OpenStreetMap:** dữ liệu theo giấy phép ODbL. Mọi bản đồ và hình phải ghi "© OpenStreetMap contributors".
- **GADM:** miễn phí cho mục đích học thuật và phi thương mại; không được phân phối lại. Xem điều khoản trên trang GADM trước khi đưa file vào repo (khuyến nghị: không commit, chỉ hướng dẫn tải).