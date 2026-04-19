"""
Check if LabelImg process is running
"""
import sys
import subprocess
import time

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

print("检查 LabelImg 进程...")
print("=" * 60)

# Check for running processes
try:
    result = subprocess.run(
        ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
        capture_output=True,
        text=True,
        encoding='gbk',
        errors='ignore'
    )
    
    if 'python.exe' in result.stdout:
        print("发现 Python 进程:")
        lines = result.stdout.split('\n')
        for line in lines:
            if 'python.exe' in line:
                print(f"  {line}")
    else:
        print("未发现 Python 进程")
        
except Exception as e:
    print(f"检查进程失败: {e}")

print("\n提示:")
print("1. 如果 LabelImg 窗口没有显示，检查任务栏")
print("2. 检查任务管理器中的 python.exe 进程")
print("3. 尝试 Alt+Tab 切换窗口")
print("4. 检查是否有多个显示器")






