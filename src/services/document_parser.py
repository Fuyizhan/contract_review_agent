import io
import PyPDF2
from docx import Document
from fastapi import HTTPException

class DocumentParserService:
    @staticmethod
    async def parse(file_bytes: bytes, filename: str) -> str:
        """根据文件类型解析文本，返回纯文本。"""
        if filename.endswith(".txt"):
            return file_bytes.decode("utf-8", errors="ignore")
            
        elif filename.endswith(".pdf"):
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                content = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
                if not content.strip():
                    raise ValueError("PDF 中未提取到文本，可能是扫描件（图片型 PDF）")
                return content
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"PDF 解析失败: {e}")
                
        elif filename.endswith(".docx"):
            try:
                doc = Document(io.BytesIO(file_bytes))
                content = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                if not content.strip():
                    raise ValueError("Word 文档内容为空")
                return content
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Word 解析失败: {e}")
                
        else:
            raise HTTPException(status_code=400, detail="仅支持 TXT, PDF, DOCX 格式")

# 实例化一个单例给路由用
document_parser = DocumentParserService()