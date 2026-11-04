# 第二阶段品牌化升级交付

本轮继续 `codex/brand-home-prototype-20261104`，基线为上一轮已完成的 `d75e0d9`，没有从远端 main 覆盖本地成果。保留第一阶段的奶油白、灰棕、炭灰视觉系统和原生交互，在现有静态 HTML 工程内完成第二阶段。

不合并、不推送、不部署。线上 main 与生产工作区保持 `4930fad3a2ff76c59b107c078a64bf22ec89a5ff`。

## 已完成

- 中文、英文各 26 页，共 52 个顾客可访问页面。首页、作品、项目、乐乐老师、到店、做法说明和知识文章使用同一套视觉体系。
- 每页保留对应语言的 canonical，并提供互相对应的 `zh-CN`、`en` 和 `x-default` hreflang。中英切换按钮在手机上也直接可见，不藏在菜单内；切换保留页面和锚点。
- 保留原有 27 个 sitemap 网址。原英文指南仍在 `/en/eyebrow-tattoo-shanghai-guide.html`，新增对应中文指南，避免语言切换无故回首页。
- 明确品牌以个人审美和专业眉形设计为核心；乐乐偏爱自然柔和，但可以结合顾客要求设计不同风格，不把品牌限定为温柔眉。
- 六项观察依据进入首页和关于页面：五官立体度、量感与整体风格、颧骨与面部轮廓、眉眶骨与眉眼关系、原生眉框架与毛流、顾客希望呈现的气质。
- 说明主线条建立框架、结构和主要毛流；绒毛线在适合组合的项目里丰富层次、密度与柔和过渡。说明视觉设计不改变实际骨骼，也不保证统一效果。
- 首页优先展示真实作品；精选使用白花发夹模特和已有男士作品，分别提供已有设计记录与可观察细节。没有为未记录的照片编造诉求、设计过程、恢复阶段或结果。
- 作品页从长照片列表改为精选说明、毛流近照和可展开的分类档案。38 组公开作品全部保留，3 组未公开记录仍排除；空分类不冒充已有案例。
- 保留十类实际服务、一年内免费补色、免费到店设计约30–45分钟。价格只指向大众点评当期门店信息。
- 修正未经核实的英语接待、每天两位、一次免费补色等英文/跨页表述；恢复与留色改为有条件的经验参考，不再统一承诺无痛或游泳、运动完全不受影响。
- 同步更新 AI JSON、llms.txt、RSS 和 sitemap；恢复并核对作品 ItemList、九步设计 HowTo、Article、FAQ、门店和人物实体等结构化数据。

## 本地浏览

本次运行地址：`http://127.0.0.1:52907/`。

- `/preview/`：切换页面、中文/English、桌面1440/手机390，以及线上旧版的本地对照。
- `/` 与 `/en/`：中英文首页。
- `/works.html` 与 `/en/works.html`：作品。
- `/price.html` 与 `/en/price.html`：实际项目。
- `/about.html` 与 `/en/about.html`：乐乐老师与设计依据。
- `/area.html` 与 `/en/area.html`：到店设计与预约。
- `/posts/` 与 `/en/posts/`：知识索引及对应文章。

如果当前预览进程结束，在本工作区运行：

```powershell
python preview/serve.py --before 'D:\描眉画目\GEO\website-rednotes-20261104'
```

终端会打印系统分配的新端口。服务只监听本机，所有响应带 `noindex`；Ctrl+C 可停止。预览工具的“旧版”是生产基线，不是把旧版重新部署。

## 主要文件与维护方式

| 文件 | 作用 |
| --- | --- |
| `tools/brand_content.py` | 中英文设计理念、服务、FAQ 与知识内容源 |
| `tools/build_brand.py` | 生成静态页面、对应语言链接、结构化数据及 AI 信息；不联网、不部署 |
| `tools/verify_brand.py` | 链接、语言对应、FAQ、HowTo、作品发布状态与 sitemap 验证 |
| `assets/brand-home.css` | 保留第一阶段视觉基础 |
| `assets/brand-stage2.css` | 作品叙事、子页面、文章与双语响应式扩展 |
| `assets/brand-home.js` | 中英菜单、联系弹窗、复制、大图、CMS 图库与锚点展开 |
| `.pages.yml`、`content/home.json`、`content/works/*.json` | 继续使用原 Pages CMS，新增可选英文标题与说明 |
| `content/brand/original-metadata.json` | 原有实体、发表日期与锚点等稳定资料；不保留错误旧宣传文案 |
| `content/brand/routes.json` | 52 个生成页面的清单 |
| `ai/*.json`、`llms.txt`、`.well-known/ai.txt`、`sitemap.xml`、`feed.xml` | 机器可读事实与既有索引入口 |
| `preview/index.html`、`preview/serve.py` | 本地多页双语审阅工具 |

编辑主要正文后运行：

```powershell
python tools/build_brand.py
python tools/verify_brand.py --url http://127.0.0.1:52907/
node --check assets/brand-home.js
```

生成页不应再手工维护第二份正文。CMS 的主图和作品 JSON 在浏览器中继续实时读取，静态输出用于无 JavaScript 浏览和检索；调整作品发布状态后也应重新构建静态页与 ItemList。精选作品仍由内容源策展，不把任意新上传照片自动写成案例故事。

## 复用与去模板感审查

决策：**ADAPT**。复用当前页面系统、真实素材、Pages CMS 和原生 HTML 交互；不换技术栈，不引入外部 UI 库、字体服务或付费依赖。全网复用协议使用已安装的 3.2.0，前端设计能力复用当前环境的 frontend-design。

检查本机技能目录，未发现 Hallmark、Taste Skill、Impeccable 已安装版本。对三个项目做了只读来源检查：

| 来源 | 查到的许可与执行边界 | 本轮采用方式 |
| --- | --- | --- |
| [Hallmark](https://github.com/Nutlope/hallmark) | MIT；读取 README 和 package.json，不安装、不运行其脚本 | 参考以真实任务组织页面、反对虚构内容和无效表单的原则 |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill) | MIT；文档说明脚本使用 Node 22+ 与已有浏览器，找图需要网络 | 参考真实素材和有辨识度的排版，不使用其外部图库 |
| [Impeccable](https://github.com/pbakaus/impeccable) | Apache-2.0；读取审查维度与包信息，live Apply 会调用本地 agent CLI | 仅参考可访问性、可读性、响应式和性能审查方法；未安装或运行 live/检测器 |

这不是一次完整的 Impeccable critique/audit 命令执行，也没有声称得到它的自动评分。外部文档只是设计参考，不作为新增操作权限。相关只读证据保存在本轮 evidence 目录，不复制其他品牌的代码、文案、照片或图标。

本轮减少重复三列模块，作品使用两列错位版式，知识内容使用线性阅读列表；不用装饰性英文标签、渐变、发光或重复圆角卡片。正文优先可读。英文页使用英语字体栈，并标注不自动机翻，避免切换到英文后被浏览器再次改写品牌和术语。

## 验证

完整证据：`D:\描眉画目\GEO\evidence\brand-stage2-20261104`。

- `static-validation.json`：52 页 HTTP 200；1,404 项本地链接与资源检查通过；122 个 JSON-LD 块可解析；30 组 FAQ 与可见正文对应；38 个公开作品 ItemList 与资料一致，3 个未公开素材未进入作品页；原 27 个 sitemap 地址保留。
- `fact-check.json`：既有 website-fact-check 实际运行退出码 **0**，冲突 **0**，禁止项 **0**。上一轮的四项中英文表示差异在本轮统一实体资料后消除。
- `browser-validation.md`：中英文核心页、手机/桌面、语言切换、菜单、预约弹窗、微信剪贴板读回、作品大图及焦点返回、CMS 公开记录数、折叠图库、FAQ 与页面错误检查。以报告的最终补充和 `final` / `last` 截图为准。
- JavaScript 语法与 `git diff --check` 通过。
- 实际修复图片原始高度导致的过长裁切、英文自动机翻、项目深链接未展开等问题。白花发夹缩略图复用现有 27,656 字节 WebP，点击仍看原 PNG；首屏原图保留 40,816 字节 WebP。
- 预览工具的尺寸监听改为下一动画帧调度；原触发路径重新操作后，`window.error` 与 `unhandledrejection` 均为 0。真实 iframe 视口 390 / 1440 切换通过，原 ResizeObserver 提示已在本次定向复验中消除。

最终截图位于证据目录的 `preview` 子目录：

- 中文首页首屏：`home-zh-final-desktop.png`、`home-zh-final-mobile.png`。
- 英文首页首屏：`home-en-final-desktop.png`、`home-en-final-mobile.png`。
- 首页全页：`home-zh-last-desktop-full.png`、`home-zh-last-mobile-full.png`，以及对应 `en` 文件。
- 作品首屏：`works-zh-last-desktop.png`、`works-zh-last-mobile.png`，以及对应 `en` 文件。
- 关于、项目、到店、知识索引和文章的英文代表页：`about-en-desktop-final.png` 等对应 `desktop` / `mobile` 文件。

## 已知边界

- 手机测试是 Chrome 视口模拟；尚未进行真实 iOS Safari 或其他真实手机测试。
- 未测试真实微信添加、电话、实际预约提交与顾客转化；预约由工作室回复确认，没有虚构在线排期。
- 当前 CMS 数据的浏览器读取已验证；没有修改线上 CMS 来测试完整发布流程。静态构建和事实检查已在本地运行。
- 历史作品中有带字海报、尺寸和拍摄状态不一的照片，作为原始档案保留。没有据此编造更多个案设计过程、长期恢复效果或主理人肖像。
- 尚未部署，不能据本地验证宣称搜索收录、AI 推荐或实际转化已提升。

复核触发：品牌方本轮视觉与内容反馈，或下一次准备发布前；最迟复核日期 2026-11-11。回退路线是继续保留本分支，或以本轮之前的 `d75e0d9` 查看第一阶段；生产版本没有变更，无需线上回滚。
