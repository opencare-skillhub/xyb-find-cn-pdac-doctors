# 找医生 / find-cn-pdac-doctors

面向中国胰腺癌（PDAC）患者与家属的医生资源查询技能，覆盖肿瘤内科、外科、影像读片及其他支持学科，也可辅助准备第二意见问题。

**查询给出完整 list：列出库内所有符合条件的记录，不只挑几位。** 当前快照为 229 条医生记录和 36 条试验记录；名单覆盖范围有限，具体任职、院区、出诊、招募情况需要当次核实。

一如既往，感谢 **小x宝社区志愿者 sam 的 ❤️ 贡献**。

## 安装

需要 Python 3.9+，查询脚本仅依赖标准库。克隆到技能目录，文件夹使用技能英文名：

```bash
git clone git@github.com:opencare-skillhub/xyb-find-cn-pdac-doctors.git ~/.codex/skills/find-cn-pdac-doctors
cd ~/.codex/skills/find-cn-pdac-doctors
python3 scripts/doctor_db.py --validate
```

重新加载宿主的技能列表后，通过 `$find-cn-pdac-doctors` 调用；其他技能宿主可把仓库克隆到其技能目录。UI 名称为“找医生”。联网核验使用宿主已有搜索工具，离线仍可查 CSV，但应标明未核验当前信息。

## 典型使用方式

对 AI 直接说：

- “使用 $find-cn-pdac-doctors，列出上海所有库内匹配的胰腺癌影像读片医生，包括来源、用途与备注。”
- “帮我找山西的胰腺癌肿瘤内科医生，完整列出候选，并核实郭亚荣的医院与出诊信息。”
- “查钱黎俊的影像会诊信息，说明社区推荐与官方已核实信息分别是什么。”
- “列出库内所有 KRAS 相关胰腺癌试验线索，核验招募状态，未核实的注明待核。”
- “针对这个治疗建议准备第二意见问题，附证据来源、适用条件和费用需要问清的项目。”

命令行从仓库根目录运行：

```bash
# 默认就是完整编号 list，保留完整备注
python3 scripts/doctor_db.py --city 上海 --dept 影像
python3 scripts/doctor_db.py --city 太原 --dept 肿瘤
# 姓名精确匹配；不会混入其他人备注中提及该姓名的记录
python3 scripts/doctor_db.py --name 钱黎俊
python3 scripts/doctor_db.py --name 郭亚荣
# 全字段关键词 AND 匹配，可能匹配备注；不做同义词推断
python3 scripts/doctor_db.py --query "广州 影像"
python3 scripts/doctor_db.py --table trials --query KRAS
# 全量列表和机器可读的全字段结果
python3 scripts/doctor_db.py --list
python3 scripts/doctor_db.py --city 上海 --json > /tmp/shanghai-doctors.json
```

字段条件不会自动把“山西”转成“太原”；可用 `--query 山西` 搜医院名，或用 `--city 太原`。`--brief` 兼容旧用法，与默认完整 list 一致。零命中也返回 count=0；错误返回非零状态。输出较长时请写入文件查看，交付给用户时附完整文件，不用终端预览的截断内容冒充完整名单。

## 通过 CSV 更新数据

1. 修改 `data/doctors.csv`；新增医生补齐稳定序号、姓名、医院、科室、城市、依据与日期。已有医生更新原行，避免重复。试验修改 `data/trials.csv`。
2. 保留中文表头，保存 UTF-8；优先附官方网址。仅有社区或用户资料时标明来源、日期和待核项，不编造评分、任职或招募状态。
3. 运行校验与目标查询，确认新记录能被找到：

   ```bash
   python3 scripts/doctor_db.py --validate
   python3 scripts/doctor_db.py --table trials --validate
   python3 scripts/doctor_db.py --audit > /tmp/doctor-audit.json
   python3 -m unittest discover -s tests
   ```

4. 提交 CSV 与相关来源说明的变更。下次查询直接读取新 CSV，**无需导入 SQLite、修改脚本或重建索引**。

完整字段说明和去重规则见 [维护规范](references/local-db.md)，历史来源与数据口径见 [数据说明](data/README.md)。原始快照不会覆盖现行 CSV。

## 已知边界

分类和风险标记是原始档案口径，不是全国排名或医疗认证；R0 不保证安全，RU 表示经验待核，U 表示未知。社区“首选”是有出处的经验评价，所有匹配项仍会列出。原库部分记录缺少可直接访问的出处，审计输出用于逐步补齐。

技能检查覆盖离线查询、名单完整性与数据结构，不能替代对每位医生的当前执业事实核验。医生名单、试验线索与方案核查不构成诊断或处方，具体决策与正规医院主诊/MDT 团队讨论。

## 协议与贡献

[MIT License](LICENSE)。欢迎提交 CSV 数据补充、来源校正与使用反馈；请只贡献可分享的公开或获授权资料，不提交患者隐私。

## 首次发布

远端仓库已建立：`opencare-skillhub/xyb-find-cn-pdac-doctors`。贡献者可在已配置 GitHub SSH、拥有仓库写入权限且允许 Git 写入的终端运行 `sh scripts/publish.sh`，将本地提交推送到 main。脚本使用普通推送；远端已有不同历史时会拒绝覆盖，需先检查并合并。`LICENSE` 随文件一并提交。
