import os
import re

def check_paths(file_path):
    """检查HTML文件中的相对路径"""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查相对路径引用
            if re.search(r'(src|href)=["\']\.\./', line):
                issues.append(f"第{i}行: 使用了相对路径 '../'")
            
            # 检查本地资源引用（非CDN）
            matches = re.findall(r'(src|href)=["\']((?!https?://)[^"\']+)["\']', line)
            for attr, path in matches:
                if path.startswith('../') or (not path.startswith('/') and not path.startswith('#')):
                    issues.append(f"第{i}行: {attr}='{path}' 应改为绝对路径")
    
    return issues

# 检查所有HTML文件
html_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

print("=" * 80)
print("HTML文件路径检查")
print("=" * 80)

for file in html_files:
    issues = check_paths(file)
    if issues:
        print(f"\n文件: {file}")
        print("-" * 80)
        for issue in issues[:5]:  # 只显示前5个问题
            print(f"  ⚠ {issue}")
        if len(issues) > 5:
            print(f"  ... 还有 {len(issues) - 5} 个问题")
    else:
        print(f"\n✓ {file} - 路径正确")

print("\n" + "=" * 80)
print("建议: 所有本地资源应使用绝对路径，如 /page/xxx 或 /image/xxx")
print("=" * 80)
