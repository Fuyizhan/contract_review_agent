import re

def regex_clause_extraction(raw_text: str) -> list[dict]:
    """
    降级方案：完全不依赖大模型，用状态机正则切分条款。
    只认“第X条”作为主边界，子条款（1.、2.）作为正文保留。
    """
    # 只匹配“第X条”，且后面必须跟着空格或中文字符，避免误伤正文
    pattern = r"(第[一二三四五六七八九十百\d]+条)"
    
    # finditer 会找出所有“第X条”出现的位置
    matches = list(re.finditer(pattern, raw_text))
    
    clauses = []
    if not matches:
        # 如果连“第X条”都没有，说明可能是杂乱的聊天记录，整篇算作一块
        if raw_text.strip():
            clauses.append({
                "title": "全文",
                "content": raw_text.strip(),
                "category": "other"
            })
        return clauses

    # 1. 处理第一个“第X条”之前的内容（通常是合同前言、甲乙方信息）
    preface_text = raw_text[:matches[0].start()].strip()
    if preface_text:
        clauses.append({
            "title": "合同前言",
            "content": preface_text,
            "category": "other"
        })

    # 2. 遍历找到的每一个“第X条”
    for i in range(len(matches)):
        # 当前匹配到的标题（例如：“第一条”）
        title = matches[i].group(1).strip()
        
        # 内容的起点：当前标题结束的位置
        content_start = matches[i].end()
        
        # 内容的终点：下一个标题开始的位置；如果是最后一个，就到文本末尾
        if i + 1 < len(matches):
            content_end = matches[i+1].start()
        else:
            content_end = len(raw_text)
            
        content = raw_text[content_start:content_end].strip()
        
        # 过滤掉标题后面可能紧跟的冒号或空格（例如：第一条 合同期限 -> 合同期限）
        # 这一步是为了让 title 更干净
        if content:
            clauses.append({
                "title": title,
                "content": content,
                "category": "other" # 规则降级无法判断类别，默认 other
            })
            
    return clauses

# 给风险识别用的兜底规则（用简单的关键词扫描）
def scan_rules_fallback(clauses: list[dict]) -> list[dict]:
    fallback_risks = []
    for clause in clauses:
        content = clause.get("content", "")
        # 如果包含“违约金”、“罚款”等字眼，且没说具体比例，就是风险
        if any(kw in content for kw in ["违约金", "罚款", "赔偿"]) and "%" in content:
            fallback_risks.append({
                "risk_level": "high",
                "description": f"[规则兜底] 条款中涉及违约金比例，请人工复核金额是否合理（原文: {content[:15]}...）"
            })
        # 如果包含“放弃”、“不承担”，也是高风险
        if any(kw in content for kw in ["放弃", "不承担", "单方面"]):
            fallback_risks.append({
                "risk_level": "high",
                "description": f"[规则兜底] 疑似霸王条款，单方面免除责任（原文: {content[:15]}...）"
            })
    return fallback_risks

#  给合规检查用的兜底规则
def scan_compliance_fallback(raw_text: str) -> tuple[list[str], list[str]]:
    missing = []
    issues = []
    # 简单的查漏补缺
    if "争议解决" not in raw_text and "法院" not in raw_text and "仲裁" not in raw_text:
        missing.append("争议解决方式")
    if "保密" not in raw_text:
        missing.append("保密条款")
    if "解除" not in raw_text and "终止" not in raw_text:
        missing.append("合同解除与终止条款")
        
    return missing, issues

# 3. 给建议生成用的兜底字典
def generate_suggestions_fallback(risks: list[dict]) -> list[dict]:
    suggestions = []
    for r in risks:
        desc = r.get("description", "")
        if "违约金" in desc:
            suggestions.append({
                "target": "违约金条款",
                "issue": "违约金比例可能畸高",
                "suggestion": "建议修改违约金比例，不超过合同总额的 20%。",
                "priority": "high"
            })
        elif "免责" in desc or "放弃" in desc:
            suggestions.append({
                "target": "责任条款",
                "issue": "存在单方面免责的霸王条款",
                "suggestion": "建议删除单方面免责表述，按公平原则分担责任。",
                "priority": "high"
            })
        else:
            suggestions.append({
                "target": "需复核条款",
                "issue": desc,
                "suggestion": "建议由法务人员人工复核该条款。",
                "priority": "medium"
            })
    return suggestions