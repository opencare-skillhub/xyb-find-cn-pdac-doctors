#!/bin/sh
# 在允许 Git 写入及 GitHub SSH 访问的终端运行；远端仓库已建立。
set -eu
cd "$(dirname "$0")/.."
remote_url=git@github.com:opencare-skillhub/xyb-find-cn-pdac-doctors.git
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10"
# 连接或认证失败即停止。
git ls-remote "$remote_url"
if [ ! -d .git ]; then
  if [ -f find-cn-pdac-doctors.bundle ]; then
    git init -b main
    git fetch ./find-cn-pdac-doctors.bundle main
    git reset --mixed FETCH_HEAD
  else
    git init -b main
    git add .
    git commit -m 'Create find-cn-pdac-doctors skill and CSV maintenance workflow'
  fi
fi
if [ -n "$(git status --porcelain)" ]; then
  echo '存在未提交变更，请先检查并提交后重试。' >&2
  exit 1
fi
# 使用普通推送；不会强制覆盖远端已有历史。
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$remote_url"
else
  git remote add origin "$remote_url"
fi
git push -u origin main
