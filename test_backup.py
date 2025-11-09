#!/usr/bin/env python
"""測試備份功能"""
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.utils.backup_service import BackupService

def test_backup():
    """測試備份功能"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("備份功能測試")
        print("=" * 60)
        
        # 測試建立備份
        print("\n1. 測試建立備份...")
        backup = BackupService.create_backup(
            backup_type='manual',
            description='Test Backup',
            created_by=None
        )
        
        if backup:
            print(f"   ✓ 備份已建立: {backup.filename}")
            print(f"   ✓ 檔案大小: {backup.get_display_size()}")
            print(f"   ✓ 檔案路徑: {backup.filepath}")
        else:
            print("   ✗ 備份建立失敗")
            return False
        
        # 測試列出備份
        print("\n2. 測試列出備份...")
        backups = BackupService.get_backup_list()
        print(f"   ✓ 找到 {len(backups)} 個備份")
        for b in backups:
            print(f"     - {b.filename} ({b.get_display_size()}, {b.backup_type})")
        
        # 測試備份統計
        print("\n3. 測試備份統計...")
        stats = BackupService.get_backup_stats()
        print(f"   ✓ 總備份數: {stats['total_backups']}")
        print(f"   ✓ 自動備份: {stats['auto_backups']}")
        print(f"   ✓ 手動備份: {stats['manual_backups']}")
        print(f"   ✓ 總容量: {stats['total_size_formatted']}")
        
        # 測試清理舊備份
        print("\n4. 測試清理舊備份...")
        count = BackupService.cleanup_old_backups(retention_days=0)
        print(f"   ✓ 清理了 {count} 個備份")
        
        # 測試列出備份後清理
        print("\n5. 測試清理後的備份列表...")
        backups = BackupService.get_backup_list()
        print(f"   ✓ 剩餘備份數: {len(backups)}")
        
        print("\n" + "=" * 60)
        print("所有測試完成!")
        print("=" * 60)
        return True

if __name__ == '__main__':
    success = test_backup()
    sys.exit(0 if success else 1)
