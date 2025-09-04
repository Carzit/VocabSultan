#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词记忆程序 - 核心模块 (重构版本)
抽象化接口设计，支持多种UI实现
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Protocol, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import threading
import time
import operator

from utils import enum_asdict


class WordStatus(Enum):
    DRAFT = "draft"
    LEARNING = "learning" 
    REVIEWING = "reviewing"
    MASTERED = "mastered"


class DifficultyLevel(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    VERY_HARD = 4


class SortOrder(Enum):
    """排序方式"""
    ALPHABETICAL = "alphabetical"  # 按字母顺序
    ADDED_TIME = "added_time"      # 按添加时间
    REVIEW_TIME = "review_time"    # 按复习时间
    COMPLETENESS = "completeness"  # 按完整度
    STATUS = "status"              # 按状态
    REVIEW_COUNT = "review_count"  # 按复习次数


@dataclass
class Note:
    """笔记数据结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    
    def get_simplified_display(self, max_length: int = 50) -> str:
        """获取简化显示版本"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length-3] + "..."
    
    def get_full_display(self, include_metadata: bool = True) -> str:
        """获取完整显示版本"""
        if not include_metadata:
            return self.content
        
        created_time = datetime.fromisoformat(self.created_at)
        date_str = created_time.strftime("%Y-%m-%d %H:%M")
        result = f"[{date_str}] {self.content}"
        
        if self.tags:
            result += f" #{' #'.join(self.tags)}"
        
        return result


@dataclass
class CoreInfo:
    """核心单词信息"""
    pronunciation: str = ""
    primary_definition: str = ""
    part_of_speech: str = ""


@dataclass
class ExtendedInfo:
    """扩展单词信息"""
    definitions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    etymology: str = ""
    memory_tips: str = ""


@dataclass
class LearningData:
    """学习数据"""
    added_date: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "manual_input"
    context: str = ""
    last_reviewed: str = ""
    next_review: str = ""
    review_count: int = 0
    correct_count: int = 0
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM


@dataclass
class AddWordConfig:
    """添加单词时的配置"""
    skip_pronunciation: bool = False  # 跳过发音输入
    skip_part_of_speech: bool = False  # 跳过词性输入
    skip_context: bool = False  # 跳过语境输入
    skip_tags: bool = False  # 跳过标签输入
    auto_promote_to_learning: bool = True  # 有定义时自动提升为learning状态
    default_tags: List[str] = field(default_factory=list)  # 默认标签


@dataclass
class UIChoiceDefaults:
    """UI选择项的默认值配置"""
    # 主菜单默认选择
    main_menu_default: str = "1"
    
    # 复习时的默认表现评级
    review_performance_default: str = "g"  # good
    
    # 词汇表管理默认排序
    vocabulary_sort_default: str = "1"  # 按字母顺序
    
    # 批量操作默认选择
    batch_edit_default: str = "1"  # 添加标签
    batch_status_default: str = "2"  # 学习中
    batch_difficulty_default: str = "2"  # 中等
    
    # 笔记类型默认选择
    note_type_default: str = "5"  # 自定义
    
    # 确认操作默认值
    confirm_continue_review: bool = True
    confirm_add_note: bool = False
    confirm_batch_edit: bool = False
    confirm_delete: bool = False


@dataclass
class AppConfig:
    """应用配置"""
    # 自动保存设置
    auto_save: bool = True
    auto_save_interval: int = 300  # 秒
    
    # 数据文件设置
    data_file: str = "vocabulary.json"
    backup_enabled: bool = True
    backup_count: int = 5
    
    # 学习算法设置
    mastery_threshold: float = 0.8
    mastery_review_count: int = 3
    max_interval_days: int = 30
    
    # 显示设置
    note_simplified_length: int = 50
    search_result_limit: int = 20
    
    # 间隔重复设置
    sr_base_intervals: Dict[str, float] = field(default_factory=lambda: {
        "excellent": 7.0,
        "good": 3.0,
        "fair": 1.0,
        "poor": 0.5
    })
    
    # 添加单词配置
    add_word_config: AddWordConfig = field(default_factory=AddWordConfig)
    
    # UI选择默认值配置
    ui_defaults: UIChoiceDefaults = field(default_factory=UIChoiceDefaults)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 处理嵌套的枚举或特殊类型
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置"""
        # 处理嵌套配置的转换
        if 'add_word_config' in data and isinstance(data['add_word_config'], dict):
            data['add_word_config'] = AddWordConfig(**data['add_word_config'])
        
        if 'ui_defaults' in data and isinstance(data['ui_defaults'], dict):
            data['ui_defaults'] = UIChoiceDefaults(**data['ui_defaults'])
        
        return cls(**data)
    
    def save(self, config_file: str = "config.json"):
        """保存配置"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    @classmethod
    def load(cls, config_file: str = "config.json") -> 'AppConfig':
        """加载配置"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return cls.from_dict(data)
            except Exception as e:
                print(f"加载配置失败: {e}")
        return cls()  # 返回默认配置


@dataclass
class Word:
    """单词数据结构"""
    id: str
    word: str
    status: WordStatus = WordStatus.DRAFT
    completeness: float = 0.0
    tags: List[str] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    core_info: CoreInfo = field(default_factory=CoreInfo)
    extended_info: ExtendedInfo = field(default_factory=ExtendedInfo)
    learning_data: LearningData = field(default_factory=LearningData)
    
    def add_note(self, content: str, tags: List[str] = None) -> Note:
        """添加笔记"""
        note = Note(content=content, tags=tags or [])
        self.notes.append(note)
        return note
    
    def get_notes_display(self, simplified: bool = True, 
                         include_metadata: bool = False) -> List[str]:
        """获取笔记显示列表"""
        if not self.notes:
            return []
        
        if simplified:
            return [note.get_simplified_display() for note in self.notes]
        else:
            return [note.get_full_display(include_metadata) for note in self.notes]
    
    def calculate_completeness(self) -> float:
        """计算信息完整度"""
        score = 0
        total = 10  # 调整总分以包含笔记
        
        # 核心信息权重更高
        if self.core_info.pronunciation: score += 1.5
        if self.core_info.primary_definition: score += 2
        if self.core_info.part_of_speech: score += 1
        
        # 扩展信息
        if self.extended_info.definitions: score += 1.5
        if self.extended_info.examples: score += 1.5
        if self.extended_info.synonyms: score += 1
        if self.extended_info.etymology: score += 0.5
        if self.extended_info.memory_tips: score += 0.5
        
        # 笔记加分
        if self.notes: score += 0.5
        
        self.completeness = min(score / total, 1.0)
        return self.completeness
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'word': self.word,
            'status': self.status.value,
            'completeness': self.completeness,
            'tags': self.tags,
            'notes': [asdict(note) for note in self.notes],
            'core_info': asdict(self.core_info),
            'extended_info': asdict(self.extended_info),
            'learning_data': enum_asdict(asdict(self.learning_data))
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Word':
        """从字典创建Word对象"""
        word = cls(
            id=data['id'],
            word=data['word'],
            status=WordStatus(data.get('status', 'draft')),
            completeness=data.get('completeness', 0.0),
            tags=data.get('tags', [])
        )
        
        # 重建笔记
        if 'notes' in data:
            word.notes = [Note(**note_data) for note_data in data['notes']]
        
        # 重建其他信息
        if 'core_info' in data:
            word.core_info = CoreInfo(**data['core_info'])
        
        if 'extended_info' in data:
            word.extended_info = ExtendedInfo(**data['extended_info'])
        
        if 'learning_data' in data:
            ld_data = data['learning_data'].copy()
            if 'difficulty' in ld_data:
                if isinstance(ld_data['difficulty'], (str, int)):
                    ld_data['difficulty'] = DifficultyLevel(int(ld_data['difficulty']))
            word.learning_data = LearningData(**ld_data)
        
        return word


# 抽象接口定义
class IVocabularyStorage(ABC):
    """词汇存储接口"""
    
    @abstractmethod
    def load(self) -> Dict[str, Word]:
        """加载所有单词"""
        pass
    
    @abstractmethod
    def save(self, words: Dict[str, Word]) -> bool:
        """保存所有单词"""
        pass
    
    @abstractmethod
    def backup(self) -> bool:
        """备份数据"""
        pass


class ILearningAlgorithm(ABC):
    """学习算法接口"""
    
    @abstractmethod
    def calculate_next_review(self, word: Word, performance: str) -> datetime:
        """计算下次复习时间"""
        pass
    
    @abstractmethod
    def should_promote_status(self, word: Word) -> bool:
        """判断是否应该提升状态"""
        pass


class IUIAdapter(Protocol):
    """UI适配器接口"""
    
    def display_message(self, message: str, level: str = "info") -> None:
        """显示消息"""
        ...
    
    def get_user_input(self, prompt: str, input_type: str = "text") -> Any:
        """获取用户输入"""
        ...
    
    def display_word_list(self, words: List[Word], simplified: bool = True) -> None:
        """显示单词列表"""
        ...
    
    def display_statistics(self, stats: Dict[str, Any]) -> None:
        """显示统计信息"""
        ...


# 具体实现类
class JSONStorage(IVocabularyStorage):
    """JSON文件存储实现"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def load(self) -> Dict[str, Word]:
        """加载数据"""
        words = {}
        if os.path.exists(self.config.data_file):
            try:
                with open(self.config.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for word_data in data.get('words', []):
                        word = Word.from_dict(word_data)
                        words[word.id] = word
            except Exception as e:
                print(f"加载数据失败: {e}")
        return words
    
    def save(self, words: Dict[str, Word]) -> bool:
        """保存数据"""
        try:
            data = {
                'version': '1.1',
                'created_at': datetime.now().isoformat(),
                'word_count': len(words),
                'words': [word.to_dict() for word in words.values()]
            }
            with open(self.config.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False
    
    def backup(self) -> bool:
        """创建备份"""
        if not self.config.backup_enabled or not os.path.exists(self.config.data_file):
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.config.data_file}.backup.{timestamp}"
            
            import shutil
            shutil.copy2(self.config.data_file, backup_file)
            
            # 清理旧备份
            self._cleanup_old_backups()
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            import glob
            backup_pattern = f"{self.config.data_file}.backup.*"
            backup_files = sorted(glob.glob(backup_pattern), reverse=True)
            
            if len(backup_files) > self.config.backup_count:
                for old_backup in backup_files[self.config.backup_count:]:
                    os.remove(old_backup)
        except Exception as e:
            print(f"清理备份失败: {e}")


class SimpleSpacedRepetition(ILearningAlgorithm):
    """简单间隔重复算法实现"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def calculate_next_review(self, word: Word, performance: str) -> datetime:
        """计算下次复习时间"""
        base_interval = self.config.sr_base_intervals.get(performance, 1.0)
        
        # 根据复习次数调整间隔
        review_multiplier = min(word.learning_data.review_count * 0.3 + 1, 3.0)
        
        # 根据正确率调整
        if word.learning_data.review_count > 0:
            accuracy = word.learning_data.correct_count / word.learning_data.review_count
            accuracy_multiplier = max(0.5, accuracy * 1.5)
        else:
            accuracy_multiplier = 1.0
        
        final_interval = min(
            base_interval * review_multiplier * accuracy_multiplier,
            self.config.max_interval_days
        )
        
        return datetime.now() + timedelta(days=final_interval)
    
    def should_promote_status(self, word: Word) -> bool:
        """判断是否应该提升状态"""
        if word.learning_data.review_count < self.config.mastery_review_count:
            return False
        
        accuracy = word.learning_data.correct_count / word.learning_data.review_count
        return accuracy >= self.config.mastery_threshold


class VocabularyCore:
    """词汇管理核心类"""
    
    def __init__(self, config: AppConfig = None, 
                 storage: IVocabularyStorage = None,
                 algorithm: ILearningAlgorithm = None):
        self.config = config or AppConfig()
        self.storage = storage or JSONStorage(self.config)
        self.algorithm = algorithm or SimpleSpacedRepetition(self.config)
        
        self.words: Dict[str, Word] = {}
        self._auto_save_timer: Optional[threading.Timer] = None
        self._data_changed = False
        
        # 事件回调
        self.on_word_added: Optional[Callable[[Word], None]] = None
        self.on_word_updated: Optional[Callable[[Word], None]] = None
        self.on_data_saved: Optional[Callable[[], None]] = None
        
        self.load_data()
        if self.config.auto_save:
            self._start_auto_save()
    
    def load_data(self):
        """加载数据"""
        self.words = self.storage.load()
        self._data_changed = False
    
    def save_data(self, force: bool = False) -> bool:
        """保存数据"""
        if not force and not self._data_changed:
            return True
        
        success = self.storage.save(self.words)
        if success:
            self._data_changed = False
            if self.on_data_saved:
                self.on_data_saved()
        return success
    
    def add_word(self, word_str: str, **kwargs) -> Word:
        """添加新单词"""
        word_id = str(uuid.uuid4())
        word = Word(id=word_id, word=word_str.lower().strip())
        
        # 设置可选参数
        for key, value in kwargs.items():
            if hasattr(word.core_info, key):
                setattr(word.core_info, key, value)
            elif hasattr(word.learning_data, key):
                setattr(word.learning_data, key, value)
            elif hasattr(word, key):
                setattr(word, key, value)
        
        # 如果有基本定义，状态改为learning
        if word.core_info.primary_definition:
            word.status = WordStatus.LEARNING
        
        word.calculate_completeness()
        self.words[word_id] = word
        self._data_changed = True
        
        if self.on_word_added:
            self.on_word_added(word)
        
        return word
    
    def update_word(self, word_id: str, **kwargs) -> Optional[Word]:
        """更新单词"""
        word = self.words.get(word_id)
        if not word:
            return None
        
        for key, value in kwargs.items():
            if hasattr(word.core_info, key):
                setattr(word.core_info, key, value)
            elif hasattr(word.extended_info, key):
                setattr(word.extended_info, key, value)
            elif hasattr(word.learning_data, key):
                setattr(word.learning_data, key, value)
            elif hasattr(word, key):
                setattr(word, key, value)
        
        word.calculate_completeness()
        self._data_changed = True
        
        if self.on_word_updated:
            self.on_word_updated(word)
        
        return word
    
    def add_note_to_word(self, word_id: str, content: str, 
                        tags: List[str] = None) -> Optional[Note]:
        """为单词添加笔记"""
        word = self.words.get(word_id)
        if not word:
            return None
        
        note = word.add_note(content, tags)
        word.calculate_completeness()
        self._data_changed = True
        
        if self.on_word_updated:
            self.on_word_updated(word)
        
        return note
    
    def get_word(self, word_id: str) -> Optional[Word]:
        """获取单词"""
        return self.words.get(word_id)
    
    def search_words(self, query: str, limit: int = None) -> List[Word]:
        """搜索单词"""
        if not query:
            return []
        
        query = query.lower()
        results = []
        
        for word in self.words.values():
            if (query in word.word.lower() or 
                query in word.core_info.primary_definition.lower() or
                any(query in tag.lower() for tag in word.tags) or
                any(query in note.content.lower() for note in word.notes)):
                results.append(word)
        
        # 按相关度排序（简单实现）
        results.sort(key=lambda w: (
            query == w.word.lower(),  # 精确匹配优先
            query in w.word.lower(),  # 单词匹配
            w.completeness  # 完整度高的优先
        ), reverse=True)
        
        limit = limit or self.config.search_result_limit
        return results[:limit]
    
    def get_words_by_status(self, status: WordStatus) -> List[Word]:
        """按状态获取单词"""
        return [w for w in self.words.values() if w.status == status]
    
    def get_words_for_review(self) -> List[Word]:
        """获取需要复习的单词"""
        now = datetime.now()
        review_words = []
        
        for word in self.words.values():
            if word.status in [WordStatus.LEARNING, WordStatus.REVIEWING]:
                if not word.learning_data.next_review:
                    review_words.append(word)
                else:
                    try:
                        next_review = datetime.fromisoformat(word.learning_data.next_review)
                        if now >= next_review:
                            review_words.append(word)
                    except:
                        review_words.append(word)
        
        return review_words
    
    def update_word_after_review(self, word_id: str, performance: str) -> bool:
        """复习后更新单词状态"""
        word = self.words.get(word_id)
        if not word:
            return False
        
        # 更新学习数据
        word.learning_data.review_count += 1
        word.learning_data.last_reviewed = datetime.now().isoformat()
        
        if performance in ['excellent', 'good']:
            word.learning_data.correct_count += 1
        
        # 计算下次复习时间
        next_review = self.algorithm.calculate_next_review(word, performance)
        word.learning_data.next_review = next_review.isoformat()
        
        # 检查是否应该提升状态
        if self.algorithm.should_promote_status(word):
            if word.status == WordStatus.LEARNING:
                word.status = WordStatus.REVIEWING
            elif word.status == WordStatus.REVIEWING:
                word.status = WordStatus.MASTERED
        
        self._data_changed = True
        
        if self.on_word_updated:
            self.on_word_updated(word)
        
        return True
    
    def get_all_words_paginated(self, page: int = 1, page_size: int = 20, 
                               sort_by: SortOrder = SortOrder.ALPHABETICAL,
                               reverse: bool = False) -> Tuple[List[Word], int, int]:
        """获取分页的单词列表
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            sort_by: 排序方式
            reverse: 是否逆序
            
        Returns:
            (单词列表, 总页数, 总数量)
        """
        words_list = list(self.words.values())
        
        # 排序
        if sort_by == SortOrder.ALPHABETICAL:
            words_list.sort(key=lambda w: w.word.lower(), reverse=reverse)
        elif sort_by == SortOrder.ADDED_TIME:
            words_list.sort(key=lambda w: w.learning_data.added_date, reverse=reverse)
        elif sort_by == SortOrder.REVIEW_TIME:
            words_list.sort(key=lambda w: w.learning_data.last_reviewed or "1970-01-01", reverse=reverse)
        elif sort_by == SortOrder.COMPLETENESS:
            words_list.sort(key=lambda w: w.completeness, reverse=reverse)
        elif sort_by == SortOrder.STATUS:
            words_list.sort(key=lambda w: w.status.value, reverse=reverse)
        elif sort_by == SortOrder.REVIEW_COUNT:
            words_list.sort(key=lambda w: w.learning_data.review_count, reverse=reverse)
        
        # 分页
        total_count = len(words_list)
        total_pages = (total_count + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return words_list[start_idx:end_idx], total_pages, total_count
    
    def delete_word(self, word_id: str) -> bool:
        """删除单词"""
        if word_id not in self.words:
            return False
        
        del self.words[word_id]
        self._data_changed = True
        return True
    
    def delete_words_batch(self, word_ids: List[str]) -> Tuple[int, int]:
        """批量删除单词
        
        Returns:
            (成功删除数量, 失败数量)
        """
        success_count = 0
        fail_count = 0
        
        for word_id in word_ids:
            if self.delete_word(word_id):
                success_count += 1
            else:
                fail_count += 1
        
        return success_count, fail_count
    
    def update_word_comprehensive(self, word_id: str, **kwargs) -> Optional[Word]:
        """全面更新单词信息"""
        word = self.words.get(word_id)
        if not word:
            return None
        
        # 更新核心信息
        if 'core_info' in kwargs:
            core_data = kwargs['core_info']
            for key, value in core_data.items():
                if hasattr(word.core_info, key):
                    setattr(word.core_info, key, value)
        
        # 更新扩展信息
        if 'extended_info' in kwargs:
            ext_data = kwargs['extended_info']
            for key, value in ext_data.items():
                if hasattr(word.extended_info, key):
                    setattr(word.extended_info, key, value)
        
        # 更新学习数据
        if 'learning_data' in kwargs:
            learn_data = kwargs['learning_data']
            for key, value in learn_data.items():
                if hasattr(word.learning_data, key):
                    setattr(word.learning_data, key, value)
        
        # 更新其他属性
        for key, value in kwargs.items():
            if key not in ['core_info', 'extended_info', 'learning_data']:
                if hasattr(word, key):
                    setattr(word, key, value)
        
        word.calculate_completeness()
        self._data_changed = True
        
        if self.on_word_updated:
            self.on_word_updated(word)
        
        return word
    
    def add_note_quick(self, word_id: str, content: str, 
                      tags: List[str] = None, context: str = "") -> Optional[Note]:
        """快速添加笔记（支持更多场景）"""
        word = self.words.get(word_id)
        if not word:
            return None
        
        # 创建带上下文的笔记
        note_content = content
        if context:
            note_content = f"[{context}] {content}"
        
        note = word.add_note(note_content, tags)
        word.calculate_completeness()
        self._data_changed = True
        
        if self.on_word_updated:
            self.on_word_updated(word)
        
        return note
    
    def add_note_during_review(self, word_id: str, content: str, 
                              review_context: str = "复习中") -> Optional[Note]:
        """复习时添加笔记"""
        return self.add_note_quick(word_id, content, 
                                 tags=["review", "learning"], 
                                 context=review_context)
    
    def get_words_by_tag(self, tag: str) -> List[Word]:
        """按标签获取单词"""
        return [w for w in self.words.values() if tag in w.tags]
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        all_tags = set()
        for word in self.words.values():
            all_tags.update(word.tags)
        return sorted(list(all_tags))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        stats = {
            'total_words': len(self.words),
            'by_status': {},
            'avg_completeness': 0,
            'words_for_review': len(self.get_words_for_review()),
            'notes_count': sum(len(w.notes) for w in self.words.values()),
            'last_added': None,
            'last_reviewed': None,
            'total_tags': len(self.get_all_tags())
        }
        
        # 状态统计
        for status in WordStatus:
            count = len(self.get_words_by_status(status))
            stats['by_status'][status.value] = count
        
        # 平均完整度
        if self.words:
            total_completeness = sum(w.completeness for w in self.words.values())
            stats['avg_completeness'] = total_completeness / len(self.words)
        
        # 最近添加和复习
        words_list = list(self.words.values())
        if words_list:
            # 最近添加
            latest_added = max(words_list, key=lambda w: w.learning_data.added_date)
            stats['last_added'] = latest_added.learning_data.added_date
            
            # 最近复习
            reviewed_words = [w for w in words_list if w.learning_data.last_reviewed]
            if reviewed_words:
                latest_reviewed = max(reviewed_words, 
                                    key=lambda w: w.learning_data.last_reviewed)
                stats['last_reviewed'] = latest_reviewed.learning_data.last_reviewed
        
        return stats
    
    def _start_auto_save(self):
        """启动自动保存"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
        
        def auto_save():
            if self._data_changed:
                self.save_data()
            self._start_auto_save()  # 重新设置定时器
        
        self._auto_save_timer = threading.Timer(
            self.config.auto_save_interval, auto_save
        )
        self._auto_save_timer.daemon = True
        self._auto_save_timer.start()
    
    def cleanup(self):
        """清理资源"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
        
        # 保存未保存的数据
        if self._data_changed:
            self.save_data()


def create_default_core() -> VocabularyCore:
    """创建默认配置的核心实例"""
    config = AppConfig.load()
    return VocabularyCore(config)





if __name__ == "__main__":
    # 演示用的简单控制台UI适配器
    class ConsoleUI:
        """简单的控制台UI实现"""
        
        def display_message(self, message: str, level: str = "info"):
            prefix = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}
            print(f"{prefix.get(level, 'ℹ')} {message}")
        
        def get_user_input(self, prompt: str, input_type: str = "text") -> Any:
            if input_type == "text":
                return input(f"{prompt}: ").strip()
            elif input_type == "choice":
                return input(f"{prompt} (y/n): ").lower() == 'y'
            return input(f"{prompt}: ")
        
        def display_word_list(self, words: List[Word], simplified: bool = True):
            if not words:
                print("无单词")
                return
            
            for i, word in enumerate(words, 1):
                status_icon = {"draft": "📝", "learning": "📚", "reviewing": "🔄", "mastered": "✅"}
                print(f"{i}. {status_icon.get(word.status.value, '?')} {word.word}")
                print(f"   {word.core_info.primary_definition}")
                if word.notes and not simplified:
                    for note in word.notes[:2]:  # 只显示前2个笔记
                        print(f"   💬 {note.get_simplified_display()}")
                print(f"   完整度: {word.completeness:.1%} | 状态: {word.status.value}")
                print()
        
        def display_statistics(self, stats: Dict[str, Any]):
            print("=== 学习统计 ===")
            print(f"总单词数: {stats['total_words']}")
            print(f"平均完整度: {stats['avg_completeness']:.1%}")
            print(f"待复习: {stats['words_for_review']}")
            print(f"笔记总数: {stats['notes_count']}")
            print("\n状态分布:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
    # 简单演示
    print("=== 单词记忆程序核心模块演示 ===")
    
    core = create_default_core()
    ui = ConsoleUI()
    
    # 演示添加单词
    word = core.add_word("ubiquitous", 
                        primary_definition="existing everywhere",
                        pronunciation="/juːˈbɪkwɪtəs/")
    
    # 添加笔记
    core.add_note_to_word(word.id, "在The Economist文章中遇到", ["reading"])
    
    ui.display_message("已添加示例单词", "success")
    ui.display_word_list([word], simplified=False)
    
    # 显示统计
    stats = core.get_statistics()
    ui.display_statistics(stats)
    
    core.cleanup()