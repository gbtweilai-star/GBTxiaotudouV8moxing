#!/usr/bin/env python3
"""
File Operator - 文件操作能力
为五维合一系统提供安全的文件操作功能
"""
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class OperationType(Enum):
    """文件操作类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    SEARCH = "search"
    LIST_DIR = "list_dir"

@dataclass
class FileAction:
    """文件操作记录"""
    operation: str
    path: str
    timestamp: float
    success: bool
    details: Optional[str] = None

class FileOperator:
    """文件操作能力
    
    提供读、写、删除、移动、复制、搜索等文件操作
    删除操作采用"回收站式"安全设计，默认标记删除而非真实删除
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.history: List[FileAction] = []
        self._trash_bin: Dict[str, Dict] = {}  # 回收站：path -> {original_content, timestamp}
        
    def read_file(self, path: str) -> Dict:
        """读取文件内容
        
        Args:
            path: 文件路径（相对或绝对）
            
        Returns:
            Dict: 包含文件内容或错误信息的字典
        """
        file_path = self._resolve_path(path)
        
        try:
            if not file_path.exists():
                return {
                    "status": "error",
                    "operation": "read",
                    "path": str(path),
                    "message": f"文件不存在：{file_path}"
                }
            
            content = file_path.read_text(encoding='utf-8')
            action = FileAction(
                operation=OperationType.READ.value,
                path=str(path),
                timestamp=time.time(),
                success=True,
                details=f"读取 {len(content)} 字节"
            )
            self.history.append(action)
            
            return {
                "status": "success",
                "operation": "read",
                "path": str(path),
                "content": content,
                "size": len(content),
                "message": f"成功读取文件"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "operation": "read",
                "path": str(path),
                "message": f"读取失败：{str(e)}"
            }
    
    def write_file(self, path: str, content: str) -> Dict:
        """写入文件内容
        
        Args:
            path: 文件路径
            content: 要写入的内容
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        file_path = self._resolve_path(path)
        
        try:
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件已存在，备份到回收站
            if file_path.exists():
                self._backup_to_trash(str(path))
            
            file_path.write_text(content, encoding='utf-8')
            action = FileAction(
                operation=OperationType.WRITE.value,
                path=str(path),
                timestamp=time.time(),
                success=True,
                details=f"写入 {len(content)} 字节"
            )
            self.history.append(action)
            
            return {
                "status": "success",
                "operation": "write",
                "path": str(path),
                "size": len(content),
                "message": f"成功写入文件"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "operation": "write",
                "path": str(path),
                "message": f"写入失败：{str(e)}"
            }
    
    def list_dir(self, path: str = ".") -> Dict:
        """列出目录内容
        
        Args:
            path: 目录路径（默认为当前目录）
            
        Returns:
            Dict: 包含目录内容列表的字典
        """
        dir_path = self._resolve_path(path)
        
        try:
            if not dir_path.exists():
                return {
                    "status": "error",
                    "operation": "list_dir",
                    "path": str(path),
                    "message": f"目录不存在：{dir_path}"
                }
            
            if not dir_path.is_dir():
                return {
                    "status": "error",
                    "operation": "list_dir",
                    "path": str(path),
                    "message": f"不是目录：{dir_path}"
                }
            
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_file": item.is_file(),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            action = FileAction(
                operation=OperationType.LIST_DIR.value,
                path=str(path),
                timestamp=time.time(),
                success=True,
                details=f"列出 {len(items)} 个项目"
            )
            self.history.append(action)
            
            return {
                "status": "success",
                "operation": "list_dir",
                "path": str(path),
                "items": items,
                "count": len(items),
                "message": f"成功列出目录内容"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "operation": "list_dir",
                "path": str(path),
                "message": f"列出目录失败：{str(e)}"
            }
    
    def search_files(self, pattern: str) -> Dict:
        """搜索文件
        
        Args:
            pattern: 搜索模式（支持通配符，如 '*.py'）
            
        Returns:
            Dict: 包含搜索结果列表的字典
        """
        try:
            results = list(self.base_path.rglob(pattern))
            
            files = []
            for f in results:
                if f.is_file():
                    files.append({
                        "path": str(f),
                        "name": f.name,
                        "size": f.stat().st_size,
                        "relative_path": str(f.relative_to(self.base_path))
                    })
            
            action = FileAction(
                operation=OperationType.SEARCH.value,
                path=str(pattern),
                timestamp=time.time(),
                success=True,
                details=f"找到 {len(files)} 个文件"
            )
            self.history.append(action)
            
            return {
                "status": "success",
                "operation": "search",
                "pattern": pattern,
                "files": files,
                "count": len(files),
                "message": f"找到 {len(files)} 个匹配文件"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "operation": "search",
                "pattern": pattern,
                "message": f"搜索失败：{str(e)}"
            }
    
    def safe_delete(self, path: str, confirm: bool = False) -> Dict:
        """安全删除文件（回收站式）
        
        默认情况下，删除操作会将文件备份到内存中的回收站，
        而非真正删除。设置 confirm=True 可真正删除文件。
        
        Args:
            path: 文件路径
            confirm: 是否真正删除（默认 False，标记删除）
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        file_path = self._resolve_path(path)
        
        try:
            if not file_path.exists():
                return {
                    "status": "error",
                    "operation": "delete",
                    "path": str(path),
                    "message": f"文件不存在：{file_path}"
                }
            
            if not file_path.is_file():
                return {
                    "status": "error",
                    "operation": "delete",
                    "path": str(path),
                    "message": f"不是文件：{file_path}"
                }
            
            if not confirm:
                # 标记删除：备份到回收站
                self._backup_to_trash(str(path))
                # 标记文件为已删除（在文件名后加 .deleted 标记）
                deleted_path = file_path.with_suffix(file_path.suffix + ".deleted")
                file_path.rename(deleted_path)
                
                action = FileAction(
                    operation=OperationType.DELETE.value,
                    path=str(path),
                    timestamp=time.time(),
                    success=True,
                    details="标记删除（可恢复）"
                )
                self.history.append(action)
                
                return {
                    "status": "success",
                    "operation": "delete",
                    "path": str(path),
                    "deleted": False,
                    "in_trash": True,
                    "message": f"文件已标记删除（备份到回收站）"
                }
            else:
                # 真正删除
                content = file_path.read_text(encoding='utf-8')
                file_path.unlink()
                
                action = FileAction(
                    operation=OperationType.DELETE.value,
                    path=str(path),
                    timestamp=time.time(),
                    success=True,
                    details="真正删除（不可恢复）"
                )
                self.history.append(action)
                
                return {
                    "status": "success",
                    "operation": "delete",
                    "path": str(path),
                    "deleted": True,
                    "in_trash": False,
                    "message": f"文件已真正删除"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "operation": "delete",
                "path": str(path),
                "message": f"删除失败：{str(e)}"
            }
    
    def copy_file(self, source: str, destination: str) -> Dict:
        """复制文件
        
        Args:
            source: 源文件路径
            destination: 目标路径
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        src_path = self._resolve_path(source)
        dst_path = self._resolve_path(destination)
        
        try:
            if not src_path.exists():
                return {
                    "status": "error",
                    "operation": "copy",
                    "source": str(source),
                    "destination": str(destination),
                    "message": f"源文件不存在：{src_path}"
                }
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            
            action = FileAction(
                operation=OperationType.COPY.value,
                path=f"{source} -> {destination}",
                timestamp=time.time(),
                success=True,
                details="文件复制完成"
            )
            self.history.append(action)
            
            return {
                "status": "success",
                "operation": "copy",
                "source": str(source),
                "destination": str(destination),
                "message": f"文件复制成功"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "operation": "copy",
                "source": str(source),
                "destination": str(destination),
                "message": f"复制失败：{str(e)}"
            }
    
    def move_file(self, source: str, destination: str) -> Dict:
        """移动文件
        
        Args:
            source: 源文件路径
            destination: 目标路径
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        src_path = self._resolve_path(source)
        dst_path = self._resolve_path(destination)
        
        try:
            if not src_path.exists():
                return {
                    "status": "error",
                    "operation": "move",
                    "source": str(source),
                    "destination": str(destination),
                    "message": f"源文件不存在：{src_path}"
                }
            
            # 备份原文件
            self._backup_to_trash(str(source))
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            
            action = FileAction(
                operation=OperationType.MOVE.value,
                path=f"{source} -> {destination}",
                timestamp=time.time(),
                success=True,
                details="文件移动完成"
            )
            self.history.append(action)
            
            return {
                "status": "success",
                "operation": "move",
                "source": str(source),
                "destination": str(destination),
                "message": f"文件移动成功"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "operation": "move",
                "source": str(source),
                "destination": str(destination),
                "message": f"移动失败：{str(e)}"
            }
    
    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.base_path / p
    
    def _backup_to_trash(self, path: str) -> None:
        """备份文件到回收站"""
        file_path = self._resolve_path(path)
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8')
                self._trash_bin[str(path)] = {
                    "content": content,
                    "timestamp": time.time(),
                    "original_path": str(file_path)
                }
            except:
                pass
    
    def get_history(self) -> List[Dict]:
        """获取操作历史
        
        Returns:
            List[Dict]: 操作历史列表
        """
        return [
            {
                "operation": a.operation,
                "path": a.path,
                "timestamp": a.timestamp,
                "success": a.success,
                "details": a.details
            }
            for a in self.history
        ]
    
    def get_trash_bin(self) -> Dict:
        """获取回收站内容
        
        Returns:
            Dict: 回收站中的文件列表
        """
        return {
            "status": "success",
            "operation": "get_trash",
            "files": list(self._trash_bin.keys()),
            "count": len(self._trash_bin),
            "message": f"回收站中有 {len(self._trash_bin)} 个文件"
        }

if __name__ == '__main__':
    print("=" * 50)
    print("File Operator 自测")
    print("=" * 50)
    
    operator = FileOperator()
    
    # 测试写文件
    result = operator.write_file("test_file.txt", "Hello, File Operator!")
    print(f"\n[写文件] {result['status']}: {result['message']}")
    
    # 测试读文件
    result = operator.read_file("test_file.txt")
    print(f"[读文件] {result['status']}: {result.get('content', '')}")
    
    # 测试列目录
    result = operator.list_dir(".")
    print(f"[列目录] {result['status']}: 找到 {result.get('count', 0)} 个项目")
    
    # 测试搜索文件
    result = operator.search_files("*.py")
    print(f"[搜索文件] {result['status']}: 找到 {result.get('count', 0)} 个 Python 文件")
    
    # 测试安全删除（标记删除）
    result = operator.safe_delete("test_file.txt", confirm=False)
    print(f"[安全删除] {result['status']}: {result['message']}")
    
    # 测试回收站
    result = operator.get_trash_bin()
    print(f"[回收站] {result['status']}: {result['message']}")
    
    # 获取历史
    history = operator.get_history()
    print(f"\n[操作历史] 共 {len(history)} 条记录")
    
    print("\n" + "=" * 50)
    print("自测完成")
    print("=" * 50)
