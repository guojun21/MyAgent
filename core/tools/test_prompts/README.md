# 🧪 工具测试Prompt

每个工具对应一个JSON文件，包含4-5个测试用例。

## 📁 文件列表

- `read_file_prompts.json` - 读取文件测试
- `write_file_prompts.json` - 写入文件测试
- `edit_file_prompts.json` - 编辑文件测试
- `list_files_prompts.json` - 列出文件测试
- `search_code_prompts.json` - 搜索代码测试
- `get_project_structure_prompts.json` - 项目结构测试
- `run_terminal_prompts.json` - 终端命令测试
- `analyze_imports_prompts.json` - 导入分析测试

## 📊 JSON格式

```json
{
  "tool": "工具名",
  "prompts": [
    {
      "id": 1,
      "description": "测试说明",
      "prompt": "实际的测试提示词"
    }
  ]
}
```

## 🚀 使用方式

1. 在测试Tab中导入这些prompt
2. 按工具分类运行测试
3. 验证工具功能是否正常

## 📝 添加新测试

编辑对应的JSON文件，按格式添加新的测试用例即可。

