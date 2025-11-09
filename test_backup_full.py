#!/usr/bin/env python
"""完整測試備份功能，包括下載和刪除"""
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.utils.backup_service import BackupService

def test_backup_full():
    """完整測試備份功能"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("完整備份功能測試")
        print("=" * 70)
        
        # 測試1: 建立多個備份
        print("\n[測試 1] 建立多個備份...")
        backup_ids = []
        for i in range(3):
            backup = BackupService.create_backup(
                backup_type='manual' if i > 0 else 'auto',
                description=f'Test Backup #{i+1}',
                created_by=None
            )
            if backup:
                backup_ids.append(backup.id)
                print(f"   ✓ 備份 {i+1}: {backup.filename} ({backup.get_display_size()})")
            else:
                print(f"   ✗ 備份 {i+1} 建立失敗")
                return False
        
        # 測試2: 列出所有備份
        print("\n[測試 2] 列出所有備份...")
        backups = BackupService.get_backup_list()
        print(f"   ✓ 總備份數: {len(backups)}")
        for b in backups:
            print(f"     - {b.filename} | 類型: {b.backup_type} | 大小: {b.get_display_size()}")
        
        # 測試3: 取得指定備份
        print("\n[測試 3] 取得指定備份...")
        first_backup = BackupService.get_backup_by_id(backup_ids[0])
        if first_backup:
            print(f"   ✓ 找到備份: {first_backup.filename}")
            print(f"     檔案存在: {Path(first_backup.filepath).exists()}")
        else:
            print("   ✗ 無法找到備份")
        
        # 測試4: 備份統計
        print("\n[測試 4] 備份統計...")
        stats = BackupService.get_backup_stats()
        print(f"   ✓ 總備份數: {stats['total_backups']}")
        print(f"   ✓ 自動備份: {stats['auto_backups']}")
        print(f"   ✓ 手動備份: {stats['manual_backups']}")
        print(f"   ✓ 總容量: {stats['total_size_formatted']}")
        if stats['oldest_backup']:
            print(f"   ✓ 最舊備份: {stats['oldest_backup']}")
        if stats['newest_backup']:
            print(f"   ✓ 最新備份: {stats['newest_backup']}")
        
        # 測試5: 刪除指定備份
        print("\n[測試 5] 刪除指定備份...")
        delete_id = backup_ids[1]
        success = BackupService.delete_backup(delete_id)
        if success:
            print(f"   ✓ 已刪除 ID {delete_id} 的備份")
        else:
            print(f"   ✗ 刪除失敗")
            return False
        
        # 測試6: 驗證刪除
        print("\n[測試 6] 驗證刪除...")
        remaining_backups = BackupService.get_backup_list()
        print(f"   ✓ 剩餘備份數: {len(remaining_backups)}")
        if BackupService.get_backup_by_id(delete_id) is None:
            print("   ✓ 已刪除的備份確實不存在")
        else:
            print("   ✗ 刪除失敗，備份仍然存在")
        
        # 測試7: 測試保留天數清理
        print("\n[測試 7] 測試保留天數清理 (retention_days=365)...")
        count = BackupService.cleanup_old_backups(retention_days=365)
        print(f"   ✓ 清理了 {count} 個備份（應為 0，因為備份都很新）")
        
        final_count = len(BackupService.get_backup_list())
        print(f"   ✓ 最終備份數: {final_count}")
        
        # 測試8: 清理所有老備份
        print("\n[測試 8] 清理所有老備份 (retention_days=0)...")
        count = BackupService.cleanup_old_backups(retention_days=0)
        print(f"   ✓ 清理了 {count} 個備份")
        
        final_backups = BackupService.get_backup_list()
        print(f"   ✓ 清理後備份數: {len(final_backups)}")
        
        print("\n" + "=" * 70)
        print("✓ 所有測試完成!")
        print("=" * 70)
        return True

if __name__ == '__main__':
    success = test_backup_full()
    sys.exit(0 if success else 1)
