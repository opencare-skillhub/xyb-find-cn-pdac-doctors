#!/bin/sh
# 在允许 Git 写入及 GitHub 网络访问的终端运行；需要 gh 已登录且拥有组织建仓权限。
set -eu
cd "$(dirname "$0")/.."
repo=opencare-skillhub/find-cn-pdac-doctors
export GH_PROMPT_DISABLED=1
# 连接或认证失败即停止，不覆盖已有仓库。
gh api user --jq .login
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
# 失败即退出；仓库若已存在，请人工核对归属及 remote 后使用 git push。
gh repo create "$repo" --public --source=. --remote=origin --push \
  --description '找医生：中国胰腺癌医生完整名单查询技能，CSV 持续维护。感谢小x宝社区志愿者 sam 的 ❤️ 贡献。'
