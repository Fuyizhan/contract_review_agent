# src/services/report_service.py
from fpdf import FPDF

def generate_pdf_report(review_data: dict) -> bytes:
    """根据审查数据生成 PDF 报告，返回二进制流。"""
    
    # 1. 初始化 PDF（A4 尺寸，单位毫米）
    pdf = FPDF()
    pdf.add_page()
    
    # 2. 设置中文字体（非常重要！如果不设置，中文全是乱码方块）
    # Windows 系统自带微软雅黑，路径通常在 C:/Windows/Fonts/msyh.ttc 或 simhei.ttf
    try:
        pdf.add_font("msyh", "", "C:/Windows/Fonts/msyh.ttc")
        pdf.set_font("msyh", size=12)
    except Exception:
        # 如果找不到字体，降级用黑体，或者提醒
        try:
            pdf.add_font("simhei", "", "C:/Windows/Fonts/simhei.ttf")
            pdf.set_font("simhei", size=12)
        except Exception:
            raise RuntimeError("找不到中文字体，请确保 C:/Windows/Fonts/ 下有 msyh.ttc 或 simhei.ttf")

    # 3. 提取数据
    filename = review_data.get("original_filename", "未知合同")
    risks = review_data.get("risk_findings", [])
    missing = review_data.get("missing_clauses", [])
    issues = review_data.get("compliance_issues", [])
    suggestions = review_data.get("suggestions", [])

    # ================= 开始渲染内容 =================
    
    # 标题
    pdf.set_font_size(20)
    pdf.cell(0, 15, "合同智能审查报告", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # 基本信息
    pdf.set_font_size(12)
    pdf.cell(0, 10, f"合同名称：{filename}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # --- 风险发现 ---
    pdf.set_font_size(16)
    pdf.set_text_color(200, 0, 0) # 红色
    pdf.cell(0, 10, f"一、 风险发现 ({len(risks)}项)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0) # 黑色
    pdf.set_font_size(12)
    if not risks:
        pdf.cell(0, 8, "未发现明显风险。", new_x="LMARGIN", new_y="NEXT")
    else:
        for r in risks:
            level = r.get("risk_level", "low").upper()
            desc = r.get("description", "")
            # 使用 multi_cell 支持自动换行
            pdf.multi_cell(0, 8, f"[{level}] {desc}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # --- 合规检查 ---
    pdf.set_font_size(16)
    pdf.set_text_color(200, 100, 0) # 橙色
    pdf.cell(0, 10, "二、 合规检查与缺失条款", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(12)
    
    pdf.multi_cell(0, 8, f"缺失必备条款：{', '.join(missing) if missing else '无'}", new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 8, "合规问题：", new_x="LMARGIN", new_y="NEXT")
    if not issues:
        pdf.multi_cell(0, 8, "  未发现合规问题。", new_x="LMARGIN", new_y="NEXT")
    else:
        for i in issues:
            pdf.multi_cell(0, 8, f"  - {i}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # --- 修改建议 ---
    pdf.set_font_size(16)
    pdf.set_text_color(0, 100, 200) # 蓝色
    pdf.cell(0, 10, f"三、 修改建议 ({len(suggestions)}项)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(12)
    if not suggestions:
        pdf.cell(0, 8, "暂无修改建议。", new_x="LMARGIN", new_y="NEXT")
    else:
        for s in suggestions:
            pdf.multi_cell(0, 8, f"问题：{s.get('issue', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(0, 8, f"建议：{s.get('suggestion', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(0, 8, f"优先级：{s.get('priority', 'medium')}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    # 4. 输出为字节流 (bytes)
    return bytes(pdf.output())