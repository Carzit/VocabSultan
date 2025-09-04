#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词记忆程序 - Rich CLI版本
使用Rich库提供美观的命令行界面

使用方法:
python rich_cli.py
"""

import sys
import os
from typing import List, Optional, Any, Dict
from datetime import datetime
import time

# 添加核心模块路径
sys.path.append(os.path.dirname(__file__))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.text import Text
    from rich.columns import Columns
    from rich.tree import Tree
    from rich.align import Align
    from rich.live import Live
    from rich.rule import Rule
    from rich.markdown import Markdown
    from rich import box
    import rich.traceback
except ImportError:
    print("请安装Rich库: pip install rich")
    sys.exit(1)

# 导入核心模块
from core import (
    VocabularyCore, Word, WordStatus, AppConfig, 
    create_default_core, Note, SortOrder, AddWordConfig, UIChoiceDefaults
)

# 启用Rich的异常追踪
rich.traceback.install()


class RichCliUI:
    """Rich CLI用户界面"""
    
    def __init__(self):
        self.console = Console()
        self.core = create_default_core()
        
        # 状态图标映射
        self.status_icons = {
            WordStatus.DRAFT: "📝",
            WordStatus.LEARNING: "📚", 
            WordStatus.REVIEWING: "🔄",
            WordStatus.MASTERED: "✅"
        }
        
        self.status_colors = {
            WordStatus.DRAFT: "dim",
            WordStatus.LEARNING: "yellow",
            WordStatus.REVIEWING: "blue", 
            WordStatus.MASTERED: "green"
        }
        
        # 设置回调
        self.core.on_word_added = self._on_word_added
        self.core.on_word_updated = self._on_word_updated
        self.core.on_data_saved = self._on_data_saved
    
    def _on_word_added(self, word: Word):
        """单词添加回调"""
        self.console.print(f"✨ 已添加单词: [bold]{word.word}[/bold]", style="green")
    
    def _on_word_updated(self, word: Word):
        """单词更新回调"""
        pass  # 静默更新
    
    def _on_data_saved(self):
        """数据保存回调"""
        self.console.print("💾 数据已自动保存", style="dim")
    
    def display_header(self):
        """显示标题"""
        title = Text("Vocab Sultan Rich CLI", style="bold magenta")
        subtitle = Text("Developed by Carzit", style="italic")
        
        panel = Panel(
            Align.center(f"{title}\n{subtitle}"),
            box=box.DOUBLE,
            border_style="magenta"
        )
        self.console.print(panel)
    
    def display_main_menu(self):
        """显示主菜单"""
        stats = self.core.get_statistics()
        
        # 创建菜单选项
        menu_items = [
            ("1", "📝", "添加单词", "添加新单词到词汇库"),
            ("2", "📚", "批量添加", "连续添加多个单词"),
            ("3", "🧠", "开始复习", f"复习 {stats['words_for_review']} 个单词"),
            ("4", "🔍", "搜索单词", "查找和浏览单词"),
            ("5", "📊", "学习统计", "查看详细学习报告"),
            ("6", "💾", "数据管理", "保存、备份和导入数据"),
            ("7", "📋", "词汇表管理", "浏览、编辑、删除词汇"),
            ("8", "⚙️", "设置管理", "修改配置和偏好"),
            ("9", "❌", "退出程序", "保存并退出"),
        ]
        
        table = Table(show_header=True, header_style="bold blue", box=box.ROUNDED)
        table.add_column("选项", style="cyan", width=8)
        table.add_column("功能", width=20)
        table.add_column("描述", style="dim")
        
        for option, icon, title, desc in menu_items:
            table.add_row(option, f"{icon} {title}", desc)
        
        # 显示状态栏
        status_text = (f"📚 总词数: {stats['total_words']} | "
                      f"⏰ 待复习: {stats['words_for_review']} | "
                      f"📈 平均完整度: {stats['avg_completeness']:.1%}")
        
        self.console.print()
        self.console.print(Panel(table, title="主菜单", border_style="blue"))
        self.console.print(Panel(status_text, style="dim"))
    
    def quick_add_word(self):
        """快速添加单词"""
        self.console.print(Rule("[bold]快速添加单词[/bold]"))
        
        while True:
            word = Prompt.ask("🔤 请输入单词 (输入 'back' 返回)")
            if word.lower() == 'back':
                break
            
            if not word.strip():
                continue
            
            # 检查是否已存在
            existing = self.core.search_words(word)
            if existing:
                self.console.print(f"⚠️  发现相似单词:")
                self.display_word_brief_list(existing[:3])
                
                if not Confirm.ask("继续添加吗?", default=False):
                    continue
            
            # 交互式输入
            definition = Prompt.ask("📖 主要释义", default="")
            
            # 根据配置决定是否跳过某些步骤
            config = self.core.config.add_word_config
            
            pronunciation = ""
            if not config.skip_pronunciation:
                pronunciation = Prompt.ask("🔊 发音 (可选)", default="")
            
            part_of_speech = ""
            if not config.skip_part_of_speech:
                part_of_speech = Prompt.ask("📝 词性 (可选)", default="")
            
            context = ""
            if not config.skip_context:
                context = Prompt.ask("📍 遇到语境 (可选)", default="")
            
            # 标签处理
            tags = config.default_tags.copy() if config.default_tags else []
            if not config.skip_tags:
                tags_input = Prompt.ask("🏷️  标签 (逗号分隔，可选)", default="")
                if tags_input.strip():
                    tags.extend([t.strip() for t in tags_input.split(',') if t.strip()])
            tags = list(set(tags))  # 去重
            
            # 添加单词
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("正在添加单词...", total=None)
                
                word_obj = self.core.add_word(
                    word,
                    primary_definition=definition,
                    pronunciation=pronunciation,
                    part_of_speech=part_of_speech,
                    context=context,
                    tags=tags
                )
                
                time.sleep(0.5)  # 视觉效果
                progress.update(task, completed=True)
            
            # 显示添加结果
            self.display_word_detail(word_obj)
            
            # 询问是否添加笔记
            if Confirm.ask("添加学习笔记吗?", default=False):
                self.add_note_to_word(word_obj)
            
            if not Confirm.ask("继续添加其他单词?", default=True):
                break
    
    def batch_input_session(self):
        """批量输入会话"""
        self.console.print(Rule("[bold]批量输入模式[/bold]"))
        self.console.print("💡 输入单词，按回车确认。输入 'done' 或 'quit' 结束")
        
        count = 0
        words_added = []
        
        while True:
            word = Prompt.ask(f"单词 #{count + 1}", default="")
            
            if word.lower() in ['done', 'quit', '']:
                break
            
            try:
                # 快速添加（根据配置决定输入内容）
                config = self.core.config.add_word_config
                definition = Prompt.ask("释义 (可选)", default="")
                
                # 构建添加参数
                add_kwargs = {"primary_definition": definition}
                
                # 根据配置添加其他信息
                if not config.skip_pronunciation:
                    pronunciation = Prompt.ask("发音 (可选)", default="")
                    if pronunciation:
                        add_kwargs["pronunciation"] = pronunciation
                
                if not config.skip_part_of_speech:
                    part_of_speech = Prompt.ask("词性 (可选)", default="")
                    if part_of_speech:
                        add_kwargs["part_of_speech"] = part_of_speech
                
                if not config.skip_context:
                    context = Prompt.ask("语境 (可选)", default="")
                    if context:
                        add_kwargs["context"] = context
                
                # 处理标签
                tags = config.default_tags.copy() if config.default_tags else []
                if not config.skip_tags:
                    tags_input = Prompt.ask("标签 (可选)", default="")
                    if tags_input.strip():
                        tags.extend([t.strip() for t in tags_input.split(',') if t.strip()])
                
                if tags:
                    add_kwargs["tags"] = list(set(tags))  # 去重
                
                word_obj = self.core.add_word(word, **add_kwargs)
                words_added.append(word_obj)
                count += 1
                
                self.console.print(f"✅ 已添加: {word}", style="green")
                
            except Exception as e:
                self.console.print(f"❌ 添加失败: {e}", style="red")
        
        # 显示批量添加结果
        if words_added:
            self.console.print(f"\n🎉 批量添加完成！共添加 {count} 个单词:")
            self.display_word_brief_list(words_added)
            
            # 询问是否立即开始学习
            if Confirm.ask("立即开始学习这些单词?", default=True):
                self.review_specific_words(words_added)
    
    def vocabulary_management(self):
        """词汇表管理"""
        self.console.print(Rule("[bold]词汇表管理[/bold]"))
        
        # 排序选项
        sort_options = [
            ("1", "按字母顺序", SortOrder.ALPHABETICAL),
            ("2", "按添加时间", SortOrder.ADDED_TIME),
            ("3", "按复习时间", SortOrder.REVIEW_TIME),
            ("4", "按完整度", SortOrder.COMPLETENESS),
            ("5", "按状态", SortOrder.STATUS),
            ("6", "按复习次数", SortOrder.REVIEW_COUNT),
        ]
        
        self.console.print("选择排序方式:")
        for key, desc, _ in sort_options:
            self.console.print(f"  {key}. {desc}")
        
        sort_choice = Prompt.ask("选择排序方式", choices=[s[0] for s in sort_options], 
                                default=self.core.config.ui_defaults.vocabulary_sort_default)
        sort_by = sort_options[int(sort_choice) - 1][2]
        
        # 是否逆序
        reverse = Confirm.ask("逆序排列?", default=False)
        
        # 分页显示
        self.show_vocabulary_paginated(sort_by, reverse)
    
    def show_vocabulary_paginated(self, sort_by: SortOrder, reverse: bool, page_size: int = 10):
        """分页显示词汇表"""
        page = 1
        
        while True:
            words, total_pages, total_count = self.core.get_all_words_paginated(
                page=page, page_size=page_size, sort_by=sort_by, reverse=reverse
            )
            
            self.console.clear()
            self.console.print(Rule(f"[bold]词汇表 - 第 {page}/{total_pages} 页 (共 {total_count} 个单词)[/bold]"))
            
            if not words:
                self.console.print("📝 暂无单词", style="dim")
                break
            
            # 显示单词列表
            self.display_word_list_with_actions(words, show_index=True)
            
            # 分页控制
            self.console.print(f"\n📄 第 {page}/{total_pages} 页")
            
            # 操作选项
            actions = []
            if page > 1:
                actions.append("p")
            if page < total_pages:
                actions.append("n")
            actions.extend(["s", "e", "d", "b"])
            
            action_descriptions = {
                "p": "上一页",
                "n": "下一页", 
                "s": "选择单词",
                "e": "批量编辑",
                "d": "批量删除",
                "b": "返回主菜单"
            }
            
            self.console.print("\n操作选项:")
            for action in actions:
                self.console.print(f"  {action}. {action_descriptions[action]}")
            
            choice = Prompt.ask("选择操作", choices=actions, default="b")
            
            if choice == "p" and page > 1:
                page -= 1
            elif choice == "n" and page < total_pages:
                page += 1
            elif choice == "s":
                self.select_word_from_list(words)
            elif choice == "e":
                self.batch_edit_words(words)
            elif choice == "d":
                self.batch_delete_words(words)
            elif choice == "b":
                break
    
    def display_word_list_with_actions(self, words: List[Word], show_index: bool = False):
        """显示带操作选项的单词列表"""
        table = Table(box=box.MINIMAL)
        if show_index:
            table.add_column("#", width=3)
        table.add_column("单词", style="bold")
        table.add_column("状态", width=8)
        table.add_column("释义", width=40)
        table.add_column("完整度", width=8)
        table.add_column("复习次数", width=8)
        
        for i, word in enumerate(words, 1):
            icon = self.status_icons.get(word.status, "?")
            status_color = self.status_colors.get(word.status, "white")
            
            row_data = []
            if show_index:
                row_data.append(str(i))
            
            row_data.extend([
                word.word,
                f"[{status_color}]{icon}[/{status_color}]",
                word.core_info.primary_definition[:40] + "..." if len(word.core_info.primary_definition) > 40 else word.core_info.primary_definition,
                f"{word.completeness:.0%}",
                str(word.learning_data.review_count)
            ])
            
            table.add_row(*row_data)
        
        self.console.print(table)
    
    def select_word_from_list(self, words: List[Word]):
        """从列表中选择单词进行详细操作"""
        try:
            choice = IntPrompt.ask(
                f"选择单词 (1-{len(words)}，0返回)",
                default=0
            )
            if 1 <= choice <= len(words):
                selected_word = words[choice - 1]
                self.show_word_detail_menu(selected_word)
        except:
            pass
    
    def batch_edit_words(self, words: List[Word]):
        """批量编辑单词"""
        self.console.print("🔧 批量编辑功能")
        self.console.print("选择要编辑的单词 (输入数字，用逗号分隔，如: 1,3,5)")
        
        try:
            selection = Prompt.ask("选择单词编号")
            if not selection.strip():
                return
            
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_words = [words[i] for i in indices if 0 <= i < len(words)]
            
            if not selected_words:
                self.console.print("❌ 没有选择有效的单词", style="red")
                return
            
            self.console.print(f"已选择 {len(selected_words)} 个单词:")
            self.display_word_brief_list(selected_words)
            
            if Confirm.ask("确认编辑这些单词?", 
                          default=self.core.config.ui_defaults.confirm_batch_edit):
                self.batch_edit_selected_words(selected_words)
                
        except Exception as e:
            self.console.print(f"❌ 输入格式错误: {e}", style="red")
    
    def batch_edit_selected_words(self, words: List[Word]):
        """批量编辑选中的单词"""
        self.console.print("选择要批量修改的属性:")
        edit_options = [
            ("1", "添加标签"),
            ("2", "修改状态"),
            ("3", "添加笔记"),
            ("4", "修改难度"),
        ]
        
        for key, desc in edit_options:
            self.console.print(f"  {key}. {desc}")
        
        choice = Prompt.ask("选择操作", choices=[o[0] for o in edit_options], 
                           default=self.core.config.ui_defaults.batch_edit_default)
        
        if choice == "1":
            self.batch_add_tags(words)
        elif choice == "2":
            self.batch_change_status(words)
        elif choice == "3":
            self.batch_add_notes(words)
        elif choice == "4":
            self.batch_change_difficulty(words)
    
    def batch_add_tags(self, words: List[Word]):
        """批量添加标签"""
        tags_input = Prompt.ask("要添加的标签 (逗号分隔)")
        tags = [t.strip() for t in tags_input.split(',') if t.strip()]
        
        if not tags:
            return
        
        success_count = 0
        for word in words:
            word.tags.extend(tags)
            word.tags = list(set(word.tags))  # 去重
            word.calculate_completeness()
            success_count += 1
        
        self.core._data_changed = True
        self.console.print(f"✅ 已为 {success_count} 个单词添加标签: {', '.join(tags)}", style="green")
    
    def batch_change_status(self, words: List[Word]):
        """批量修改状态"""
        status_options = [
            ("1", "草稿", WordStatus.DRAFT),
            ("2", "学习中", WordStatus.LEARNING),
            ("3", "复习中", WordStatus.REVIEWING),
            ("4", "已掌握", WordStatus.MASTERED),
        ]
        
        self.console.print("选择新状态:")
        for key, desc, _ in status_options:
            self.console.print(f"  {key}. {desc}")
        
        choice = Prompt.ask("选择状态", choices=[s[0] for s in status_options], 
                           default=self.core.config.ui_defaults.batch_status_default)
        new_status = status_options[int(choice) - 1][2]
        
        success_count = 0
        for word in words:
            word.status = new_status
            word.calculate_completeness()
            success_count += 1
        
        self.core._data_changed = True
        self.console.print(f"✅ 已将 {success_count} 个单词状态修改为: {new_status.value}", style="green")
    
    def batch_add_notes(self, words: List[Word]):
        """批量添加笔记"""
        note_content = Prompt.ask("笔记内容")
        if not note_content.strip():
            return
        
        tags_input = Prompt.ask("笔记标签 (可选)", default="")
        tags = [t.strip() for t in tags_input.split(',') if t.strip()]
        
        success_count = 0
        for word in words:
            self.core.add_note_quick(word.id, note_content, tags, "批量编辑")
            success_count += 1
        
        self.console.print(f"✅ 已为 {success_count} 个单词添加笔记", style="green")
    
    def batch_change_difficulty(self, words: List[Word]):
        """批量修改难度"""
        difficulty_options = [
            ("1", "简单", 1),
            ("2", "中等", 2),
            ("3", "困难", 3),
            ("4", "非常困难", 4),
        ]
        
        self.console.print("选择难度等级:")
        for key, desc, _ in difficulty_options:
            self.console.print(f"  {key}. {desc}")
        
        choice = Prompt.ask("选择难度", choices=[d[0] for d in difficulty_options], 
                           default=self.core.config.ui_defaults.batch_difficulty_default)
        new_difficulty = difficulty_options[int(choice) - 1][2]
        
        success_count = 0
        for word in words:
            word.learning_data.difficulty = new_difficulty
            success_count += 1
        
        self.core._data_changed = True
        self.console.print(f"✅ 已将 {success_count} 个单词难度修改为: {new_difficulty}", style="green")
    
    def batch_delete_words(self, words: List[Word]):
        """批量删除单词"""
        self.console.print("⚠️  批量删除功能")
        self.console.print("选择要删除的单词 (输入数字，用逗号分隔，如: 1,3,5)")
        
        try:
            selection = Prompt.ask("选择单词编号")
            if not selection.strip():
                return
            
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_words = [words[i] for i in indices if 0 <= i < len(words)]
            
            if not selected_words:
                self.console.print("❌ 没有选择有效的单词", style="red")
                return
            
            self.console.print(f"⚠️  即将删除 {len(selected_words)} 个单词:")
            self.display_word_brief_list(selected_words)
            
            if Confirm.ask("确认删除这些单词? (此操作不可撤销)", 
                          default=self.core.config.ui_defaults.confirm_delete):
                word_ids = [w.id for w in selected_words]
                success_count, fail_count = self.core.delete_words_batch(word_ids)
                
                if success_count > 0:
                    self.console.print(f"✅ 成功删除 {success_count} 个单词", style="green")
                if fail_count > 0:
                    self.console.print(f"❌ 删除失败 {fail_count} 个单词", style="red")
                
        except Exception as e:
            self.console.print(f"❌ 输入格式错误: {e}", style="red")
    
    def search_words(self):
        """搜索单词"""
        self.console.print(Rule("[bold]搜索单词[/bold]"))
        
        while True:
            query = Prompt.ask("🔍 搜索关键词 (输入 'back' 返回)")
            if query.lower() == 'back':
                break
            
            if not query.strip():
                continue
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("正在搜索...", total=None)
                results = self.core.search_words(query)
                time.sleep(0.3)
                progress.update(task, completed=True)
            
            if not results:
                self.console.print("😔 未找到相关单词", style="yellow")
                continue
            
            self.console.print(f"🎯 找到 {len(results)} 个相关单词:")
            self.display_word_list(results)
            
            # 详细查看选项
            if results:
                try:
                    choice = IntPrompt.ask(
                        f"选择查看详情 (1-{len(results)}，0返回)",
                        default=0
                    )
                    if 1 <= choice <= len(results):
                        selected_word = results[choice - 1]
                        self.show_word_detail_menu(selected_word)
                except:
                    continue
    
    def show_word_detail_menu(self, word: Word):
        """显示单词详情菜单"""
        while True:
            self.display_word_detail(word)
            
            actions = [
                ("1", "📝 添加笔记"),
                ("2", "✏️ 编辑信息"),
                ("3", "🏷️ 管理标签"),
                ("4", "🧠 立即复习"),
                ("5", "📊 学习记录"),
                ("6", "🗑️ 删除单词"),
                ("7", "◀️ 返回")
            ]
            
            self.console.print("\n可用操作:")
            for key, desc in actions:
                self.console.print(f"  {key}. {desc}")
            
            choice = Prompt.ask("选择操作", choices=[a[0] for a in actions], default="7")
            
            if choice == "1":
                self.add_note_to_word(word)
            elif choice == "2":
                self.edit_word_info(word)
            elif choice == "3":
                self.manage_word_tags(word)
            elif choice == "4":
                self.review_single_word(word)
            elif choice == "5":
                self.show_word_learning_history(word)
            elif choice == "6":
                self.delete_single_word(word)
                break  # 删除后退出菜单
            elif choice == "7":
                break
    
    def add_note_to_word(self, word: Word):
        """为单词添加笔记"""
        self.console.print(f"\n📝 为 '[bold]{word.word}[/bold]' 添加笔记")
        
        content = Prompt.ask("笔记内容")
        if not content.strip():
            return
        
        tags_input = Prompt.ask("笔记标签 (可选)", default="")
        tags = [t.strip() for t in tags_input.split(',') if t.strip()]
        
        note = self.core.add_note_to_word(word.id, content, tags)
        if note:
            self.console.print("✅ 笔记添加成功", style="green")
        else:
            self.console.print("❌ 添加失败", style="red")
    
    def add_note_during_review(self, word: Word):
        """复习时添加笔记"""
        self.console.print(f"\n📝 复习笔记 - '[bold]{word.word}[/bold]'")
        
        # 显示快速笔记选项
        quick_notes = [
            ("1", "记忆技巧", "记忆这个单词的技巧"),
            ("2", "易混词", "容易混淆的单词"),
            ("3", "使用场景", "在什么情况下使用"),
            ("4", "个人理解", "自己的理解和感悟"),
            ("5", "自定义", "输入自定义内容"),
        ]
        
        self.console.print("选择笔记类型:")
        for key, desc, _ in quick_notes:
            self.console.print(f"  {key}. {desc}")
        
        choice = Prompt.ask("选择类型", choices=[n[0] for n in quick_notes], 
                           default=self.core.config.ui_defaults.note_type_default)
        
        if choice == "1":
            content = Prompt.ask("记忆技巧")
            tags = ["memory", "tip"]
            context = "记忆技巧"
        elif choice == "2":
            content = Prompt.ask("易混词")
            tags = ["confusion", "similar"]
            context = "易混词"
        elif choice == "3":
            content = Prompt.ask("使用场景")
            tags = ["usage", "context"]
            context = "使用场景"
        elif choice == "4":
            content = Prompt.ask("个人理解")
            tags = ["understanding", "personal"]
            context = "个人理解"
        else:  # 自定义
            content = Prompt.ask("笔记内容")
            tags_input = Prompt.ask("标签 (可选)", default="")
            tags = [t.strip() for t in tags_input.split(',') if t.strip()]
            context = "复习笔记"
        
        if content.strip():
            note = self.core.add_note_during_review(word.id, content, context)
            if note:
                self.console.print("✅ 复习笔记添加成功", style="green")
            else:
                self.console.print("❌ 添加失败", style="red")
    
    def start_review(self):
        """开始复习"""
        review_words = self.core.get_words_for_review()
        
        if not review_words:
            self.console.print("🎉 暂无需要复习的单词！", style="green")
            return
        
        self.console.print(Rule("[bold]开始复习[/bold]"))
        self.console.print(f"📚 共有 {len(review_words)} 个单词需要复习\n")
        
        self.review_specific_words(review_words)
    
    def review_specific_words(self, words: List[Word]):
        """复习指定单词列表"""
        if not words:
            return
        
        reviewed = 0
        correct = 0
        
        for i, word in enumerate(words, 1):
            self.console.print(f"\n{'='*50}")
            self.console.print(f"复习进度: {i}/{len(words)}")
            self.console.print(f"{'='*50}")
            
            # 显示单词
            self.console.print(f"\n🔤 单词: [bold blue]{word.word}[/bold blue]")
            
            if word.core_info.pronunciation:
                self.console.print(f"🔊 发音: {word.core_info.pronunciation}")
            
            # 让用户思考
            input("\n💭 请回忆这个单词的含义，按回车查看答案...")
            
            # 显示答案
            self.console.print(f"\n📖 释义: [green]{word.core_info.primary_definition}[/green]")
            
            if word.extended_info.examples:
                self.console.print(f"📝 例句: {word.extended_info.examples[0]}")
            
            if word.notes:
                self.console.print("📝 笔记:")
                for note in word.notes[:2]:  # 显示前2个笔记
                    self.console.print(f"   💬 {note.get_simplified_display()}")
            
            # 评估掌握程度
            performance_options = [
                ("excellent", "😍 完全记住"),
                ("good", "😊 基本记住"),
                ("fair", "😐 模糊记得"),
                ("poor", "😵 完全忘记")
            ]
            
            self.console.print("\n评估你的掌握程度:")
            for key, desc in performance_options:
                self.console.print(f"  {key[0]}. {desc}")
            
            performance = Prompt.ask(
                "选择",
                choices=['e', 'g', 'f', 'p'],
                default=self.core.config.ui_defaults.review_performance_default
            )
            
            # 映射选择到性能评级
            perf_map = {'e': 'excellent', 'g': 'good', 'f': 'fair', 'p': 'poor'}
            performance_level = perf_map[performance]
            
            # 更新复习记录
            self.core.update_word_after_review(word.id, performance_level)
            
            reviewed += 1
            if performance in ['e', 'g']:
                correct += 1
            
            # 显示反馈
            if performance in ['e', 'g']:
                self.console.print("🎉 很棒！继续保持", style="green")
            else:
                self.console.print("💪 需要多复习，加油！", style="yellow")
            
            # 复习时添加笔记的选项
            if Confirm.ask("为这个单词添加学习笔记?", 
                          default=self.core.config.ui_defaults.confirm_add_note):
                self.add_note_during_review(word)
            
            # 询问是否继续
            if i < len(words):
                if not Confirm.ask("继续下一个?", 
                                 default=self.core.config.ui_defaults.confirm_continue_review):
                    break
        
        # 显示复习总结
        self.show_review_summary(reviewed, correct, len(words))
    
    def show_review_summary(self, reviewed: int, correct: int, total: int):
        """显示复习总结"""
        accuracy = (correct / reviewed * 100) if reviewed > 0 else 0
        
        summary = Table(title="📊 复习总结", box=box.ROUNDED)
        summary.add_column("项目", style="cyan")
        summary.add_column("数量", style="bold")
        
        summary.add_row("计划复习", str(total))
        summary.add_row("实际复习", str(reviewed))
        summary.add_row("掌握良好", str(correct))
        summary.add_row("正确率", f"{accuracy:.1f}%")
        
        self.console.print()
        self.console.print(summary)
        
        # 根据表现给出鼓励
        if accuracy >= 80:
            self.console.print("🌟 表现优秀！继续保持！", style="bold green")
        elif accuracy >= 60:
            self.console.print("👍 表现不错，再接再厉！", style="bold yellow")
        else:
            self.console.print("💪 需要多加练习，不要灰心！", style="bold red")
    
    def review_single_word(self, word: Word):
        """复习单个单词"""
        self.review_specific_words([word])
    
    def show_learning_statistics(self):
        """显示学习统计"""
        stats = self.core.get_statistics()
        
        self.console.print(Rule("[bold]学习统计报告[/bold]"))
        
        # 基本统计表格
        basic_table = Table(title="📊 基本信息", box=box.ROUNDED)
        basic_table.add_column("统计项", style="cyan")
        basic_table.add_column("数值", style="bold")
        
        basic_table.add_row("总单词数", str(stats['total_words']))
        basic_table.add_row("平均完整度", f"{stats['avg_completeness']:.1%}")
        basic_table.add_row("待复习数", str(stats['words_for_review']))
        basic_table.add_row("笔记总数", str(stats['notes_count']))
        
        if stats['last_added']:
            last_added = datetime.fromisoformat(stats['last_added'])
            basic_table.add_row("最近添加", last_added.strftime("%Y-%m-%d %H:%M"))
        
        # 状态分布表格
        status_table = Table(title="📈 状态分布", box=box.ROUNDED)
        status_table.add_column("状态", style="cyan")
        status_table.add_column("数量", style="bold")
        status_table.add_column("占比", style="dim")
        
        total = stats['total_words']
        for status, count in stats['by_status'].items():
            percentage = (count / total * 100) if total > 0 else 0
            icon = self.status_icons.get(WordStatus(status), "?")
            status_table.add_row(
                f"{icon} {status}",
                str(count),
                f"{percentage:.1f}%"
            )
        
        # 显示表格
        self.console.print()
        self.console.print(Columns([basic_table, status_table]))
        
        # 学习建议
        self.show_learning_suggestions(stats)
    
    def show_learning_suggestions(self, stats: Dict[str, Any]):
        """显示学习建议"""
        suggestions = []
        
        if stats['words_for_review'] > 0:
            suggestions.append(f"🔔 您有 {stats['words_for_review']} 个单词需要复习")
        
        draft_count = stats['by_status'].get('draft', 0)
        if draft_count > 0:
            suggestions.append(f"📝 有 {draft_count} 个单词信息不完整，建议补充")
        
        if stats['avg_completeness'] < 0.6:
            suggestions.append("📈 平均完整度较低，建议完善单词信息")
        
        mastered_count = stats['by_status'].get('mastered', 0)
        total = stats['total_words']
        if total > 0:
            mastery_rate = mastered_count / total
            if mastery_rate < 0.3:
                suggestions.append("🎯 掌握率较低，建议增加复习频率")
        
        if suggestions:
            self.console.print(Panel(
                "\n".join(f"• {s}" for s in suggestions),
                title="💡 学习建议",
                border_style="yellow"
            ))
    
    def display_word_list(self, words: List[Word], show_notes: bool = False):
        """显示单词列表"""
        if not words:
            self.console.print("📝 无单词", style="dim")
            return
        
        table = Table(box=box.MINIMAL)
        table.add_column("#", width=3)
        table.add_column("单词", style="bold")
        table.add_column("状态", width=8)
        table.add_column("释义")
        table.add_column("完整度", width=8)
        
        if show_notes:
            table.add_column("笔记", width=20)
        
        for i, word in enumerate(words, 1):
            icon = self.status_icons.get(word.status, "?")
            status_color = self.status_colors.get(word.status, "white")
            
            row_data = [
                str(i),
                word.word,
                f"[{status_color}]{icon}[/{status_color}]",
                word.core_info.primary_definition[:50] + "..." if len(word.core_info.primary_definition) > 50 else word.core_info.primary_definition,
                f"{word.completeness:.0%}"
            ]
            
            if show_notes:
                notes_preview = ""
                if word.notes:
                    notes_preview = word.notes[0].get_simplified_display(30)
                row_data.append(notes_preview)
            
            table.add_row(*row_data)
        
        self.console.print(table)
    
    def display_word_brief_list(self, words: List[Word]):
        """显示单词简要列表"""
        if not words:
            return
        
        for word in words:
            icon = self.status_icons.get(word.status, "?")
            color = self.status_colors.get(word.status, "white")
            self.console.print(
                f"  {icon} [{color}]{word.word}[/{color}] - {word.core_info.primary_definition}"
            )
    
    def display_word_detail(self, word: Word):
        """显示单词详细信息"""
        # 创建主要信息面板
        content_parts = []
        
        # 基本信息
        content_parts.append(f"🔤 [bold blue]{word.word}[/bold blue]")
        
        if word.core_info.pronunciation:
            content_parts.append(f"🔊 {word.core_info.pronunciation}")
        
        if word.core_info.part_of_speech:
            content_parts.append(f"📝 {word.core_info.part_of_speech}")
        
        content_parts.append(f"📖 {word.core_info.primary_definition}")
        
        # 扩展信息
        if word.extended_info.examples:
            content_parts.append("\n📚 例句:")
            for example in word.extended_info.examples[:3]:
                content_parts.append(f"   • {example}")
        
        if word.extended_info.synonyms:
            content_parts.append(f"\n🔗 同义词: {', '.join(word.extended_info.synonyms)}")
        
        # 标签
        if word.tags:
            tags_text = " ".join(f"[dim]#{tag}[/dim]" for tag in word.tags)
            content_parts.append(f"\n🏷️  {tags_text}")
        
        # 笔记
        if word.notes:
            content_parts.append("\n💬 笔记:")
            for note in word.notes:
                content_parts.append(f"   📝 {note.get_full_display()}")
        
        # 学习数据
        status_icon = self.status_icons.get(word.status, "?")
        status_color = self.status_colors.get(word.status, "white")
        
        learning_info = (
            f"📊 状态: [{status_color}]{status_icon} {word.status.value}[/{status_color}] | "
            f"完整度: {word.completeness:.1%} | "
            f"复习: {word.learning_data.review_count}次"
        )
        content_parts.append(f"\n{learning_info}")
        
        # 显示面板
        panel_content = "\n".join(content_parts)
        self.console.print(Panel(
            panel_content,
            title=f"📖 {word.word}",
            border_style=self.status_colors.get(word.status, "white")
        ))
    
    def edit_word_info(self, word: Word):
        """编辑单词信息"""
        self.console.print(f"✏️ 编辑 '[bold]{word.word}[/bold]' (留空保持原值)")
        
        # 编辑核心信息
        new_def = Prompt.ask("主要释义", default=word.core_info.primary_definition)
        if new_def != word.core_info.primary_definition:
            word.core_info.primary_definition = new_def
        
        new_pronunciation = Prompt.ask("发音", default=word.core_info.pronunciation)
        if new_pronunciation != word.core_info.pronunciation:
            word.core_info.pronunciation = new_pronunciation
        
        new_pos = Prompt.ask("词性", default=word.core_info.part_of_speech)
        if new_pos != word.core_info.part_of_speech:
            word.core_info.part_of_speech = new_pos
        
        # 更新完整度
        word.calculate_completeness()
        self.console.print("✅ 更新成功", style="green")
    
    def manage_word_tags(self, word: Word):
        """管理单词标签"""
        current_tags = ", ".join(word.tags) if word.tags else "无标签"
        self.console.print(f"当前标签: {current_tags}")
        
        action = Prompt.ask(
            "选择操作",
            choices=["add", "remove", "replace", "back"],
            default="back"
        )
        
        if action == "add":
            new_tags = Prompt.ask("添加标签 (逗号分隔)")
            tags_to_add = [t.strip() for t in new_tags.split(',') if t.strip()]
            word.tags.extend(tags_to_add)
            word.tags = list(set(word.tags))  # 去重
            self.console.print("✅ 标签已添加", style="green")
        
        elif action == "replace":
            new_tags = Prompt.ask("新标签 (逗号分隔)")
            word.tags = [t.strip() for t in new_tags.split(',') if t.strip()]
            self.console.print("✅ 标签已替换", style="green")
    
    def show_word_learning_history(self, word: Word):
        """显示单词学习历史"""
        history_table = Table(title=f"📊 {word.word} 学习记录", box=box.ROUNDED)
        history_table.add_column("项目", style="cyan")
        history_table.add_column("值", style="bold")
        
        history_table.add_row("添加时间", word.learning_data.added_date[:19])
        history_table.add_row("复习次数", str(word.learning_data.review_count))
        history_table.add_row("正确次数", str(word.learning_data.correct_count))
        
        if word.learning_data.review_count > 0:
            accuracy = word.learning_data.correct_count / word.learning_data.review_count * 100
            history_table.add_row("正确率", f"{accuracy:.1f}%")
        
        if word.learning_data.last_reviewed:
            history_table.add_row("上次复习", word.learning_data.last_reviewed[:19])
        
        if word.learning_data.next_review:
            history_table.add_row("下次复习", word.learning_data.next_review[:19])
        
        self.console.print(history_table)
    
    def delete_single_word(self, word: Word):
        """删除单个单词"""
        self.console.print(f"\n⚠️  删除单词: [bold red]{word.word}[/bold red]")
        self.console.print("此操作将永久删除该单词及其所有相关数据（笔记、学习记录等）")
        
        # 显示单词信息供确认
        self.console.print(f"释义: {word.core_info.primary_definition}")
        if word.notes:
            self.console.print(f"笔记数量: {len(word.notes)}")
        self.console.print(f"复习次数: {word.learning_data.review_count}")
        
        if Confirm.ask("确认删除这个单词?", 
                      default=self.core.config.ui_defaults.confirm_delete):
            if self.core.delete_word(word.id):
                self.console.print("✅ 单词删除成功", style="green")
            else:
                self.console.print("❌ 删除失败", style="red")
        else:
            self.console.print("❌ 取消删除", style="yellow")
    
    def data_management(self):
        """数据管理"""
        self.console.print(Rule("[bold]数据管理[/bold]"))
        
        actions = [
            ("1", "💾 手动保存"),
            ("2", "📦 创建备份"),
            ("3", "📊 数据统计"),
            ("4", "🔧 配置设置"),
            ("5", "◀️ 返回")
        ]
        
        for key, desc in actions:
            self.console.print(f"  {key}. {desc}")
        
        choice = Prompt.ask("选择操作", choices=[a[0] for a in actions], default="5")
        
        if choice == "1":
            self.manual_save()
        elif choice == "2":
            self.create_backup()
        elif choice == "3":
            self.show_data_statistics()
        elif choice == "4":
            self.manage_settings()
    
    def manual_save(self):
        """手动保存"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("正在保存数据...", total=None)
            success = self.core.save_data(force=True)
            time.sleep(0.5)
            progress.update(task, completed=True)
        
        if success:
            self.console.print("✅ 数据保存成功", style="green")
        else:
            self.console.print("❌ 数据保存失败", style="red")
    
    def create_backup(self):
        """创建备份"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("正在创建备份...", total=None)
            success = self.core.storage.backup()
            time.sleep(0.8)
            progress.update(task, completed=True)
        
        if success:
            self.console.print("✅ 备份创建成功", style="green")
        else:
            self.console.print("❌ 备份创建失败", style="red")
    
    def show_data_statistics(self):
        """显示数据统计"""
        stats = self.core.get_statistics()
        
        # 文件信息
        file_info = Table(title="📁 文件信息", box=box.ROUNDED)
        file_info.add_column("项目", style="cyan")
        file_info.add_column("信息", style="bold")
        
        data_file = self.core.config.data_file
        if os.path.exists(data_file):
            file_size = os.path.getsize(data_file) / 1024  # KB
            mod_time = datetime.fromtimestamp(os.path.getmtime(data_file))
            
            file_info.add_row("数据文件", data_file)
            file_info.add_row("文件大小", f"{file_size:.1f} KB")
            file_info.add_row("修改时间", mod_time.strftime("%Y-%m-%d %H:%M:%S"))
            file_info.add_row("自动保存", "开启" if self.core.config.auto_save else "关闭")
        
        self.console.print(file_info)
    
    def manage_settings(self):
        """管理设置"""
        self.console.print("⚙️ 配置管理")
        config = self.core.config
        
        # 显示配置分类
        settings_categories = [
            ("1", "基本设置", "自动保存、备份等基本配置"),
            ("2", "添加单词设置", "添加单词时的默认行为"),
            ("3", "UI默认值设置", "各种选择项的默认值"),
            ("4", "学习算法设置", "间隔重复等学习相关配置"),
            ("5", "返回主菜单", "返回主菜单")
        ]
        
        self.console.print("选择配置类别:")
        for key, title, desc in settings_categories:
            self.console.print(f"  {key}. {title} - {desc}")
        
        choice = Prompt.ask("选择配置类别", choices=[c[0] for c in settings_categories], default="5")
        
        if choice == "1":
            self.show_basic_settings()
        elif choice == "2":
            self.show_add_word_settings()
        elif choice == "3":
            self.show_ui_defaults_settings()
        elif choice == "4":
            self.show_learning_settings()
        elif choice == "5":
            return
    
    def show_basic_settings(self):
        """显示基本设置"""
        config = self.core.config
        
        settings_table = Table(title="基本设置", box=box.ROUNDED)
        settings_table.add_column("设置项", style="cyan")
        settings_table.add_column("当前值", style="bold")
        settings_table.add_column("说明", style="dim")
        
        settings_table.add_row("自动保存", str(config.auto_save), "是否自动保存数据")
        settings_table.add_row("保存间隔", f"{config.auto_save_interval}秒", "自动保存间隔")
        settings_table.add_row("备份功能", str(config.backup_enabled), "是否启用备份")
        settings_table.add_row("备份数量", str(config.backup_count), "保留的备份文件数")
        settings_table.add_row("掌握阈值", f"{config.mastery_threshold:.1%}", "判断掌握的正确率")
        
        self.console.print(settings_table)
        
        if Confirm.ask("修改基本设置?", default=False):
            self.edit_basic_settings()
    
    def show_add_word_settings(self):
        """显示添加单词设置"""
        config = self.core.config.add_word_config
        
        settings_table = Table(title="添加单词设置", box=box.ROUNDED)
        settings_table.add_column("设置项", style="cyan")
        settings_table.add_column("当前值", style="bold")
        settings_table.add_column("说明", style="dim")
        
        settings_table.add_row("跳过发音", str(config.skip_pronunciation), "添加单词时跳过发音输入")
        settings_table.add_row("跳过词性", str(config.skip_part_of_speech), "添加单词时跳过词性输入")
        settings_table.add_row("跳过语境", str(config.skip_context), "添加单词时跳过语境输入")
        settings_table.add_row("跳过标签", str(config.skip_tags), "添加单词时跳过标签输入")
        settings_table.add_row("自动提升状态", str(config.auto_promote_to_learning), "有定义时自动提升为learning状态")
        settings_table.add_row("默认标签", ", ".join(config.default_tags) or "无", "添加单词时的默认标签")
        
        self.console.print(settings_table)
        
        if Confirm.ask("修改添加单词设置?", default=False):
            self.edit_add_word_settings()
    
    def show_ui_defaults_settings(self):
        """显示UI默认值设置"""
        config = self.core.config.ui_defaults
        
        settings_table = Table(title="UI默认值设置", box=box.ROUNDED)
        settings_table.add_column("设置项", style="cyan")
        settings_table.add_column("当前值", style="bold")
        settings_table.add_column("说明", style="dim")
        
        settings_table.add_row("主菜单默认", config.main_menu_default, "主菜单的默认选择")
        settings_table.add_row("复习表现默认", config.review_performance_default, "复习时的默认表现评级")
        settings_table.add_row("词汇表排序默认", config.vocabulary_sort_default, "词汇表管理的默认排序")
        settings_table.add_row("批量编辑默认", config.batch_edit_default, "批量编辑的默认操作")
        settings_table.add_row("笔记类型默认", config.note_type_default, "笔记类型的默认选择")
        settings_table.add_row("继续复习确认", str(config.confirm_continue_review), "复习时继续的默认确认")
        settings_table.add_row("添加笔记确认", str(config.confirm_add_note), "添加笔记的默认确认")
        settings_table.add_row("批量编辑确认", str(config.confirm_batch_edit), "批量编辑的默认确认")
        settings_table.add_row("删除确认", str(config.confirm_delete), "删除操作的默认确认")
        
        self.console.print(settings_table)
        
        if Confirm.ask("修改UI默认值设置?", default=False):
            self.edit_ui_defaults_settings()
    
    def show_learning_settings(self):
        """显示学习算法设置"""
        config = self.core.config
        
        settings_table = Table(title="学习算法设置", box=box.ROUNDED)
        settings_table.add_column("设置项", style="cyan")
        settings_table.add_column("当前值", style="bold")
        settings_table.add_column("说明", style="dim")
        
        settings_table.add_row("掌握阈值", f"{config.mastery_threshold:.1%}", "判断掌握的正确率")
        settings_table.add_row("掌握复习次数", str(config.mastery_review_count), "达到掌握需要的复习次数")
        settings_table.add_row("最大间隔天数", str(config.max_interval_days), "复习间隔的最大天数")
        settings_table.add_row("优秀间隔", f"{config.sr_base_intervals['excellent']}天", "优秀表现的复习间隔")
        settings_table.add_row("良好间隔", f"{config.sr_base_intervals['good']}天", "良好表现的复习间隔")
        settings_table.add_row("一般间隔", f"{config.sr_base_intervals['fair']}天", "一般表现的复习间隔")
        settings_table.add_row("较差间隔", f"{config.sr_base_intervals['poor']}天", "较差表现的复习间隔")
        
        self.console.print(settings_table)
        
        if Confirm.ask("修改学习算法设置?", default=False):
            self.edit_learning_settings()
    
    def edit_basic_settings(self):
        """编辑基本设置"""
        config = self.core.config
        
        # 自动保存设置
        config.auto_save = Confirm.ask("启用自动保存?", default=config.auto_save)
        
        if config.auto_save:
            new_interval = IntPrompt.ask(
                "自动保存间隔(秒)",
                default=config.auto_save_interval,
                show_default=True
            )
            config.auto_save_interval = max(60, new_interval)  # 最少1分钟
        
        # 备份设置
        config.backup_enabled = Confirm.ask("启用备份功能?", default=config.backup_enabled)
        
        if config.backup_enabled:
            config.backup_count = IntPrompt.ask(
                "保留备份数量",
                default=config.backup_count,
                show_default=True
            )
        
        # 学习设置
        mastery_percent = int(config.mastery_threshold * 100)
        new_mastery = IntPrompt.ask(
            "掌握阈值(%)",
            default=mastery_percent,
            show_default=True
        )
        config.mastery_threshold = max(50, min(100, new_mastery)) / 100
        
        # 保存配置
        config.save()
        self.console.print("✅ 基本设置已保存", style="green")
        
        # 重启自动保存
        if config.auto_save:
            self.core._start_auto_save()
    
    def edit_add_word_settings(self):
        """编辑添加单词设置"""
        config = self.core.config.add_word_config
        
        # 跳过选项
        config.skip_pronunciation = Confirm.ask("跳过发音输入?", default=config.skip_pronunciation)
        config.skip_part_of_speech = Confirm.ask("跳过词性输入?", default=config.skip_part_of_speech)
        config.skip_context = Confirm.ask("跳过语境输入?", default=config.skip_context)
        config.skip_tags = Confirm.ask("跳过标签输入?", default=config.skip_tags)
        config.auto_promote_to_learning = Confirm.ask("有定义时自动提升为learning状态?", 
                                                     default=config.auto_promote_to_learning)
        
        # 默认标签
        current_tags = ", ".join(config.default_tags) if config.default_tags else ""
        new_tags = Prompt.ask("默认标签 (逗号分隔)", default=current_tags)
        if new_tags.strip():
            config.default_tags = [t.strip() for t in new_tags.split(',') if t.strip()]
        else:
            config.default_tags = []
        
        # 保存配置
        self.core.config.save()
        self.console.print("✅ 添加单词设置已保存", style="green")
    
    def edit_ui_defaults_settings(self):
        """编辑UI默认值设置"""
        config = self.core.config.ui_defaults
        
        # 主菜单默认
        config.main_menu_default = Prompt.ask("主菜单默认选择 (1-9)", 
                                             default=config.main_menu_default)
        
        # 复习表现默认
        performance_options = ["e", "g", "f", "p"]
        config.review_performance_default = Prompt.ask("复习表现默认 (e/g/f/p)", 
                                                      choices=performance_options,
                                                      default=config.review_performance_default)
        
        # 词汇表排序默认
        sort_options = ["1", "2", "3", "4", "5", "6"]
        config.vocabulary_sort_default = Prompt.ask("词汇表排序默认 (1-6)", 
                                                   choices=sort_options,
                                                   default=config.vocabulary_sort_default)
        
        # 批量编辑默认
        batch_options = ["1", "2", "3", "4"]
        config.batch_edit_default = Prompt.ask("批量编辑默认 (1-4)", 
                                              choices=batch_options,
                                              default=config.batch_edit_default)
        
        # 笔记类型默认
        note_options = ["1", "2", "3", "4", "5"]
        config.note_type_default = Prompt.ask("笔记类型默认 (1-5)", 
                                             choices=note_options,
                                             default=config.note_type_default)
        
        # 确认操作默认值
        config.confirm_continue_review = Confirm.ask("复习时继续的默认确认?", 
                                                    default=config.confirm_continue_review)
        config.confirm_add_note = Confirm.ask("添加笔记的默认确认?", 
                                             default=config.confirm_add_note)
        config.confirm_batch_edit = Confirm.ask("批量编辑的默认确认?", 
                                               default=config.confirm_batch_edit)
        config.confirm_delete = Confirm.ask("删除操作的默认确认?", 
                                           default=config.confirm_delete)
        
        # 保存配置
        self.core.config.save()
        self.console.print("✅ UI默认值设置已保存", style="green")
    
    def edit_learning_settings(self):
        """编辑学习算法设置"""
        config = self.core.config
        
        # 掌握阈值
        mastery_percent = int(config.mastery_threshold * 100)
        new_mastery = IntPrompt.ask(
            "掌握阈值(%)",
            default=mastery_percent,
            show_default=True
        )
        config.mastery_threshold = max(50, min(100, new_mastery)) / 100
        
        # 掌握复习次数
        config.mastery_review_count = IntPrompt.ask(
            "掌握复习次数",
            default=config.mastery_review_count,
            show_default=True
        )
        
        # 最大间隔天数
        config.max_interval_days = IntPrompt.ask(
            "最大间隔天数",
            default=config.max_interval_days,
            show_default=True
        )
        
        # 间隔重复设置
        self.console.print("间隔重复设置:")
        config.sr_base_intervals['excellent'] = IntPrompt.ask(
            "优秀表现间隔(天)",
            default=int(config.sr_base_intervals['excellent']),
            show_default=True
        )
        config.sr_base_intervals['good'] = IntPrompt.ask(
            "良好表现间隔(天)",
            default=int(config.sr_base_intervals['good']),
            show_default=True
        )
        config.sr_base_intervals['fair'] = IntPrompt.ask(
            "一般表现间隔(天)",
            default=int(config.sr_base_intervals['fair']),
            show_default=True
        )
        config.sr_base_intervals['poor'] = IntPrompt.ask(
            "较差表现间隔(天)",
            default=int(config.sr_base_intervals['poor']),
            show_default=True
        )
        
        # 保存配置
        config.save()
        self.console.print("✅ 学习算法设置已保存", style="green")
    
    def run(self):
        """运行主程序"""
        self.console.clear()
        self.display_header()
        
        try:
            while True:
                self.display_main_menu()
                
                choice = Prompt.ask(
                    "\n🎯 请选择功能",
                    choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                    default=self.core.config.ui_defaults.main_menu_default
                )
                
                try:
                    if choice == "1":
                        self.quick_add_word()
                    elif choice == "2":
                        self.batch_input_session()
                    elif choice == "3":
                        self.start_review()
                    elif choice == "4":
                        self.search_words()
                    elif choice == "5":
                        self.show_learning_statistics()
                    elif choice == "6":
                        self.data_management()
                    elif choice == "7":
                        self.vocabulary_management()
                    elif choice == "8":
                        self.manage_settings()
                    elif choice == "9":
                        break
                
                except KeyboardInterrupt:
                    self.console.print("\n⏸️  操作中断", style="yellow")
                    continue
                except Exception as e:
                    self.console.print(f"\n❌ 发生错误: {e}", style="red")
                    if Confirm.ask("查看详细错误信息?", default=False):
                        self.console.print_exception()
        
        except KeyboardInterrupt:
            pass
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理和退出"""
        self.console.print("\n👋 正在保存数据并退出...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("清理中...", total=None)
            
            # 保存数据
            self.core.save_data(force=True)
            time.sleep(0.5)
            
            # 清理核心资源
            self.core.cleanup()
            time.sleep(0.3)
            
            progress.update(task, completed=True)
        
        stats = self.core.get_statistics()
        
        # 显示告别信息
        farewell_panel = Panel(
            f"📚 本次会话统计\n\n"
            f"• 词汇总数: {stats['total_words']}\n"
            f"• 待复习: {stats['words_for_review']}\n"
            f"• 平均完整度: {stats['avg_completeness']:.1%}\n\n",
            title="🎓 学习总结",
            border_style="green"
        )
        
        self.console.print(farewell_panel)


def main():
    """主函数"""
    try:
        app = RichCliUI()
        app.run()
    except Exception as e:
        console = Console()
        console.print(f"❌ 程序启动失败: {e}", style="red")
        console.print_exception()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())