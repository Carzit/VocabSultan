# VocabSultan 架构文档

## 系统架构概览

VocabSultan 采用模块化设计，将核心业务逻辑与用户界面分离，支持多种存储后端和用户界面实现。

```
┌─────────────────────────────────────────────────────────────┐
│                    VocabSultan 系统架构                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   CLI 界面      │  │   Web 界面      │  │   其他界面      │ │
│  │ (Rich CLI)      │  │  (未来扩展)     │  │  (未来扩展)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                核心业务逻辑层 (Core)                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ 词汇管理    │  │ 学习算法    │  │ 配置管理    │     │ │
│  │  │ Vocabulary  │  │ Spaced      │  │ AppConfig   │     │ │
│  │  │ Core        │  │ Repetition  │  │             │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                数据访问层 (Storage)                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ JSON 存储   │  │ 数据库存储  │  │ 云存储      │     │ │
│  │  │ JSONStorage │  │ (未来扩展)  │  │ (未来扩展)  │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. 数据模型 (Data Models)

#### Word (单词)
```python
@dataclass
class Word:
    id: str                    # 唯一标识符
    word: str                  # 单词文本
    status: WordStatus         # 学习状态
    completeness: float        # 信息完整度
    tags: List[str]           # 标签列表
    notes: List[Note]         # 笔记列表
    core_info: CoreInfo       # 核心信息
    extended_info: ExtendedInfo # 扩展信息
    learning_data: LearningData # 学习数据
```

#### Note (笔记)
```python
@dataclass
class Note:
    id: str                   # 唯一标识符
    content: str              # 笔记内容
    created_at: str           # 创建时间
    tags: List[str]           # 标签列表
```

#### AppConfig (应用配置)
```python
@dataclass
class AppConfig:
    # 基本设置
    auto_save: bool
    auto_save_interval: int
    
    # 添加单词配置
    add_word_config: AddWordConfig
    
    # UI默认值配置
    ui_defaults: UIChoiceDefaults
    
    # 学习算法配置
    mastery_threshold: float
    sr_base_intervals: Dict[str, float]
```

### 2. 核心业务逻辑 (VocabularyCore)

VocabularyCore 是系统的核心类，负责：

- **词汇管理**：添加、更新、删除、搜索单词
- **学习调度**：管理复习计划和状态转换
- **数据持久化**：与存储层交互
- **事件通知**：支持回调机制

```python
class VocabularyCore:
    def __init__(self, config, storage, algorithm):
        self.config = config
        self.storage = storage
        self.algorithm = algorithm
        self.words: Dict[str, Word] = {}
    
    def add_word(self, word_str: str, **kwargs) -> Word:
        """添加新单词"""
        
    def update_word_after_review(self, word_id: str, performance: str) -> bool:
        """复习后更新单词状态"""
        
    def get_words_for_review(self) -> List[Word]:
        """获取需要复习的单词"""
```

### 3. 存储接口 (Storage Interface)

#### IVocabularyStorage
```python
class IVocabularyStorage(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Word]:
        """加载所有单词"""
        
    @abstractmethod
    def save(self, words: Dict[str, Word]) -> bool:
        """保存所有单词"""
        
    @abstractmethod
    def backup(self) -> bool:
        """备份数据"""
```

#### JSONStorage 实现
- 使用 JSON 格式存储数据
- 支持自动备份
- 包含版本控制和元数据

### 4. 学习算法 (Learning Algorithm)

#### ILearningAlgorithm
```python
class ILearningAlgorithm(ABC):
    @abstractmethod
    def calculate_next_review(self, word: Word, performance: str) -> datetime:
        """计算下次复习时间"""
        
    @abstractmethod
    def should_promote_status(self, word: Word) -> bool:
        """判断是否应该提升状态"""
```

#### SimpleSpacedRepetition 实现
- 基于 SM-2 算法的简化版本
- 支持四种表现等级
- 可配置的间隔参数

### 5. 用户界面 (User Interface)

#### CLI 界面 (Rich CLI)
- 基于 Rich 库的美观命令行界面
- 支持表格、进度条、颜色等丰富显示
- 完整的交互式操作流程

#### UI 适配器接口
```python
class IUIAdapter(Protocol):
    def display_message(self, message: str, level: str) -> None:
        """显示消息"""
        
    def get_user_input(self, prompt: str, input_type: str) -> Any:
        """获取用户输入"""
        
    def display_word_list(self, words: List[Word]) -> None:
        """显示单词列表"""
```

## 数据流

### 1. 添加单词流程
```
用户输入 → CLI界面 → VocabularyCore → 数据验证 → 存储层 → 回调通知
```

### 2. 复习流程
```
获取复习单词 → 显示单词 → 用户评估 → 更新学习数据 → 计算下次复习时间 → 保存数据
```

### 3. 配置管理流程
```
用户修改配置 → 验证配置 → 保存到文件 → 重新加载配置 → 应用新设置
```

## 扩展点

### 1. 存储后端扩展
- 数据库存储 (SQLite, PostgreSQL, MySQL)
- 云存储 (AWS S3, Google Cloud Storage)
- 内存存储 (用于测试)

### 2. 学习算法扩展
- SM-2 完整实现
- Anki 算法
- 自定义算法

### 3. 用户界面扩展
- Web 界面 (Flask/Django)
- 桌面应用 (Tkinter, PyQt)
- 移动应用 (Kivy)

### 4. 功能扩展
- 语音识别和发音
- 图像和多媒体支持
- 社交功能
- 数据分析和报告

## 性能考虑

### 1. 内存管理
- 使用字典存储单词，O(1) 查找时间
- 延迟加载大数据集
- 定期清理临时数据

### 2. 存储优化
- JSON 格式便于查看和调试
- 压缩存储减少文件大小
- 增量备份减少存储空间

### 3. 算法效率
- 高效的搜索算法
- 优化的排序和分页
- 缓存常用计算结果

## 安全考虑

### 1. 数据安全
- 本地存储，不上传云端
- 自动备份机制
- 数据完整性检查

### 2. 输入验证
- 严格的输入验证
- 防止注入攻击
- 错误处理机制

### 3. 隐私保护
- 用户数据本地化
- 无数据收集
- 透明的数据处理

## 测试策略

### 1. 单元测试
- 核心业务逻辑测试
- 数据模型测试
- 算法测试

### 2. 集成测试
- 存储层测试
- 用户界面测试
- 端到端测试

### 3. 性能测试
- 大数据集测试
- 内存使用测试
- 响应时间测试

## 部署和分发

### 1. 包管理
- 使用 pyproject.toml 配置
- 支持 pip 安装
- 版本控制

### 2. 依赖管理
- 最小化依赖
- 版本锁定
- 可选依赖

### 3. 跨平台支持
- Windows, macOS, Linux
- Python 3.8+
- 无系统依赖

---

这个架构设计确保了系统的可扩展性、可维护性和性能，同时保持了代码的清晰和简洁。
