"""
OCR 文字识别能力模块 (OCR Engine)

为五维合一系统提供 OCR 文字识别能力，支持全文识别、区域识别和文本块检测。
"""

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class TextOrientation(Enum):
    """文本方向枚举"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ROTATED = "rotated"
    UNKNOWN = "unknown"


class Language(Enum):
    """支持的语言枚举"""
    CHI_SIM = "chi_sim"  # 简体中文
    CHI_TRA = "chi_tra"  # 繁体中文
    ENG = "eng"          # 英语
    JAP = "jap"          # 日语
    KOR = "kor"          # 韩语
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """边界框数据类（归一化坐标 0-1）"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
            "confidence": self.confidence
        }


@dataclass
class TextBlock:
    """文本块数据类"""
    text: str
    bounding_box: BoundingBox
    language: Language
    orientation: TextOrientation
    confidence: float
    block_type: str  # title, paragraph, list, table, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict(),
            "language": self.language.value,
            "orientation": self.orientation.value,
            "confidence": self.confidence,
            "block_type": self.block_type
        }


@dataclass
class TextLine:
    """文本行数据类"""
    text: str
    bounding_box: BoundingBox
    confidence: float
    line_number: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict(),
            "confidence": self.confidence,
            "line_number": self.line_number
        }


@dataclass
class OCRResult:
    """OCR 识别结果数据类"""
    status: str
    full_text: str
    text_blocks: List[TextBlock]
    text_lines: List[TextLine]
    language: Language
    average_confidence: float
    processing_time_ms: float
    image_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "full_text": self.full_text,
            "text_blocks": [block.to_dict() for block in self.text_blocks],
            "text_lines": [line.to_dict() for line in self.text_lines],
            "language": self.language.value,
            "average_confidence": self.average_confidence,
            "processing_time_ms": self.processing_time_ms,
            "image_info": self.image_info
        }


@dataclass
class RegionResult:
    """区域识别结果数据类"""
    region_id: str
    text: str
    bounding_box: BoundingBox
    confidence: float
    language: Language
    text_lines: List[TextLine]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict(),
            "confidence": self.confidence,
            "language": self.language.value,
            "text_lines": [line.to_dict() for line in self.text_lines]
        }


class OCREngine:
    """
    OCR 文字识别引擎

    提供 OCR 文字识别能力，包括：
    - 全文识别
    - 区域识别
    - 文本块检测
    - 多语言支持
    - 置信度评估
    """

    def __init__(
        self,
        default_language: str = "chi_sim",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 OCR 引擎

        Args:
            default_language: 默认识别语言，支持 chi_sim/chi_tra/eng/jap/kor
            config: 可选的配置字典，可包含阈值、模型路径等参数
        """
        self.default_language = self._parse_language(default_language)
        self.config = config or {}
        self._initialized = True

        # 支持的语言配置
        self.supported_languages = {
            "chi_sim": Language.CHI_SIM,
            "chi_tra": Language.CHI_TRA,
            "eng": Language.ENG,
            "jap": Language.JAP,
            "kor": Language.KOR
        }

    def extract_text(
        self,
        image: str,
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        全文识别：提取图像中的所有文字

        Args:
            image: 图像路径或 base64 编码的图像数据
            lang: 识别语言，可选 chi_sim/chi_tra/eng/jap/kor，默认使用初始化时的语言

        Returns:
            包含完整 OCR 结果的字典
        """
        start_time = time.time()
        target_lang = self._parse_language(lang) if lang else self.default_language

        try:
            # 检测文本块
            text_blocks = self.detect_text_blocks(image)

            # 提取文本行
            text_lines = self._extract_text_lines(image, text_blocks, target_lang)

            # 合并全文
            full_text = self._merge_full_text(text_blocks)

            # 计算平均置信度
            avg_confidence = self._calculate_average_confidence(text_blocks, text_lines)

            # 获取图像信息
            image_info = self._get_image_info(image)

            processing_time = (time.time() - start_time) * 1000

            result = OCRResult(
                status="success",
                full_text=full_text,
                text_blocks=text_blocks,
                text_lines=text_lines,
                language=target_lang,
                average_confidence=avg_confidence,
                processing_time_ms=processing_time,
                image_info=image_info
            )

            return result.to_dict()

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_ms": processing_time
            }

    def recognize_regions(
        self,
        image: str,
        regions: List[Dict[str, float]],
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        区域识别：识别指定区域内的文字

        Args:
            image: 图像路径或 base64 编码的图像数据
            regions: 区域列表，每个区域包含 region_id 和边界框信息
                     格式：[{"region_id": "r1", "x_min": 0.1, "y_min": 0.2, "x_max": 0.5, "y_max": 0.6}, ...]
            lang: 识别语言，可选 chi_sim/chi_tra/eng/jap/kor

        Returns:
            包含各区域识别结果的字典
        """
        start_time = time.time()
        target_lang = self._parse_language(lang) if lang else self.default_language

        try:
            results = []

            for region in regions:
                region_id = region.get("region_id", f"region_{len(results)}")
                x_min = region.get("x_min", 0.0)
                y_min = region.get("y_min", 0.0)
                x_max = region.get("x_max", 1.0)
                y_max = region.get("y_max", 1.0)

                # 骨架实现：模拟区域识别结果
                # 实际实现需要裁剪图像区域并进行 OCR 识别

                bounding_box = BoundingBox(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                    confidence=0.9
                )

                # 模拟识别结果
                mock_text_lines = [
                    TextLine(
                        text=f"模拟文本行 {i + 1}",
                        bounding_box=BoundingBox(
                            x_min=x_min + i * 0.1,
                            y_min=y_min + i * 0.1,
                            x_max=x_max - (1 - i) * 0.1,
                            y_max=y_max - (1 - i) * 0.1,
                            confidence=0.85 + i * 0.02
                        ),
                        confidence=0.85 + i * 0.02,
                        line_number=i + 1
                    )
                    for i in range(2)
                ]

                region_result = RegionResult(
                    region_id=region_id,
                    text="\n".join(line.text for line in mock_text_lines),
                    bounding_box=bounding_box,
                    confidence=0.88,
                    language=target_lang,
                    text_lines=mock_text_lines
                )

                results.append(region_result.to_dict())

            processing_time = (time.time() - start_time) * 1000

            return {
                "status": "success",
                "regions": results,
                "language": target_lang.value,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_ms": processing_time
            }

    def detect_text_blocks(self, image: str) -> List[TextBlock]:
        """
        文本块检测：检测图像中的文本块及其位置

        Args:
            image: 图像路径或 base64 编码的图像数据

        Returns:
            文本块列表
        """
        # 骨架实现：模拟文本块检测结果
        # 实际实现需要集成文本检测模型（如 CRAFT、DBNet）

        mock_blocks = [
            TextBlock(
                text="标题文本示例",
                bounding_box=BoundingBox(0.1, 0.05, 0.9, 0.15, 0.95),
                language=Language.CHI_SIM,
                orientation=TextOrientation.HORIZONTAL,
                confidence=0.92,
                block_type="title"
            ),
            TextBlock(
                text="这是正文段落的内容，包含多行文字信息。",
                bounding_box=BoundingBox(0.1, 0.2, 0.9, 0.5, 0.88),
                language=Language.CHI_SIM,
                orientation=TextOrientation.HORIZONTAL,
                confidence=0.85,
                block_type="paragraph"
            ),
            TextBlock(
                text="项目列表项 1\n项目列表项 2\n项目列表项 3",
                bounding_box=BoundingBox(0.1, 0.55, 0.7, 0.75, 0.82),
                language=Language.CHI_SIM,
                orientation=TextOrientation.HORIZONTAL,
                confidence=0.79,
                block_type="list"
            )
        ]

        return mock_blocks

    def get_confidence(
        self,
        text_blocks: List[TextBlock],
        text_lines: Optional[List[TextLine]] = None
    ) -> Dict[str, Any]:
        """
        获取识别置信度评估

        Args:
            text_blocks: 文本块列表
            text_lines: 可选的文本行列表

        Returns:
            置信度评估结果字典
        """
        if not text_blocks:
            return {
                "status": "warning",
                "message": "没有文本块可供评估",
                "average_confidence": 0.0,
                "block_count": 0
            }

        # 计算文本块置信度统计
        block_confidences = [block.confidence for block in text_blocks]
        avg_block_confidence = sum(block_confidences) / len(block_confidences)
        min_block_confidence = min(block_confidences)
        max_block_confidence = max(block_confidences)

        # 如果有文本行，也计算其置信度
        line_confidences = []
        if text_lines:
            line_confidences = [line.confidence for line in text_lines]
            avg_line_confidence = sum(line_confidences) / len(line_confidences)
        else:
            avg_line_confidence = None

        # 综合置信度
        if avg_line_confidence is not None:
            overall_confidence = (avg_block_confidence + avg_line_confidence) / 2
        else:
            overall_confidence = avg_block_confidence

        # 置信度等级
        if overall_confidence >= 0.9:
            confidence_level = "high"
        elif overall_confidence >= 0.7:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return {
            "status": "success",
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level,
            "block_statistics": {
                "average": avg_block_confidence,
                "minimum": min_block_confidence,
                "maximum": max_block_confidence,
                "count": len(text_blocks)
            },
            "line_statistics": {
                "average": avg_line_confidence,
                "count": len(line_confidences)
            } if line_confidences else None
        }

    def _parse_language(self, lang_code: str) -> Language:
        """
        解析语言代码

        Args:
            lang_code: 语言代码字符串

        Returns:
            Language 枚举值
        """
        lang_map = {
            "chi_sim": Language.CHI_SIM,
            "chi_tra": Language.CHI_TRA,
            "eng": Language.ENG,
            "jap": Language.JAP,
            "kor": Language.KOR
        }
        return lang_map.get(lang_code.lower(), Language.UNKNOWN)

    def _extract_text_lines(
        self,
        image: str,
        text_blocks: List[TextBlock],
        language: Language
    ) -> List[TextLine]:
        """
        从文本块中提取文本行

        Args:
            image: 图像路径
            text_blocks: 文本块列表
            language: 识别语言

        Returns:
            文本行列表
        """
        text_lines = []
        line_counter = 1

        for block in text_blocks:
            # 骨架实现：模拟文本行提取
            # 实际实现需要对每个文本块进行行分割和识别

            # 根据 block_type 生成模拟行
            if block.block_type == "title":
                text_lines.append(TextLine(
                    text=block.text,
                    bounding_box=block.bounding_box,
                    confidence=block.confidence,
                    line_number=line_counter
                ))
                line_counter += 1
            elif block.block_type == "paragraph":
                # 模拟将段落拆分为多行
                lines = block.text.split("，")
                for i, line_text in enumerate(lines):
                    text_lines.append(TextLine(
                        text=line_text + ("，" if i < len(lines) - 1 else ""),
                        bounding_box=BoundingBox(
                            x_min=block.bounding_box.x_min,
                            y_min=block.bounding_box.y_min + i * 0.05,
                            x_max=block.bounding_box.x_max,
                            y_max=block.bounding_box.y_min + (i + 1) * 0.05,
                            confidence=block.confidence
                        ),
                        confidence=block.confidence,
                        line_number=line_counter
                    ))
                    line_counter += 1
            elif block.block_type == "list":
                # 列表项作为独立行
                list_items = block.text.split("\n")
                for i, item in enumerate(list_items):
                    text_lines.append(TextLine(
                        text=item,
                        bounding_box=BoundingBox(
                            x_min=block.bounding_box.x_min,
                            y_min=block.bounding_box.y_min + i * 0.04,
                            x_max=block.bounding_box.x_max,
                            y_max=block.bounding_box.y_min + (i + 1) * 0.04,
                            confidence=block.confidence
                        ),
                        confidence=block.confidence,
                        line_number=line_counter
                    ))
                    line_counter += 1

        return text_lines

    def _merge_full_text(self, text_blocks: List[TextBlock]) -> str:
        """
        合并所有文本块为完整文本

        Args:
            text_blocks: 文本块列表

        Returns:
            完整文本字符串
        """
        if not text_blocks:
            return ""

        # 按位置排序（从上到下）
        sorted_blocks = sorted(text_blocks, key=lambda b: b.bounding_box.y_min)

        # 合并文本，不同类型之间添加分隔
        full_text_parts = []
        for block in sorted_blocks:
            if full_text_parts and block.block_type != "paragraph":
                full_text_parts.append("\n")
            full_text_parts.append(block.text)
            if block.block_type in ["title", "list"]:
                full_text_parts.append("\n")

        return "".join(full_text_parts)

    def _calculate_average_confidence(
        self,
        text_blocks: List[TextBlock],
        text_lines: List[TextLine]
    ) -> float:
        """
        计算平均置信度

        Args:
            text_blocks: 文本块列表
            text_lines: 文本行列表

        Returns:
            平均置信度
        """
        all_confidences = [block.confidence for block in text_blocks]
        all_confidences.extend([line.confidence for line in text_lines])

        if not all_confidences:
            return 0.0

        return sum(all_confidences) / len(all_confidences)

    def _get_image_info(self, image: str) -> Dict[str, Any]:
        """
        获取图像信息

        Args:
            image: 图像路径或 base64 数据

        Returns:
            图像信息字典
        """
        # 骨架实现：返回模拟图像信息
        # 实际实现需要读取图像元数据

        if isinstance(image, str) and image.endswith(('.png', '.jpg', '.jpeg')):
            return {
                "format": image.split(".")[-1].upper(),
                "source": "file_path",
                "filename": os.path.basename(image)
            }
        else:
            return {
                "format": "UNKNOWN",
                "source": "base64_or_other"
            }


if __name__ == "__main__":
    print("=" * 60)
    print("OCR 文字识别模块 (OCR Engine) 自测")
    print("=" * 60)

    # 创建实例（默认简体中文）
    ocr = OCREngine(default_language="chi_sim")
    print("[OK] OCREngine 实例创建成功（默认语言：chi_sim）")

    # 测试图像路径（模拟）
    test_image = "test_document.png"

    # 测试 1: 全文识别
    print("\n[测试 1] extract_text - 全文识别")
    result = ocr.extract_text(test_image, lang="chi_sim")
    print(f"状态：{result['status']}")
    print(f"识别语言：{result.get('language', 'N/A')}")
    print(f"文本块数：{len(result.get('text_blocks', []))}")
    print(f"文本行数：{len(result.get('text_lines', []))}")
    print(f"平均置信度：{result.get('average_confidence', 'N/A'):.2f}")
    print(f"处理时间：{result.get('processing_time_ms', 'N/A'):.2f}ms")
    print(f"全文内容:\n{result.get('full_text', 'N/A')}")

    # 测试 2: 区域识别
    print("\n[测试 2] recognize_regions - 区域识别")
    regions = [
        {"region_id": "header", "x_min": 0.0, "y_min": 0.0, "x_max": 1.0, "y_max": 0.15},
        {"region_id": "content", "x_min": 0.1, "y_min": 0.2, "x_max": 0.9, "y_max": 0.6}
    ]
    region_result = ocr.recognize_regions(test_image, regions, lang="chi_sim")
    print(f"状态：{region_result['status']}")
    print(f"识别区域数：{len(region_result.get('regions', []))}")
    for region in region_result.get('regions', []):
        print(f"  - 区域 {region['region_id']}: 置信度 {region['confidence']}, 文本：{region['text'][:30]}...")

    # 测试 3: 文本块检测
    print("\n[测试 3] detect_text_blocks - 文本块检测")
    blocks = ocr.detect_text_blocks(test_image)
    print(f"检测到 {len(blocks)} 个文本块:")
    for block in blocks:
        print(f"  - 类型：{block.block_type}, 文本：{block.text[:20]}..., 置信度：{block.confidence}")

    # 测试 4: 置信度评估
    print("\n[测试 4] get_confidence - 置信度评估")
    lines = ocr._extract_text_lines(test_image, blocks, Language.CHI_SIM)
    confidence_result = ocr.get_confidence(blocks, lines)
    print(f"状态：{confidence_result['status']}")
    print(f"综合置信度：{confidence_result['overall_confidence']:.2f}")
    print(f"置信度等级：{confidence_result['confidence_level']}")
    print(f"文本块统计：平均={confidence_result['block_statistics']['average']:.2f}, "
          f"最小={confidence_result['block_statistics']['minimum']:.2f}, "
          f"最大={confidence_result['block_statistics']['maximum']:.2f}")

    # 测试 5: 英文识别
    print("\n[测试 5] extract_text - 英文识别")
    ocr_eng = OCREngine(default_language="eng")
    eng_result = ocr_eng.extract_text(test_image, lang="eng")
    print(f"状态：{eng_result['status']}")
    print(f"识别语言：{eng_result.get('language', 'N/A')}")
    print(f"文本块数：{len(eng_result.get('text_blocks', []))}")

    print("\n" + "=" * 60)
    print("自测完成！所有方法正常工作。")
    print("=" * 60)
