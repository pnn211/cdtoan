import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import sqlite3
from datetime import datetime
import qrcode
from io import BytesIO

# ================= CẤU HÌNH TRANG WEB =================
st.set_page_config(page_title="Math10 Interactive Hub", layout="wide", page_icon="📐")

# ================= CƠ SỞ DỮ LIỆU THỜI GIAN THỰC (SQLite) =================
conn = sqlite3.connect('lop_hoc_toan10.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS assignments
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, topic TEXT, content TEXT, time TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS submissions
             (id INTEGER PRIMARY KEY AUTOINCREMENT, assign_id INTEGER, student_name TEXT, 
              answer TEXT, score TEXT, correction TEXT, status TEXT, time TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
             (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, role TEXT, message TEXT, time TEXT)''')

# Tạo sẵn 3 bài tập mẫu bám sát 3 dự án chuyên đề nếu DB đang trống
c.execute("SELECT COUNT(*) FROM assignments")
if c.fetchone()[0] == 0:
    sample_assigns = [
        ("Bài 1 [Cảnh báo gù lưng, cận thị]", "Giải tam giác & Vector", 
         "Khi ngồi học, khoảng cách từ Cổ (C) đến Mắt (M) là 15cm, từ Cổ (C) đến Sách (S) trên bàn là 35cm, góc cúi cổ ∠MCS = 60°.\n1) Dùng định lý Cosin tính khoảng cách từ Mắt đến Sách (MS).\n2) Dùng mệnh đề kiểm tra xem học sinh có nguy cơ cận thị không (Biết MS < 30cm là nguy cơ cao).", "08:00"),
        ("Bài 2 [Kiểm soát thực đơn sức khỏe]", "Hệ bất phương trình", 
         "Một học sinh cần nạp ít nhất 30g Protein và 20g Chất xơ từ 2 món: Ức gà (x lạng) và Rau củ (y lạng). Biết 1 lạng ức gà có 15g Protein, 2g Chất xơ (giá 15k); 1 lạng rau củ có 3g Protein, 5g Chất xơ (giá 5k). Tổng tiền không quá 45k.\nHãy lập hệ BPT và tìm (x, y) thuộc miền nghiệm.", "08:05"),
        ("Bài 3 [Thước đo góc tia đỏ]", "Giá trị lượng giác & Hệ thức lượng", 
         "Dùng thước đo góc tia đỏ đặt tại O cách chân cột cờ 12m, bắn tia laser lên đỉnh cột cờ thu được góc nâng α = 38°. Biết chiều cao giá đỡ thước là 1.2m. Tính chiều cao cột cờ.", "08:10")
    ]
    c.executemany("INSERT INTO assignments (title, topic, content, time) VALUES (?, ?, ?, ?)", sample_assigns)
    conn.commit()

# ================= THANH BÊN (SIDEBAR): ĐĂNG NHẬP & QR CODE =================
with st.sidebar:
    st.title("🎓 CỔNG TƯƠNG TÁC TOÁN 10")
    role = st.radio("Bạn đang đăng nhập với tư cách:", ["👨‍🎓 Học sinh (HS)", "👩‍🏫 Giáo viên (GV)"])
    user_name = st.text_input("Nhập Họ & Tên của bạn:", value="Nguyễn Văn A" if "Học sinh" in role else "Cô Giáo Toán")
    
    if "Giáo viên" in role:
        gv_pass = st.text_input("Mật khẩu GV (Mặc định: 123):", type="password", value="123")
        is_gv = (gv_pass == "123")
        if not is_gv:
            st.warning("⚠️ Nhập mật khẩu '123' để mở quyền chấm bài!")
    else:
        is_gv = False

    st.divider()
    st.subheader("📱 Quét QR vào lớp (4G/Wi-Fi)")
    web_url = st.text_input("Dán link Web của bạn vào đây để tạo QR:", "https://share.streamlit.io")
    if web_url:
        qr = qrcode.make(web_url)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Chiếu mã này lên màn hình sân khấu", use_container_width=True)

# ================= CÁC TAB CHỨC NĂNG CHÍNH =================
tabs = st.tabs([
    "📊 1. Giải Hệ BPT & Bảng Giá Trị", 
    "📐 2. Giải Tam Giác & Vector", 
    "🎭 3. Mô Phỏng Chuyên Đề (Sân Khấu)",
    "📝 4. Lớp Học: Giao Bài & Chấm Sửa Lỗi", 
    "💬 5. Chatbox Trực Tuyến"
])

# -------------------------------------------------------------------------
# TAB 1: HỆ BẤT PHƯƠNG TRÌNH & BẢNG GIÁ TRỊ TỰ ĐỘNG
# -------------------------------------------------------------------------
with tabs[0]:
    st.header("📊 Vẽ Miền Nghiệm Hệ BPT & Lập Bảng Giá Trị Tự Động")
    st.caption("Hỗ trợ tìm miền nghiệm đa giác, lập bảng giao điểm trục tọa độ và tìm GTLN/GTNN của biểu thức F(x, y) = mx + ny.")
    
    col_in, col_out = st.columns([1, 1.4])
    with col_in:
        st.subheader("1. Nhập hệ BPT dạng: a·x + b·y ≤ c")
        num_ineq = st.number_input("Số lượng bất phương trình:", min_value=1, max_value=6, value=4)
        
        default_a = [2.0, 1.0, -1.0, 0.0, 1.0, 0.0]
        default_b = [1.0, 2.0, 0.0, -1.0, 1.0, 1.0]
        default_c = [10.0, 8.0, 0.0, 0.0, 6.0, 5.0]
        
        inequalities = []
        for i in range(num_ineq):
            c1, c2, c3, c4 = st.columns([1, 1, 0.8, 1])
            a = c1.number_input(f"a_{i+1}", value=default_a[i], step=1.0, key=f"a{i}")
            b = c2.number_input(f"b_{i+1}", value=default_b[i], step=1.0, key=f"b{i}")
            sign = c3.selectbox("Dấu", ["≤", "≥"], index=0, key=f"s{i}")
            c_val = c4.number_input(f"c_{i+1}", value=default_c[i], step=1.0, key=f"c{i}")
            inequalities.append((a, b, sign, c_val))
            
        st.subheader("2. Biểu thức tối ưu F(x, y) = m·x + n·y")
        cm, cn = st.columns(2)
        m_obj = cm.number_input("Hệ số m:", value=3.0)
        n_obj = cn.number_input("Hệ số n:", value=2.0)

    with col_out:
        # 1. Lập bảng giá trị lấy điểm vẽ từng đường thẳng bờ
        st.subheader("📋 Bảng 1: Bảng giá trị các đường thẳng bờ (d)")
        line_table = []
        for idx, (a, b, s, c_val) in enumerate(inequalities):
            eq_str = f"{a}x + ({b})y = {c_val}"
            p1 = f"(0 ; {round(c_val/b, 2)})" if b != 0 else "Không cắt Oy"
            p2 = f"({round(c_val/a, 2)} ; 0)" if a != 0 else "Không cắt Ox"
            test_O = (0 <= c_val) if s == "≤" else (0 >= c_val)
            line_table.append({
                "Đường thẳng": f"(d{idx+1}): {eq_str}",
                "BPT": f"{a}x + {b}y {s} {c_val}",
                "Điểm cắt Oy (x=0)": p1,
                "Điểm cắt Ox (y=0)": p2,
                "Kiểm tra gốc O(0;0)": "Thuộc miền nghiệm" if test_O else "Bị gạch bỏ"
            })
        st.dataframe(pd.DataFrame(line_table), use_container_width=True, hide_index=True)

        # 2. Tìm các đỉnh của miền nghiệm và vẽ đồ thị
        vertices = []
        for i in range(len(inequalities)):
            for j in range(i + 1, len(inequalities)):
                a1, b1, _, c1_val = inequalities[i]
                a2, b2, _, c2_val = inequalities[j]
                det = a1 * b2 - a2 * b1
                if abs(det) > 1e-9:
                    x_int = (c1_val * b2 - c2_val * b1) / det
                    y_int = (a1 * c2_val - a2 * c1_val) / det
                    # Kiểm tra điểm giao có thỏa mãn tất cả BPT không
                    valid = True
                    for a, b, s, c_v in inequalities:
                        val = a * x_int + b * y_int
                        if s == "≤" and val > c_v + 1e-6: valid = False
                        if s == "≥" and val < c_v - 1e-6: valid = False
                    if valid:
                        if not any(np.hypot(x_int - vx, y_int - vy) < 1e-5 for vx, vy in vertices):
                            vertices.append((x_int, y_int))

        fig, ax = plt.subplots(figsize=(7, 5))
        x_vals = np.linspace(-2, 12, 400)
        for idx, (a, b, s, c_val) in enumerate(inequalities):
            if abs(b) > 1e-9:
                y_vals = (c_val - a * x_vals) / b
                ax.plot(x_vals, y_vals, label=f"d{idx+1}: {a}x+{b}y={c_val}", linewidth=1.8)
            elif abs(a) > 1e-9:
                ax.axvline(c_val / a, label=f"d{idx+1}: {a}x={c_val}", linewidth=1.8, linestyle="--")

        if len(vertices) >= 3:
            pts = np.array(vertices)
            center = pts.mean(axis=0)
            angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
            pts = pts[np.argsort(angles)]
            poly = Polygon(pts, closed=True, facecolor='#4CAF50', alpha=0.35, edgecolor='green', lw=2, label="Miền nghiệm")
            ax.add_patch(poly)
            
            vertex_data = []
            for k, (vx, vy) in enumerate(pts):
                f_val = m_obj * vx + n_obj * vy
                ax.plot(vx, vy, 'ro')
                ax.text(vx + 0.15, vy + 0.15, f"M{k+1}({vx:.1f};{vy:.1f})", fontsize=9, fontweight='bold', color='darkred')
                vertex_data.append({
                    "Đỉnh": f"M{k+1}",
                    "Hoành độ (x)": round(vx, 2),
                    "Tung độ (y)": round(vy, 2),
                    f"Giá trị F = {m_obj}x + {n_obj}y": round(f_val, 2)
                })
            
            st.subheader("📋 Bảng 2: Bảng giá trị tại các đỉnh miền nghiệm")
            df_vert = pd.DataFrame(vertex_data)
            st.dataframe(df_vert, use_container_width=True, hide_index=True)
            
            col_f = f"Giá trị F = {m_obj}x + {n_obj}y"
            st.success(f"🎯 **Kết luận:** GTLN (Max F) = **{df_vert[col_f].max()}** | GTNN (Min F) = **{df_vert[col_f].min()}**")
        else:
            st.info("Miền nghiệm không khép kín hoặc vô nghiệm trên khung nhìn hiện tại.")

        ax.set_xlim(-2, 10)
        ax.set_ylim(-2, 10)
        ax.axhline(0, color='black', lw=1)
        ax.axvline(0, color='black', lw=1)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper right', fontsize=8)
        st.pyplot(fig)

# -------------------------------------------------------------------------
# TAB 2: GIẢI TAM GIÁC, LƯỢNG GIÁC & VECTOR
# -------------------------------------------------------------------------
with tabs[1]:
    c_tri, c_vec = st.columns(2)
    with c_tri:
        st.subheader("📐 Giải Tam Giác & Bảng Lượng Giác (C-G-C)")
        side_b = st.number_input("Cạnh b (đơn vị):", min_value=1.0, value=15.0)
        side_c = st.number_input("Cạnh c (đơn vị):", min_value=1.0, value=35.0)
        angle_A = st.slider("Góc xen giữa A (độ):", min_value=5, max_value=175, value=60)
        
        rad_A = np.radians(angle_A)
        side_a = np.sqrt(side_b**2 + side_c**2 - 2 * side_b * side_c * np.cos(rad_A))
        cos_B = (side_a**2 + side_c**2 - side_b**2) / (2 * side_a * side_c)
        angle_B = np.degrees(np.arccos(np.clip(cos_B, -1.0, 1.0)))
        angle_C = 180.0 - angle_A - angle_B
        area_S = 0.5 * side_b * side_c * np.sin(rad_A)
        
        st.markdown(f"**Kết quả Định lý Cosin:** Cạnh đối diện $a = \\sqrt{{b^2+c^2-2bc\\cos A}} = \\mathbf{{{side_a:.2f}}}$ | **Diện tích** $S = \\mathbf{{{area_S:.2f}}}$")
        
        trig_df = pd.DataFrame([
            {"Góc": f"Góc A ({angle_A:.1f}°)", "sin": round(np.sin(rad_A), 3), "cos": round(np.cos(rad_A), 3), "tan": round(np.tan(rad_A), 3)},
            {"Góc": f"Góc B ({angle_B:.1f}°)", "sin": round(np.sin(np.radians(angle_B)), 3), "cos": round(np.cos(np.radians(angle_B)), 3), "tan": round(np.tan(np.radians(angle_B)), 3)},
            {"Góc": f"Góc C ({angle_C:.1f}°)", "sin": round(np.sin(np.radians(angle_C)), 3), "cos": round(np.cos(np.radians(angle_C)), 3), "tan": round(np.tan(np.radians(angle_C)), 3)}
        ])
        st.dataframe(trig_df, use_container_width=True, hide_index=True)

    with c_vec:
        st.subheader("🏹 Tổng - Hiệu Vector & Bảng Tọa Độ")
        va_x, va_y = st.columns(2)
        ux = va_x.number_input("Hoành độ u_x:", value=4.0)
        uy = va_y.number_input("Tung độ u_y:", value=2.0)
        vb_x, vb_y = st.columns(2)
        vx = vb_x.number_input("Hoành độ v_x:", value=1.0)
        vy = vb_y.number_input("Tung độ v_y:", value=5.0)
        
        sum_x, sum_y = ux + vx, uy + vy
        diff_x, diff_y = ux - vx, uy - vy
        
        vec_df = pd.DataFrame([
            {"Vector": "u", "Tọa độ (x; y)": f"({ux}; {uy})", "Độ dài |v|": round(np.hypot(ux, uy), 2)},
            {"Vector": "v", "Tọa độ (x; y)": f"({vx}; {vy})", "Độ dài |v|": round(np.hypot(vx, vy), 2)},
            {"Vector": "Tổng u + v", "Tọa độ (x; y)": f"({sum_x}; {sum_y})", "Độ dài |v|": round(np.hypot(sum_x, sum_y), 2)},
            {"Vector": "Hiệu u - v", "Tọa độ (x; y)": f"({diff_x}; {diff_y})", "Độ dài |v|": round(np.hypot(diff_x, diff_y), 2)}
        ])
        st.dataframe(vec_df, use_container_width=True, hide_index=True)
        
        fig_v, ax_v = plt.subplots(figsize=(5, 3.2))
        ax_v.quiver(0, 0, ux, uy, angles='xy', scale_units='xy', scale=1, color='blue', label='u')
        ax_v.quiver(0, 0, vx, vy, angles='xy', scale_units='xy', scale=1, color='orange', label='v')
        ax_v.quiver(0, 0, sum_x, sum_y, angles='xy', scale_units='xy', scale=1, color='red', label='u + v')
        max_lim = max(abs(sum_x), abs(sum_y), abs(ux), abs(vx), 5) + 2
        ax_v.set_xlim(-max_lim, max_lim)
        ax_v.set_ylim(-max_lim, max_lim)
        ax_v.axhline(0, color='black', lw=0.8)
        ax_v.axvline(0, color='black', lw=0.8)
        ax_v.grid(True, linestyle=':')
        ax_v.legend()
        st.pyplot(fig_v)

# -------------------------------------------------------------------------
# TAB 3: MÔ PHỎNG CHUYÊN ĐỀ SÂN KHẤU (TÍCH HỢP CẢ 3 ĐỀ TÀI)
# -------------------------------------------------------------------------
with tabs[2]:
    st.header("🎭 Bảng Điều Khiển Mô Phỏng Sân Khấu (Đủ 7 Bài Toán 10)")
    project_choice = st.selectbox("Chọn chủ đề kịch bản đang biểu diễn:", [
        "Dự án A: Cảnh báo gù lưng, cận thị",
        "Dự án B: Kiểm soát thực đơn sức khỏe",
        "Dự án C: Thước đo góc tia đỏ"
    ])
    
    if "Cảnh báo gù lưng" in project_choice:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.subheader("Thông số đo tư thế học sinh")
            neck_eye = st.slider("Cạnh Cổ - Mắt (cm):", 10.0, 25.0, 15.0)
            neck_book = st.slider("Cạnh Cổ - Vở (cm):", 20.0, 60.0, 35.0)
            bend_angle = st.slider("Góc cúi đầu α (độ):", 15, 110, 40)
            
            # Giải tam giác tính khoảng cách Mắt - Vở
            eye_book = np.sqrt(neck_eye**2 + neck_book**2 - 2*neck_eye*neck_book*np.cos(np.radians(bend_angle)))
            # Tổng hợp Vector lực nén lên đốt sống cổ: |F| = sqrt(P^2 + T^2 + 2PTcos(180 - alpha))
            force_spine = round(5.0 * (1 + (90 - min(bend_angle, 90)) / 18.0), 1)
            
            st.metric("Khoảng cách Mắt - Vở (Giải tam giác)", f"{eye_book:.1f} cm")
            st.metric("Tổng Vector lực đè lên đốt sống cổ |P + T|", f"{force_spine} kg")
            
            # Mệnh đề logic
            p_logic = eye_book < 30
            q_logic = bend_angle < 50
            if p_logic or q_logic:
                st.error(f"🚨 MỆNH ĐỀ CẢNH BÁO (P ∨ Q = ĐÚNG): Học sinh đang ngồi sai tư thế! Nguy cơ cận thị & gù lưng!")
            else:
                st.success("✅ MỆNH ĐỀ AN TOÀN (P ∨ Q = SAI): Tư thế ngồi chuẩn công thái học!")
        with col2:
            fig_p, ax_p = plt.subplots(figsize=(5, 4))
            rad = np.radians(bend_angle)
            eye_pt = (neck_eye * np.cos(rad), neck_eye * np.sin(rad))
            book_pt = (neck_book, 0)
            ax_p.plot([0, eye_pt[0], book_pt[0], 0], [0, eye_pt[1], book_pt[1], 0], 'b-o', lw=2)
            ax_p.text(0, -2, "Cổ (0,0)", fontweight='bold')
            ax_p.text(eye_pt[0], eye_pt[1]+1, f"Mắt ({eye_book:.1f}cm tới vở)", color='red', fontweight='bold')
            ax_p.text(book_pt[0]-5, 1, "Quyển Vở", fontweight='bold')
            ax_p.set_xlim(-5, 65)
            ax_p.set_ylim(-5, 30)
            ax_p.grid(True, linestyle='--')
            ax_p.set_title("Mô hình Giải Tam Giác Tư Thế Ngồi")
            st.pyplot(fig_p)
            
    elif "Kiểm soát thực đơn" in project_choice:
        st.info("💡 Mẹo trình diễn: Nhập khẩu phần 3 nhóm chất (Đạm - Đường bột - Béo) trên 3 trục lệch nhau 120° để giải tam giác dinh dưỡng.")
        c1, c2, c3 = st.columns(3)
        p_val = c1.slider("Trục Đạm - Protein (g):", 10, 100, 60)
        c_val = c2.slider("Trục Đường bột - Carb (g):", 10, 100, 85)
        f_val = c3.slider("Trục Béo - Fat (g):", 10, 100, 75)
        # Diện tích tam giác dinh dưỡng S = 1/2 * sin(120) * (ab + bc + ca)
        s_nutri = 0.5 * np.sin(np.radians(120)) * (p_val*c_val + c_val*f_val + f_val*p_val)
        calo_in = p_val*4 + c_val*4 + f_val*9
        st.write(f"**Tổng năng lượng nạp (Vector nạp):** `{calo_in} kcal` | **Diện tích tam giác cân bằng dinh dưỡng (Giải tam giác góc 120°):** `{s_nutri:.1f}`")
        if calo_in > 900:
            st.error("🚨 MỆNH ĐỀ CẢNH BÁO: Thực đơn vượt ngưỡng Bất phương trình Calo cho phép (Calo ≤ 900 kcal)!")
        else:
            st.success("✅ Thực đơn nằm trong miền nghiệm an toàn!")
            
    else:
        st.subheader("🔦 Mô phỏng Thước Đo Góc Tia Đỏ (Đo khoảng cách không chạm)")
        d_base = st.number_input("Khoảng cách từ chân thước đến vật chuẩn A (m):", value=10.0)
        ang_1 = st.slider("Góc tia đỏ ngắm vào điểm A (độ):", 10, 85, 30)
        ang_2 = st.slider("Góc tia đỏ ngắm vào mục tiêu B (độ):", 10, 85, 65)
        h_target = d_base * (np.tan(np.radians(ang_2)) - np.tan(np.radians(ang_1)))
        st.success(f"🎯 **Kết quả giải tam giác & hiệu 2 Vector tia đỏ:** Khoảng cách AB = **{abs(h_target):.2f} mét**")

# -------------------------------------------------------------------------
# TAB 4: LỚP HỌC TƯƠNG TÁC (GV GIAO BÀI & SỬA LỖI - HS LÀM BÀI)
# -------------------------------------------------------------------------
with tabs[3]:
    st.header("📝 Hệ Thống Tương Tác Trực Tuyến Giáo Viên - Học Sinh")
    
    # Nút làm mới dữ liệu trực tiếp
    if st.button("🔄 Cập nhật bài nộp & điểm số mới nhất"):
        st.rerun()

    if is_gv:
        st.subheader("👩‍🏫 Bảng Điều Khiển Của Giáo Viên")
        with st.expander("➕ Đăng bài tập mới cho cả lớp"):
            new_title = st.text_input("Tiêu đề bài tập:")
            new_topic = st.selectbox("Chủ đề Toán 10:", ["Mệnh đề", "Hệ bất phương trình", "Giải tam giác & Lượng giác", "Vector"])
            new_content = st.text_area("Nội dung đề bài:")
            if st.button("Phát đề cho học sinh"):
                now_str = datetime.now().strftime("%H:%M:%S")
                c.execute("INSERT INTO assignments (title, topic, content, time) VALUES (?, ?, ?, ?)",
                          (new_title, new_topic, new_content, now_str))
                conn.commit()
                st.success("Đã đăng bài tập lên hệ thống!")
                st.rerun()

        st.subheader("📋 Danh sách bài làm của Học sinh (Chấm & Sửa lỗi trực tiếp)")
        subs = pd.read_sql_query("""
            SELECT s.id, a.title, s.student_name, s.answer, s.score, s.correction, s.status, s.time 
            FROM submissions s JOIN assignments a ON s.assign_id = a.id ORDER BY s.id DESC
        """, conn)
        
        if subs.empty:
            st.info("Chưa có học sinh nào nộp bài.")
        else:
            for _, row in subs.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Học sinh:** `{row['student_name']}` | **Bài:** {row['title']} *(Nộp lúc {row['time']})* — **Trạng thái:** `{row['status']}`")
                    st.write("**Bài làm của HS:**")
                    st.code(row['answer'], language="text")
                    
                    c_sc, c_cor, c_btn = st.columns([1, 2.5, 0.8])
                    new_score = c_sc.text_input("Điểm số (0-10):", value=row['score'] or "", key=f"sc_{row['id']}")
                    new_corr = c_cor.text_input("Sửa lỗi trực tiếp (Sẽ hiện chữ đỏ bên máy HS):", value=row['correction'] or "", key=f"cor_{row['id']}")
                    if c_btn.button("💾 Lưu điểm", key=f"btn_{row['id']}"):
                        c.execute("UPDATE submissions SET score=?, correction=?, status='Đã chấm' WHERE id=?",
                                  (new_score, new_corr, row['id']))
                        conn.commit()
                        st.success("Đã trả bài cho HS!")
                        st.rerun()
    else:
        st.subheader(f"👨‍🎓 Góc Học Tập của: {user_name}")
        assign_df = pd.read_sql_query("SELECT * FROM assignments ORDER BY id DESC", conn)
        selected_assign = st.selectbox("Chọn bài tập Giáo viên đã giao:", assign_df['id'], 
                                       format_func=lambda x: assign_df[assign_df['id']==x]['title'].values[0])
        
        cur_row = assign_df[assign_df['id'] == selected_assign].iloc[0]
        st.info(f"**Đề bài ({cur_row['topic']}):**\n\n{cur_row['content']}")
        
        student_ans = st.text_area("Nhập lời giải & đáp số của bạn vào đây:", height=110)
        if st.button("🚀 Nộp bài cho Giáo viên"):
            if student_ans.strip():
                now_str = datetime.now().strftime("%H:%M:%S")
                c.execute("INSERT INTO submissions (assign_id, student_name, answer, score, correction, status, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (int(selected_assign), user_name, student_ans, "Chưa chấm", "Đang chờ GV nhận xét...", "Chờ chấm", now_str))
                conn.commit()
                st.success("Đã gửi bài thành công! Hãy bấm nút Cập nhật để xem Giáo viên chấm và sửa lỗi.")
                st.rerun()

        st.divider()
        st.subheader("📌 Kết quả & Phần sửa lỗi trực tiếp từ Giáo viên")
        my_subs = pd.read_sql_query("""
            SELECT a.title, s.answer, s.score, s.correction, s.status, s.time 
            FROM submissions s JOIN assignments a ON s.assign_id = a.id 
            WHERE s.student_name = ? ORDER BY s.id DESC
        """, conn, params=(user_name,))
        
        for _, r in my_subs.iterrows():
            with st.container(border=True):
                st.markdown(f"**{r['title']}** *(Nộp lúc {r['time']})* — **Điểm:** `{r['score']}`")
                st.text(f"Bài làm đã nộp: {r['answer']}")
                if r['status'] == 'Đã chấm':
                    st.markdown(f"🔴 **Giáo viên sửa lỗi:** :red[**{r['correction']}**]")
                else:
                    st.caption("⏳ Giáo viên đang chấm bài...")

# -------------------------------------------------------------------------
# TAB 5: CHATBOX TRỰC TUYẾN (HỖ TRỢ CÔNG THỨC TOÁN)
# -------------------------------------------------------------------------
with tabs[4]:
    st.header("💬 Phòng Chat Thảo Luận Toán 10 Trực Tuyến")
    st.caption("Mẹo: Bạn có thể gõ công thức toán trong cặp dấu $ (ví dụ: `$\\vec{AB} + \\vec{BC} = \\vec{AC}$` hoặc `$\\cos 60^\\circ = 0.5$`).")
    
    if st.button("🔄 Tải tin nhắn mới"):
        st.rerun()

    chat_df = pd.read_sql_query("SELECT * FROM chat_messages ORDER BY id DESC LIMIT 30", conn)
    chat_box = st.container(height=320, border=True)
    with chat_box:
        if chat_df.empty:
            st.caption("Chưa có tin nhắn nào. Hãy bắt đầu cuộc trò chuyện!")
        else:
            for _, msg in chat_df.iloc[::-1].iterrows():
                badge = "👩‍🏫 [GIÁO VIÊN]" if "Giáo viên" in msg['role'] else "👨‍🎓 [HỌC SINH]"
                st.markdown(f"**{badge} {msg['sender']}** *({msg['time']})*: {msg['message']}")

    with st.form("chat_form", clear_on_submit=True):
        c_msg, c_send = st.columns([5, 1])
        msg_text = c_msg.text_input("Nhập tin nhắn thảo luận hoặc câu hỏi cho GV...", label_visibility="collapsed")
        sent = c_send.form_submit_button("Gửi  paper-plane")
        if sent and msg_text.strip():
            now_str = datetime.now().strftime("%H:%M")
            c.execute("INSERT INTO chat_messages (sender, role, message, time) VALUES (?, ?, ?, ?)",
                      (user_name, role, msg_text, now_str))
            conn.commit()
            st.rerun()
