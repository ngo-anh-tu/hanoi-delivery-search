# Hanoi Delivery Search — So sánh BFS, GBFS và A\* trên bản đồ Hà Nội

Tìm đường từ **kho** đến **khách hàng** trên bản đồ thật của Hà Nội (OpenStreetMap) bằng **BFS**, **Greedy Best-First Search (GBFS)** và **A\***, dùng **UCS/Dijkstra** làm đáp án chuẩn. So sánh số nút mở rộng và chiều dài đường đi trên ba đồ thị:

| Đồ thị | Mức | Nút | Cạnh có hướng | Dùng để |
|---|---|---|---|---|
| **A** | 12 quận nội thành cũ | 12 | 30 (15 cạnh vô hướng) | Chạy tay từng bước |
| **B1** | Mạng chi tiết cho ô tô (`drive`) | 56 348 | 138 445 | So sánh trên mạng dày |
| **B2** | Mạng trục chính | 3 890 | 7 027 | So sánh trên mạng thưa |

Số cạnh là sau khi gộp cạnh song song và bỏ self-loop. Chi phí là quãng đường tính bằng mét; không xét thời gian hay tắc đường.

Tài liệu: [đặc tả và các sai khác khi cài đặt](docs/design.md), [hạn chế](docs/limitations.md), [bảng kết quả](results/tables/report_tables.md).

## Kết quả chính

Dữ liệu OSM chụp ngày 31/10/2026 (UTC). Có 56 ca trên B1 và 31 ca trên B2 (gồm các ca có tên và đích ngẫu nhiên), cộng 132 cặp quận ở mức A.

| Đồ thị | Thuật toán | Trung vị nút mở rộng | So với UCS (trung vị) | Trung vị gap | Gap lớn nhất | Ca tối ưu |
|---|---|---:|---:|---:|---:|---:|
| B1 | BFS | 21 501 | 132,4% | 32,2% | 122,1% | 5,4% |
| B1 | GBFS | 146 | 1,0% | 34,0% | 73,0% | 5,4% |
| B1 | A\* | 1 892 | 14,5% | 0% | 0% | 100% |
| B1 | UCS | 17 650 | 100% | 0% | 0% | 100% |
| B2 | BFS | 1 742 | 121,9% | 20,6% | 123,9% | 12,9% |
| B2 | GBFS | 71 | 5,7% | 28,9% | 109,4% | 9,7% |
| B2 | A\* | 268 | 21,2% | 0% | 0% | 100% |
| B2 | UCS | 1 513 | 100% | 0% | 0% | 100% |

![Số nút mở rộng theo ca](results/figures/fig_expanded_by_case.png)

### Đối chiếu giả thuyết

| Giả thuyết | Kết quả | Số liệu |
|---|---|---|
| **H1.** A\* luôn tối ưu và mở rộng không nhiều hơn UCS | **Đạt** | Gap = 0 ở cả 87 ca và 132 cặp mức A; `reopened` = 0; không ca nào A\* mở rộng nhiều hơn UCS |
| **H2a.** GBFS mở rộng ít nhất ở phần lớn ca | **Đạt** | 98,9% số ca (tính cả hòa) |
| **H2b.** Gap của GBFS tăng theo tỉ lệ vòng | **Chỉ yếu** | Mọi ca: ρ = 0,37 (p = 0,006) trên B1, ρ = 0,26 (p = 0,18) trên B2. Riêng đích ngẫu nhiên: ρ = 0,25 (p = 0,09) và ρ = −0,03 (p = 0,91) |
| **H3a.** BFS không tối ưu ở phần lớn ca | **Đạt** | 92% số ca có gap > 0 |
| **H3b.** Gap của BFS lớn nhất ở C4 | **Không đạt** | C4 là 46,3% (B1) và 21,9% (B2); lớn nhất là 122,1% ở R26 và 123,9% ở R14 |
| **H4a.** Số nút mở rộng tăng theo khoảng cách | **Đạt** | Hệ số góc log–log đều dương, từ 1,15 đến 2,05 |
| **H4b.** BFS, UCS tăng nhanh hơn A\* | **Không đạt** | B1: A\* 2,05, UCS 1,66, BFS 1,62. B2: A\* 1,82, BFS 1,73, UCS 1,65 |
| **H4c.** B1 mở rộng nhiều hơn B2 | **Đạt** | Trên 23 đích chung: gấp 8,0 lần (BFS), 7,9 (UCS), 5,6 (A\*), 1,9 (GBFS) |

Về H4b: A\* vẫn mở rộng ít nút hơn nhiều ở mọi khoảng cách, nhưng tỉ lệ tiết kiệm giảm dần khi đích xa hơn. Ví dụ trên B1, A\*/UCS là 3% ở C5a (1,7 km), 4% ở C5b (4,6 km) và 8% ở C5c (7,8 km).

Ca C3 (K2 → Quảng An, phải qua sông Hồng) cho thấy rõ cái bẫy của GBFS trên B1: GBFS mở rộng 1 698 nút nhưng đi 15,17 km, A\* mở rộng 1 915 nút và đi 9,76 km.

![Vùng mở rộng của ca C3 trên B1](results/figures/fig_expansions_B1_C3.png)

**Mức A:** BFS tối ưu ở cả 132 cặp, GBFS tối ưu ở 83,3% (gap lớn nhất 38,3%). Cả hai ứng viên chạy tay ở đặc tả đều cho GBFS trùng A\*, nên notebook 02 dùng cặp TX → CG: GBFS đi 13,0 km, A\* đi 9,4 km.

**Kịch bản nhiều điểm dừng M1:** chọn khách gần nhất theo chim bay hay theo đường bộ đều ra **cùng một thứ tự**, nên không quan sát được khác biệt mong đợi với năm khách này. Tổng 42,6 km trên B1; A\* mở rộng 7 314 nút so với 49 282 của UCS.

**Về heuristic:** cài đặt dùng `haversine` thay vì `euclid_utm`, vì đo trên dữ liệu thật cho thấy `euclid_utm` không consistent trên khoảng 20% số cạnh. Xem [mục 2.2 của đặc tả](docs/design.md#22-vì-sao-euclid-trên-utm-thỏa-cả-hai-điều-kiện).

## Hướng dẫn tái lập từ đầu

Các bước dưới đây chạy theo đúng thứ tự. Nên chạy từ thư mục gốc của repository
(`hanoi-delivery-search/`); các đường dẫn trong cấu hình đều tính tương đối từ
thư mục này.

### 1. Lấy mã nguồn và cài môi trường

Đã kiểm tra với Python 3.14. Các phiên bản thư viện được ghim trong
`requirements.txt`.

**Windows PowerShell:**

```powershell
git clone https://github.com/ngo-anh-tu/hanoi-delivery-search.git
cd hanoi-delivery-search
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu PowerShell chặn activate script, có thể gọi Python trong môi trường ảo
trực tiếp bằng `.venv\Scripts\python.exe`. Trên macOS/Linux, thay hai lệnh tạo
và kích hoạt môi trường bằng:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

### 2. Tải file ngoài bắt buộc

Tải ranh giới hành chính Việt Nam **cấp 2** từ
[GADM](https://gadm.org/download_country.html):

1. Chọn **Vietnam** → **Geopackage** (không chọn JSON cấp 2).
2. Đặt file tải về tại `data/external/gadm41_VNM.gpkg`.
3. Kiểm tra cấu hình `config/datasets.yaml` vẫn có:
   `gadm_file: data/external/gadm41_VNM.gpkg` và
   `gadm_layer: ADM_ADM_2`.

Có thể tải trực tiếp bằng PowerShell (nếu URL GADM còn giữ cấu trúc hiện tại):

```powershell
New-Item -ItemType Directory -Force data\external | Out-Null
Invoke-WebRequest `
  -Uri https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_VNM.gpkg `
  -OutFile data\external\gadm41_VNM.gpkg
```

Không cần tự tải B1/B2: `scripts/01_download.py` sẽ truy vấn OpenStreetMap
qua Overpass. Vì vậy
cần Internet; lần tải đầu có thể mất vài phút và phụ thuộc máy chủ Overpass.
Nếu đã có snapshot `.graphml` do nhóm cung cấp, đặt chúng vào `data/raw/` với
tên dạng `B1_YYYYMMDD.graphml` và `B2_YYYYMMDD.graphml`; script sẽ dùng lại
chúng thay vì tải lại.

### 3. Kiểm tra nhanh trước khi tải dữ liệu

```powershell
python -m pytest -q tests/test_toy_graphs.py tests/test_counting.py tests/test_determinism.py
```

Các test này không cần dữ liệu bản đồ thật.

### 4. Chạy pipeline dựng dữ liệu và kết quả

Chạy lần lượt, không bỏ qua bước ở giữa:

```powershell
# 01 — tải OSM, tạo data/raw/B1_<ngày>.graphml và B2_<ngày>.graphml
python scripts/01_download.py --dataset all

# 02 — làm sạch, lấy LSCC, chiếu UTM 48N
#      tạo data/processed/B1.graphml, B2.graphml
python scripts/02_preprocess.py --dataset all

# 03 — dựng đồ thị 12 quận mức A từ GADM và B2
#      tạo data/processed/A.graphml cùng các bảng A_*.csv
python scripts/03_build_district_graph.py

# 04 — chọn ca thử và đích ngẫu nhiên
#      tạo results/tables/cases.csv và detour_<dataset>_<kho>.csv
python scripts/04_select_cases.py --dataset all

# 05 — chạy BFS, GBFS, A* và UCS
#      tạo runs.csv, runs_A.csv, summary*.csv và trace
python scripts/05_run_benchmark.py --dataset all

# 06 — tạo biểu đồ PNG và bản đồ HTML
python scripts/06_make_figures.py --only all

# 07 — tùy chọn: chạy kịch bản nhiều điểm dừng M1
python scripts/07_multi_stop.py --scenario M1
```

`01_download.py` bỏ qua snapshot đã có. Dùng `--force` chỉ khi muốn tải lại
OSM và tạo snapshot mới:

```powershell
python scripts/01_download.py --dataset all --force
```

Có thể chạy riêng một dataset bằng `--dataset B1` hoặc `--dataset B2` ở các
bước 01, 02, 04 và 05. Bước 03 luôn cần cả dữ liệu cấu hình mức A và B2.

### 5. Kiểm tra toàn bộ và mở kết quả

```powershell
python -m pytest -q
```

Test trên đồ thị thật sẽ tự bỏ qua nếu chưa có `data/processed/`. Kết quả
chính nằm trong `results/tables/`, hình trong `results/figures/`, và bản đồ
HTML tương tác trong `results/maps/`.

### 6. Chạy demo web

Chỉ chạy sau bước 02 (để có B1/B2 đã xử lý); nếu muốn xem các trace và bản đồ
đã sinh thì chạy tiếp bước 04–06 trước:

```powershell
python app/server.py
```

Mở [http://127.0.0.1:5000](http://127.0.0.1:5000), chọn đồ thị, kho và đích
(hoặc bấm lên bản đồ) để xem bốn thuật toán chạy song song. Dừng server bằng
`Ctrl+C`.

### 7. Mở các notebook (tùy chọn)

Sau khi chạy pipeline, mở Jupyter:

```powershell
python -m jupyter notebook
```

Chạy theo thứ tự `notebooks/01_explore_data.ipynb` →
`notebooks/02_hand_trace_level_A.ipynb` →
`notebooks/03_results_discussion.ipynb`. Notebook 01 dùng dữ liệu đã xử lý;
notebook 02 cần đồ thị A; notebook 03 cần các bảng kết quả từ bước 05.

| Thư mục | Nội dung |
|---|---|
| `results/tables/` | `runs.csv`, `runs_A.csv` là bảng gốc; `summary*.csv`, `cases.csv`, `multistop.csv`, `report_tables.md` |
| `results/figures/` | Biểu đồ và hình vùng mở rộng |
| `results/maps/` | Bản đồ HTML tương tác: bật/tắt từng thuật toán, tỉ lệ vòng, tour M1 |
| `notebooks/` | `01` kiểm tra dữ liệu, `02` bảng chạy tay mức A, `03` trả lời RQ1–RQ4 |

## Giấy phép dữ liệu

- **OpenStreetMap:** dữ liệu theo giấy phép ODbL. © OpenStreetMap contributors.
- **GADM:** miễn phí cho mục đích học thuật và phi thương mại, không được phân phối lại. File không nằm trong repo, cần tải theo hướng dẫn trên.
