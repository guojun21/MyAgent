"""
工具执行器 - 负责执行单个工具调用
"""
from typing import Dict, Any
import json
import ast
import re
from utils.logger import safe_print as print

class ToolExecutor:
    """负责解析和执行工具调用"""
    
    def __init__(self, tool_manager):
        self.tool_manager = tool_manager

    async def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具调用"""
        function_name = tool_call["function"]["name"]
        
        print(f"    [_execute_tool_call] 准备执行工具: {function_name}")
        
        try:
            # 解析参数（尝试多种方式）
            args_str = tool_call["function"]["arguments"]
            print(f"    [_execute_tool_call] 参数字符串长度: {len(args_str)}")
            
            try:
                # 方法1: 标准JSON解析
                arguments = json.loads(args_str)
            except json.JSONDecodeError as e1:
                print(f"    [_execute_tool_call] 标准解析失败: {e1}")
                print(f"    [_execute_tool_call] 参数内容前200字符: {args_str[:200]}")
                
                try:
                    # 方法2: 修复常见问题
                    fixed_str = args_str
                    
                    # 修复单引号（DeepSeek常见问题）
                    # 将JSON中的单引号替换为双引号
                    # 匹配键名的单引号
                    fixed_str = re.sub(r"'([a-zA-Z_][a-zA-Z0-9_]*)':", r'"\1":', fixed_str)
                    # 匹配值的单引号
                    fixed_str = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_str)
                    
                    # 修复转义符
                    fixed_str = fixed_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    
                    arguments = json.loads(fixed_str)
                    print(f"    [_execute_tool_call] ✅ 修复后解析成功")
                except Exception as e2:
                    print(f"    [_execute_tool_call] 修复后解析仍失败: {e2}")
                    
                    try:
                        # 方法3: 使用ast.literal_eval（Python字面量）
                        arguments = ast.literal_eval(args_str)
                        print(f"    [_execute_tool_call] ✅ Python字面量解析成功")
                    except Exception as e3:
                        print(f"    [_execute_tool_call] 所有方法都失败: {e3}")
                        
                        # 返回详细错误给LLM，让它自己修正
                        error_msg = f"""参数格式错误，请重新生成。

错误详情：
{str(e1)}

你的参数（前200字符）：
{args_str[:200]}

请注意：
1. 使用双引号 " 而不是单引号 '
2. 键名必须用双引号包裹
3. 字符串值也用双引号
4. 确保JSON格式完整

请立即重新调用工具，使用正确的JSON格式。"""
                        
                        return {
                            "success": False,
                            "error": error_msg
                        }
            
            print(f"    [_execute_tool_call] ✅ 参数解析成功，keys: {list(arguments.keys())}")
        except Exception as e:
            print(f"    [_execute_tool_call] 严重错误: {e}")
            return {
                "success": False,
                "error": f"参数处理失败: {str(e)}"
            }
        
        # 执行工具
        print(f"    [_execute_tool_call] 调用 ToolManager.execute_tool()")
        result = self.tool_manager.execute_tool(function_name, arguments)
        print(f"    [_execute_tool_call] 工具执行完成: success={result.get('success', False)}")
        
        return result

