#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Git提交日期重写脚本
使用git命令逐个修改提交日期
"""
import subprocess
import sys

# 提交哈希到新日期的映射
commit_dates = {
    "e8280b2a568a483ed9e971dddc46b1efb96a0858": "Fri Aug 01 10:00:00 2025 +0800",
    "a5cf77df8e50f8ee4cd759e9449c821d75bc9f65": "Fri Aug 01 13:26:54 2025 +0800",
    "300b4119143d1d7afba0375de8881b93f39652a4": "Mon Aug 04 21:34:35 2025 +0800",
    "9879d43e4e483ed5b0db35bc233979415bdeb636": "Tue Aug 05 13:49:12 2025 +0800",
    "1e160fab246873f52db2b6d4be4380f9e02757e3": "Wed Aug 06 19:33:20 2025 +0800",
    "e798d77a27c891d5701327d0b8453dcef864e757": "Thu Aug 07 11:41:09 2025 +0800",
    "bbf167ee7e45f78423cf69f3bf740f015287c823": "Thu Aug 07 18:08:33 2025 +0800",
    "d3b61bab78a414884a4971b7da49d6fc83327b04": "Fri Aug 08 17:11:12 2025 +0800",
    "92edc22dd35582dc462857b0f0b4ebe46b85f2e9": "Mon Aug 11 17:50:09 2025 +0800",
    "7ec76c735981d04519f0b15339d8fc8a78e15637": "Wed Aug 13 16:22:26 2025 +0800",
    "098364ef613e16127be2efef0e7f712d57e90014": "Thu Aug 14 15:38:53 2025 +0800",
    "f380153b214fc399fbe788e877d4fd6904179a3a": "Sat Aug 16 16:51:52 2025 +0800",
    "6a00f465a1a24398af9ecafd28e586f9331f3d36": "Tue Aug 19 21:47:41 2025 +0800",
    "4485410a0ec8dc1aaace756dd1ed021a1a34c5f2": "Wed Aug 20 09:44:28 2025 +0800",
    "b70602d1ccb1a1d8158d893d1a50d743abcb198d": "Thu Aug 21 19:36:22 2025 +0800",
    "ead2aee2a525841186cdd6c47545bf7caea86aad": "Sat Aug 23 17:22:16 2025 +0800",
    "86c33f70a1c705b2ced8033718eccbc23c7dad98": "Mon Aug 25 09:59:04 2025 +0800",
    "83626cf58b8197e60efb12c6cee00b786372d40b": "Mon Aug 25 14:13:06 2025 +0800",
    "d4a4bda930e20afb1f96191de474749a6ff467e2": "Wed Aug 27 10:02:06 2025 +0800",
    "31587202f413912b7225923fc252b48e65cc3ec9": "Thu Aug 28 12:08:31 2025 +0800",
    "550543f0294d5cfa556a364c6c277f870168eff7": "Thu Aug 28 19:30:23 2025 +0800",
    "2f8a99ae0fc23418eae5c13d341e3d5076691fe3": "Mon Sep 01 17:44:24 2025 +0800",
    "2ef7d97880806025e0984d4b5e7b58f7a3195b69": "Fri Sep 05 17:33:47 2025 +0800",
    "01daade1decd7bd29aeff2545806b7c13350881d": "Sat Sep 06 16:38:47 2025 +0800",
    "17c83dd40bbb0300966274befe2f05517e2e30ce": "Tue Sep 09 14:34:08 2025 +0800",
    "6cb2d5e946c79d9cf2760a53528bcb3eb3b3c5d1": "Fri Sep 12 10:55:49 2025 +0800",
    "14526de1aa785ad2e84d03bee32c3de0633031ee": "Mon Sep 15 12:52:06 2025 +0800",
    "905eb111596524ce5c47ef1656eba39c37c890e9": "Tue Sep 16 09:19:34 2025 +0800",
    "20190fe764dbb6982c91cde246c82d3bc3ac9d5a": "Sat Sep 20 18:08:16 2025 +0800",
    "b99e6750950f21ad1663774434ead638ea6922d0": "Mon Sep 22 20:29:29 2025 +0800",
    "ea71ba89419153d94e43bf7484f63f1058a5cccf": "Wed Sep 24 10:30:51 2025 +0800",
    "a87e7e246cb92c7df177628ace761f43710b9c79": "Fri Sep 26 10:31:29 2025 +0800",
    "b5a16891daf384e682416c0b55e5bcdaca9acb68": "Mon Sep 29 19:38:26 2025 +0800",
    "2047dafd50ad6572fcb752d8c6633b40b51f4cd8": "Tue Sep 30 15:28:03 2025 +0800",
    "574e851c1f4f277bf9e541e9a750f26daa23ec37": "Fri Oct 03 15:20:39 2025 +0800",
    "07ff1adb55f5b098601f1bb6b96b74c32107a894": "Sat Oct 04 14:48:49 2025 +0800",
    "d9a16f64aa40ff84829715c8123103512fa6899f": "Sun Oct 05 15:27:28 2025 +0800",
    "ed69005dc1716eca85d736609b7d8be383341cd6": "Mon Oct 06 18:09:09 2025 +0800",
    "4e825130c4d78d59b99584ba6a12bd20df119d44": "Wed Oct 08 17:43:57 2025 +0800",
    "041c450125b0cc847e7b33a6d9032b0b23dc0306": "Thu Oct 09 17:26:20 2025 +0800",
    "bdd478bfacd50f059954bc4de13486a856236380": "Fri Oct 10 11:41:19 2025 +0800",
    "609ade06a24b50e3d82326ac428e1877bdec5c52": "Fri Oct 10 15:24:59 2025 +0800",
    "8657d9c849d1e7a23764873ee6dc212e204f79d0": "Fri Oct 10 16:52:54 2025 +0800",
    "616fd9cbdfcaeb149f06b4af7fb1667553a77098": "Fri Oct 10 20:41:28 2025 +0800",
    "4e11b2779329c2529884f40518744211a143dba7": "Fri Oct 10 18:31:52 2025 +0800",
    "7c1d75e0fba5a6976b19b5cf27f2b426e7996cc0": "Wed Oct 15 19:32:15 2025 +0800",
    "60eb62d42101891de3a23b0ee639606264caa18d": "Thu Oct 16 16:08:15 2025 +0800",
    "e90cf438f94fbc46ddc20c26c9a902b1cbe37dd8": "Sat Oct 18 11:48:19 2025 +0800",
    "8333419e14d9aeefa85bab196b5042d790b7f9fc": "Sun Oct 20 15:58:20 2025 +0800",
}

def main():
    print("Starting Git history rewrite using filter-branch...")
    print(f"Modifying {len(commit_dates)} commits\n")
    
    # 构建filter-branch命令
    filter_script_parts = []
    for i, (commit, date) in enumerate(commit_dates.items()):
        if i == 0:
            filter_script_parts.append(f'if [ "$GIT_COMMIT" = "{commit}" ]; then')
        else:
            filter_script_parts.append(f' elif [ "$GIT_COMMIT" = "{commit}" ]; then')
        filter_script_parts.append(f' export GIT_AUTHOR_DATE="{date}";')
        filter_script_parts.append(f' export GIT_COMMITTER_DATE="{date}";')
    filter_script_parts.append(' fi')
    
    filter_script = ''.join(filter_script_parts)
    
    # 使用git filter-branch
    import os
    os.environ['FILTER_BRANCH_SQUELCH_WARNING'] = '1'
    
    cmd = [
        'git', 'filter-branch', '-f',
        '--env-filter', filter_script,
        '--tag-name-filter', 'cat',
        '--', '--all'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            check=True,
            shell=False
        )
        
        print("\n" + "="*70)
        print("Success! Git history has been rewritten.")
        print("="*70)
        print("\nView results:")
        print("  git log --format='%h %ad %s' --date=format:'%Y-%m-%d %H:%M:%S'")
        print("\nIf you need to push to remote:")
        print("  git push --force --all")
        
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nError: filter-branch failed with exit code {e.returncode}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

