"""
Launch LabelImg - Final version
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

print("正在启动 LabelImg...")
print("=" * 60)

# Method 1: Direct import and run
try:
    # Ensure we're using the right path
    import labelImg
    labelImg_dir = os.path.dirname(labelImg.__file__)
    
    # Add to path
    if labelImg_dir not in sys.path:
        sys.path.insert(0, labelImg_dir)
    if os.path.dirname(labelImg_dir) not in sys.path:
        sys.path.insert(0, os.path.dirname(labelImg_dir))
    
    # Import and run
    from labelImg.labelImg import main
    
    # Set up sys.argv
    if len(sys.argv) == 1:
        sys.argv = ['labelImg']
    
    print("使用导入方式启动...")
    main()
    
except Exception as e:
    print(f"导入方式失败: {e}")
    print("\n尝试直接执行文件...")
    
    try:
        import labelImg
        labelImg_dir = os.path.dirname(labelImg.__file__)
        labelImg_py = os.path.join(labelImg_dir, 'labelImg.py')
        
        if not os.path.exists(labelImg_py):
            raise FileNotFoundError(f"找不到 labelImg.py: {labelImg_py}")
        
        # Change to labelImg directory
        original_dir = os.getcwd()
        os.chdir(labelImg_dir)
        
        try:
            # Add paths
            sys.path.insert(0, labelImg_dir)
            sys.path.insert(0, os.path.dirname(labelImg_dir))
            
            # Read and execute
            with open(labelImg_py, 'r', encoding='utf-8', errors='ignore') as f:
                code = compile(f.read(), labelImg_py, 'exec')
            
            # Execute with proper namespace
            exec(code, {
                '__name__': '__main__',
                '__file__': labelImg_py,
                '__package__': 'labelImg',
            })
        finally:
            os.chdir(original_dir)
            
    except Exception as e2:
        print(f"直接执行也失败: {e2}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("启动失败！")
        print("\n建议:")
        print("1. 检查 PyQt5 是否正确安装")
        print("2. 尝试重新安装: pip uninstall labelImg -y && pip install labelImg")
        print("3. 检查是否有杀毒软件阻止")
        print("4. 尝试以管理员身份运行")
        sys.exit(1)






