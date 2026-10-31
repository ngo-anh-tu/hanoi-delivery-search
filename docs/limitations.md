# Hạn chế

## Mô hình

- **Cấm rẽ, cấm quay đầu không được mô hình hóa.** Đồ thị có hướng chỉ ngăn đi ngược chiều; đường tìm được có thể chứa một chỗ rẽ bị cấm.
- **Không có thời gian, tắc đường, đèn tín hiệu, giờ cấm tải.** Đích nội thành như Quảng trường Ba Đình trên thực tế hạn chế xe tải.
- **B1 là mạng ô tô, không phải xe máy:** có đường cấm xe máy, thiếu cầu Long Biên và các ngõ chỉ xe máy vào được.
- **Mức A:** đi qua điểm đại diện của từng quận nên quãng đường dài hơn đường đi thẳng trên B2. Ranh giới 12 quận cũ không còn hiệu lực hành chính từ 01/07/2025.
- **Thời gian chạy** đo bằng Python thuần, phụ thuộc máy; chỉ dùng để tham khảo.

## Dữ liệu

- **Chất lượng OSM:** có thể thiếu đường, sai tag một chiều; dữ liệu là ảnh chụp theo ngày tải (31/10/2026 UTC, xem `results/run_metadata.json`).
- **Snap vào giao lộ gần nhất:** lệch đến vài trăm mét so với vị trí thật của khách. Trên B2, bốn điểm vượt ngưỡng 300 m: K2 (312 m), Quảng An (350 m), SVĐ Mỹ Đình (371 m), Phủ Tây Hồ (1 118 m). Các điểm này được giữ lại và ghi chú trong `cases.csv`.
- **Tọa độ địa danh điền tay** từ đối tượng OSM cùng tên, vì không truy cập được Nominatim lúc chạy. K2 và Quảng An lấy theo UBND phường, không phải tâm phường.
- **Điểm đại diện quận là `representative_point()` của polygon GADM**, không phải trụ sở UBND. Polygon GADM khá thô (997 đỉnh cho cả 12 quận).

## Thí nghiệm

- **Đích ngẫu nhiên trên B2 chỉ còn 23/50** (B1 còn 48/50) vì nhiều điểm cách trục chính quá 300 m. Tập còn lại thiên về các điểm gần trục chính. So sánh B1 với B2 chỉ dùng 23 đích chung; thống kê trên B2 có độ tin cậy thấp hơn.
- **C3b là đích chọn tự động trên cả B1 và B2** vì Phủ Tây Hồ có detour 1,34 và 1,25, dưới ngưỡng 1,40. Đích thay thế có detour 3,61 và 3,15, không phải một địa danh.
- **Tương quan gap(GBFS) với detour khi gộp mọi ca bị ảnh hưởng bởi cách chọn ca:** C3b được chọn chính vì có detour lớn và gap > 0. Nên đọc kèm số liệu riêng của nhóm ngẫu nhiên.
- **Tổng quãng đường M1 trên B1 và B2 không so sánh trực tiếp được:** trên B2, Phủ Tây Hồ được snap vào nút cách 1 118 m nên xe không đi vào đến nơi.
- **Mức A có BFS tối ưu ở cả 132 cặp**, nên không minh họa được RQ3. Dùng ca C4 hoặc đồ thị đồ chơi `toy_bfs_bias` để giải thích.
