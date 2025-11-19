# Git提交日期自动重写脚本（无交互版本）

Write-Host "开始重写Git提交历史..." -ForegroundColor Green

# 设置Git环境变量以跳过警告
$env:FILTER_BRANCH_SQUELCH_WARNING = "1"

# 定义filter脚本
$filterScript = @'
if test "$GIT_COMMIT" = "e8280b2a568a483ed9e971dddc46b1efb96a0858"; then
    export GIT_AUTHOR_DATE="Fri Aug 01 10:00:00 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Aug 01 10:00:00 2025 +0800"
fi
if test "$GIT_COMMIT" = "a5cf77df8e50f8ee4cd759e9449c821d75bc9f65"; then
    export GIT_AUTHOR_DATE="Fri Aug 01 13:26:54 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Aug 01 13:26:54 2025 +0800"
fi
if test "$GIT_COMMIT" = "300b4119143d1d7afba0375de8881b93f39652a4"; then
    export GIT_AUTHOR_DATE="Mon Aug 04 21:34:35 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Aug 04 21:34:35 2025 +0800"
fi
if test "$GIT_COMMIT" = "9879d43e4e483ed5b0db35bc233979415bdeb636"; then
    export GIT_AUTHOR_DATE="Tue Aug 05 13:49:12 2025 +0800"
    export GIT_COMMITTER_DATE="Tue Aug 05 13:49:12 2025 +0800"
fi
if test "$GIT_COMMIT" = "1e160fab246873f52db2b6d4be4380f9e02757e3"; then
    export GIT_AUTHOR_DATE="Wed Aug 06 19:33:20 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Aug 06 19:33:20 2025 +0800"
fi
if test "$GIT_COMMIT" = "e798d77a27c891d5701327d0b8453dcef864e757"; then
    export GIT_AUTHOR_DATE="Thu Aug 07 11:41:09 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Aug 07 11:41:09 2025 +0800"
fi
if test "$GIT_COMMIT" = "bbf167ee7e45f78423cf69f3bf740f015287c823"; then
    export GIT_AUTHOR_DATE="Thu Aug 07 18:08:33 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Aug 07 18:08:33 2025 +0800"
fi
if test "$GIT_COMMIT" = "d3b61bab78a414884a4971b7da49d6fc83327b04"; then
    export GIT_AUTHOR_DATE="Fri Aug 08 17:11:12 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Aug 08 17:11:12 2025 +0800"
fi
if test "$GIT_COMMIT" = "92edc22dd35582dc462857b0f0b4ebe46b85f2e9"; then
    export GIT_AUTHOR_DATE="Mon Aug 11 17:50:09 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Aug 11 17:50:09 2025 +0800"
fi
if test "$GIT_COMMIT" = "7ec76c735981d04519f0b15339d8fc8a78e15637"; then
    export GIT_AUTHOR_DATE="Wed Aug 13 16:22:26 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Aug 13 16:22:26 2025 +0800"
fi
if test "$GIT_COMMIT" = "098364ef613e16127be2efef0e7f712d57e90014"; then
    export GIT_AUTHOR_DATE="Thu Aug 14 15:38:53 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Aug 14 15:38:53 2025 +0800"
fi
if test "$GIT_COMMIT" = "f380153b214fc399fbe788e877d4fd6904179a3a"; then
    export GIT_AUTHOR_DATE="Sat Aug 16 16:51:52 2025 +0800"
    export GIT_COMMITTER_DATE="Sat Aug 16 16:51:52 2025 +0800"
fi
if test "$GIT_COMMIT" = "6a00f465a1a24398af9ecafd28e586f9331f3d36"; then
    export GIT_AUTHOR_DATE="Tue Aug 19 21:47:41 2025 +0800"
    export GIT_COMMITTER_DATE="Tue Aug 19 21:47:41 2025 +0800"
fi
if test "$GIT_COMMIT" = "4485410a0ec8dc1aaace756dd1ed021a1a34c5f2"; then
    export GIT_AUTHOR_DATE="Wed Aug 20 09:44:28 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Aug 20 09:44:28 2025 +0800"
fi
if test "$GIT_COMMIT" = "b70602d1ccb1a1d8158d893d1a50d743abcb198d"; then
    export GIT_AUTHOR_DATE="Thu Aug 21 19:36:22 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Aug 21 19:36:22 2025 +0800"
fi
if test "$GIT_COMMIT" = "ead2aee2a525841186cdd6c47545bf7caea86aad"; then
    export GIT_AUTHOR_DATE="Sat Aug 23 17:22:16 2025 +0800"
    export GIT_COMMITTER_DATE="Sat Aug 23 17:22:16 2025 +0800"
fi
if test "$GIT_COMMIT" = "86c33f70a1c705b2ced8033718eccbc23c7dad98"; then
    export GIT_AUTHOR_DATE="Mon Aug 25 09:59:04 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Aug 25 09:59:04 2025 +0800"
fi
if test "$GIT_COMMIT" = "83626cf58b8197e60efb12c6cee00b786372d40b"; then
    export GIT_AUTHOR_DATE="Mon Aug 25 14:13:06 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Aug 25 14:13:06 2025 +0800"
fi
if test "$GIT_COMMIT" = "d4a4bda930e20afb1f96191de474749a6ff467e2"; then
    export GIT_AUTHOR_DATE="Wed Aug 27 10:02:06 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Aug 27 10:02:06 2025 +0800"
fi
if test "$GIT_COMMIT" = "31587202f413912b7225923fc252b48e65cc3ec9"; then
    export GIT_AUTHOR_DATE="Thu Aug 28 12:08:31 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Aug 28 12:08:31 2025 +0800"
fi
if test "$GIT_COMMIT" = "550543f0294d5cfa556a364c6c277f870168eff7"; then
    export GIT_AUTHOR_DATE="Thu Aug 28 19:30:23 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Aug 28 19:30:23 2025 +0800"
fi
if test "$GIT_COMMIT" = "2f8a99ae0fc23418eae5c13d341e3d5076691fe3"; then
    export GIT_AUTHOR_DATE="Mon Sep 01 17:44:24 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Sep 01 17:44:24 2025 +0800"
fi
if test "$GIT_COMMIT" = "2ef7d97880806025e0984d4b5e7b58f7a3195b69"; then
    export GIT_AUTHOR_DATE="Fri Sep 05 17:33:47 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Sep 05 17:33:47 2025 +0800"
fi
if test "$GIT_COMMIT" = "01daade1decd7bd29aeff2545806b7c13350881d"; then
    export GIT_AUTHOR_DATE="Sat Sep 06 16:38:47 2025 +0800"
    export GIT_COMMITTER_DATE="Sat Sep 06 16:38:47 2025 +0800"
fi
if test "$GIT_COMMIT" = "17c83dd40bbb0300966274befe2f05517e2e30ce"; then
    export GIT_AUTHOR_DATE="Tue Sep 09 14:34:08 2025 +0800"
    export GIT_COMMITTER_DATE="Tue Sep 09 14:34:08 2025 +0800"
fi
if test "$GIT_COMMIT" = "6cb2d5e946c79d9cf2760a53528bcb3eb3b3c5d1"; then
    export GIT_AUTHOR_DATE="Fri Sep 12 10:55:49 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Sep 12 10:55:49 2025 +0800"
fi
if test "$GIT_COMMIT" = "14526de1aa785ad2e84d03bee32c3de0633031ee"; then
    export GIT_AUTHOR_DATE="Mon Sep 15 12:52:06 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Sep 15 12:52:06 2025 +0800"
fi
if test "$GIT_COMMIT" = "905eb111596524ce5c47ef1656eba39c37c890e9"; then
    export GIT_AUTHOR_DATE="Tue Sep 16 09:19:34 2025 +0800"
    export GIT_COMMITTER_DATE="Tue Sep 16 09:19:34 2025 +0800"
fi
if test "$GIT_COMMIT" = "20190fe764dbb6982c91cde246c82d3bc3ac9d5a"; then
    export GIT_AUTHOR_DATE="Sat Sep 20 18:08:16 2025 +0800"
    export GIT_COMMITTER_DATE="Sat Sep 20 18:08:16 2025 +0800"
fi
if test "$GIT_COMMIT" = "b99e6750950f21ad1663774434ead638ea6922d0"; then
    export GIT_AUTHOR_DATE="Mon Sep 22 20:29:29 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Sep 22 20:29:29 2025 +0800"
fi
if test "$GIT_COMMIT" = "ea71ba89419153d94e43bf7484f63f1058a5cccf"; then
    export GIT_AUTHOR_DATE="Wed Sep 24 10:30:51 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Sep 24 10:30:51 2025 +0800"
fi
if test "$GIT_COMMIT" = "a87e7e246cb92c7df177628ace761f43710b9c79"; then
    export GIT_AUTHOR_DATE="Fri Sep 26 10:31:29 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Sep 26 10:31:29 2025 +0800"
fi
if test "$GIT_COMMIT" = "b5a16891daf384e682416c0b55e5bcdaca9acb68"; then
    export GIT_AUTHOR_DATE="Mon Sep 29 19:38:26 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Sep 29 19:38:26 2025 +0800"
fi
if test "$GIT_COMMIT" = "2047dafd50ad6572fcb752d8c6633b40b51f4cd8"; then
    export GIT_AUTHOR_DATE="Tue Sep 30 15:28:03 2025 +0800"
    export GIT_COMMITTER_DATE="Tue Sep 30 15:28:03 2025 +0800"
fi
if test "$GIT_COMMIT" = "574e851c1f4f277bf9e541e9a750f26daa23ec37"; then
    export GIT_AUTHOR_DATE="Fri Oct 03 15:20:39 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Oct 03 15:20:39 2025 +0800"
fi
if test "$GIT_COMMIT" = "07ff1adb55f5b098601f1bb6b96b74c32107a894"; then
    export GIT_AUTHOR_DATE="Sat Oct 04 14:48:49 2025 +0800"
    export GIT_COMMITTER_DATE="Sat Oct 04 14:48:49 2025 +0800"
fi
if test "$GIT_COMMIT" = "d9a16f64aa40ff84829715c8123103512fa6899f"; then
    export GIT_AUTHOR_DATE="Sun Oct 05 15:27:28 2025 +0800"
    export GIT_COMMITTER_DATE="Sun Oct 05 15:27:28 2025 +0800"
fi
if test "$GIT_COMMIT" = "ed69005dc1716eca85d736609b7d8be383341cd6"; then
    export GIT_AUTHOR_DATE="Mon Oct 06 18:09:09 2025 +0800"
    export GIT_COMMITTER_DATE="Mon Oct 06 18:09:09 2025 +0800"
fi
if test "$GIT_COMMIT" = "4e825130c4d78d59b99584ba6a12bd20df119d44"; then
    export GIT_AUTHOR_DATE="Wed Oct 08 17:43:57 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Oct 08 17:43:57 2025 +0800"
fi
if test "$GIT_COMMIT" = "041c450125b0cc847e7b33a6d9032b0b23dc0306"; then
    export GIT_AUTHOR_DATE="Thu Oct 09 17:26:20 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Oct 09 17:26:20 2025 +0800"
fi
if test "$GIT_COMMIT" = "bdd478bfacd50f059954bc4de13486a856236380"; then
    export GIT_AUTHOR_DATE="Fri Oct 10 11:41:19 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Oct 10 11:41:19 2025 +0800"
fi
if test "$GIT_COMMIT" = "609ade06a24b50e3d82326ac428e1877bdec5c52"; then
    export GIT_AUTHOR_DATE="Fri Oct 10 15:24:59 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Oct 10 15:24:59 2025 +0800"
fi
if test "$GIT_COMMIT" = "8657d9c849d1e7a23764873ee6dc212e204f79d0"; then
    export GIT_AUTHOR_DATE="Fri Oct 10 16:52:54 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Oct 10 16:52:54 2025 +0800"
fi
if test "$GIT_COMMIT" = "616fd9cbdfcaeb149f06b4af7fb1667553a77098"; then
    export GIT_AUTHOR_DATE="Fri Oct 10 20:41:28 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Oct 10 20:41:28 2025 +0800"
fi
if test "$GIT_COMMIT" = "4e11b2779329c2529884f40518744211a143dba7"; then
    export GIT_AUTHOR_DATE="Fri Oct 10 18:31:52 2025 +0800"
    export GIT_COMMITTER_DATE="Fri Oct 10 18:31:52 2025 +0800"
fi
if test "$GIT_COMMIT" = "7c1d75e0fba5a6976b19b5cf27f2b426e7996cc0"; then
    export GIT_AUTHOR_DATE="Wed Oct 15 19:32:15 2025 +0800"
    export GIT_COMMITTER_DATE="Wed Oct 15 19:32:15 2025 +0800"
fi
if test "$GIT_COMMIT" = "60eb62d42101891de3a23b0ee639606264caa18d"; then
    export GIT_AUTHOR_DATE="Thu Oct 16 16:08:15 2025 +0800"
    export GIT_COMMITTER_DATE="Thu Oct 16 16:08:15 2025 +0800"
fi
if test "$GIT_COMMIT" = "e90cf438f94fbc46ddc20c26c9a902b1cbe37dd8"; then
    export GIT_AUTHOR_DATE="Sat Oct 18 11:48:19 2025 +0800"
    export GIT_COMMITTER_DATE="Sat Oct 18 11:48:19 2025 +0800"
fi
if test "$GIT_COMMIT" = "8333419e14d9aeefa85bab196b5042d790b7f9fc"; then
    export GIT_AUTHOR_DATE="Sun Oct 20 15:58:20 2025 +0800"
    export GIT_COMMITTER_DATE="Sun Oct 20 15:58:20 2025 +0800"
fi
'@

# 执行filter-branch
git filter-branch -f --env-filter $filterScript --tag-name-filter cat -- --all

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success! Git history has been rewritten." -ForegroundColor Green
    Write-Host "View results: git log --format='%h %ad %s' --date=format:'%Y-%m-%d %H:%M:%S'" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Rewrite failed! Exit code: $LASTEXITCODE" -ForegroundColor Red
}

