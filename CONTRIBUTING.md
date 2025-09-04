# 贡献指南

感谢您对 VocabSultan 项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 Bug 报告
- 💡 功能建议
- 📝 文档改进
- 🔧 代码贡献
- 🧪 测试用例

## 如何贡献

### 1. 报告问题

如果您发现了 bug 或有功能建议，请：

1. 查看 [Issues](https://github.com/your-username/VocabSultan/issues) 确认问题未被报告
2. 创建新的 Issue，包含：
   - 清晰的问题描述
   - 复现步骤
   - 期望的行为
   - 实际的行为
   - 环境信息（Python版本、操作系统等）

### 2. 代码贡献

#### 开发环境设置

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/VocabSultan.git
   cd VocabSultan
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -e ".[dev]"
   ```

4. **安装预提交钩子**
   ```bash
   pre-commit install
   ```

#### 开发流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **编写代码**
   - 遵循 PEP 8 代码风格
   - 添加类型注解
   - 编写清晰的文档字符串
   - 添加适当的测试用例

3. **运行测试**
   ```bash
   pytest
   ```

4. **代码格式化**
   ```bash
   black .
   flake8 .
   mypy .
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

6. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```

#### 提交信息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

示例：
```
feat: 添加批量导入功能
fix: 修复复习算法中的时间计算错误
docs: 更新API文档
```

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [flake8](https://flake8.pycqa.org/) 进行代码检查
- 使用 [mypy](https://mypy.readthedocs.io/) 进行类型检查

### 文档字符串

使用 Google 风格的文档字符串：

```python
def add_word(self, word_str: str, **kwargs) -> Word:
    """添加新单词到词汇库
    
    Args:
        word_str: 要添加的单词
        **kwargs: 其他可选参数，如释义、发音等
        
    Returns:
        创建的Word对象
        
    Raises:
        ValueError: 当单词格式不正确时
    """
```

### 测试规范

- 为新功能编写单元测试
- 测试覆盖率应保持在 80% 以上
- 使用描述性的测试名称
- 测试应该独立且可重复

示例：
```python
def test_add_word_with_definition():
    """测试添加带释义的单词"""
    core = VocabularyCore()
    word = core.add_word("test", primary_definition="测试")
    
    assert word.word == "test"
    assert word.core_info.primary_definition == "测试"
    assert word.status == WordStatus.LEARNING
```

## 项目结构

```
VocabSultan/
├── core.py                 # 核心业务逻辑
├── vocab_sultan_cli.py     # CLI用户界面
├── utils.py               # 工具函数
├── tests/                 # 测试文件
├── docs/                  # 文档
├── README.md              # 项目说明
├── CHANGELOG.md           # 更新日志
├── CONTRIBUTING.md        # 贡献指南
├── LICENSE                # 许可证
├── pyproject.toml         # 项目配置
└── requirements.txt       # 依赖列表
```

## 开发指南

### 添加新功能

1. 在 `core.py` 中添加核心逻辑
2. 在 `vocab_sultan_cli.py` 中添加用户界面
3. 更新文档和测试
4. 更新 CHANGELOG.md

### 修改现有功能

1. 确保向后兼容性
2. 更新相关测试
3. 更新文档
4. 考虑是否需要更新配置

### 性能优化

- 使用性能分析工具识别瓶颈
- 优化算法复杂度
- 减少内存使用
- 添加性能测试

## 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 运行完整测试套件
4. 创建发布标签
5. 构建和发布包

## 社区准则

### 行为准则

- 保持友善和尊重
- 欢迎不同背景的贡献者
- 专注于对项目最有利的事情
- 尊重不同的观点和经验

### 沟通渠道

- GitHub Issues: Bug 报告和功能建议
- GitHub Discussions: 一般讨论和问题
- Pull Requests: 代码审查和讨论

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 感谢

感谢所有为 VocabSultan 项目做出贡献的开发者！

---

如果您有任何问题，请随时在 [Issues](https://github.com/your-username/VocabSultan/issues) 中提问。
