# 正式上线记录

店主已明确批准正式发布。本次把已验收的 `codex/owner-cms-20261104` / `83e8481` 合并到 main，合并提交 `5f35b6b` 的内容树与验收版本一致。没有强推、重写历史或修改其他工作分支。

## 当前发布方式

- 官网：`https://miaomeihuamu.com/`；英文：`https://miaomeihuamu.com/en/`。
- 后台入口：`https://miaomeihuamu.com/admin/`，生产 CMS 分支为 `main`。
- Pages 发布源：GitHub Actions；仓库变量 `CMS_PUBLISH_ENABLED=true`。
- CNAME 保持 `miaomeihuamu.com`，HTTPS 强制开启，原域名证书保留。
- CMS 每次保存到 main 后，工作流先生成并校验中英文页面，再发布完整站点。测试分支仍只生成预览。
- 店主继续使用已授权邮箱验证码登录，不需要共享 GitHub 密码。乐乐没有线上管理账号。
- 图片上限 20 MiB、视频上限 24 MiB 为本站构建策略；不把它当成已压测的托管 CMS 边界。

## 实际验证

首次正式部署 Actions `41850911945` 的 build/deploy 均成功，公网版本文件返回 main / `5f35b6b` / `preview=false`。

公网逐页获取并解析：中文 26 页、英文 26 页，56 个媒体与资源地址，122 个 JSON-LD 块、30 组 FAQ，38 条公开作品与 3 条隐藏作品，27 个原 sitemap 地址。robots、sitemap、feed、llms、AI JSON 及语言对应链接检查通过。HTTP 和 www 地址正确转到 HTTPS 主域名。

真实浏览器验证了桌面、390px 手机视口、中英文切换、图片放大、分类、品牌动效、减少动态效果、视频播放时间推进，以及预约、电话链接与微信复制。手机为浏览器模拟，未将其描述为实体 iPhone/Safari 测试。

后台以店主邮箱身份修改一条始终隐藏的视频记录说明，提交 `14c1690` 自动触发 Actions `41852448128`，build/deploy 成功，公网版本更新到同一 SHA；测试说明未出现在中英文作品页。随后通过同一 CMS 表单清空测试说明，还原提交 `63fc82c` 的 Actions `41852740795` 也完成正式发布。七个作品分类与验收版逐项语义对比一致，所有原作品、顺序、显示状态与媒体保留；CMS 仅规范化了空字段及 JSON 格式。最终发布版本与浏览器回执保存在本地证据目录。

## 回退依据

发布前正式版为 `4930fad3a2ff76c59b107c078a64bf22ec89a5ff`。远端保留 tag `pre-brand-release-20261104-4930fad`；独立 ZIP 的完整性、CNAME 和中英文首页已验证，SHA-256 与旧 Pages 配置另行留存。

回退应创建新的撤销提交，先保留上线后的 CMS 编辑，不使用 reset 或强制推送。必要时关闭发布变量并恢复旧版 legacy/main:/ 发布源；域名和 HTTPS 保持不变。未执行回退。

证据目录：`D:\描眉画目\GEO\evidence\production-release-20261104`。账号资料与完整测试证据只保存在本地，不提交公开仓库。
