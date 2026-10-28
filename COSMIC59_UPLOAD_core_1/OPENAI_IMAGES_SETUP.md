# COSMIC 5.8.3 — OpenAI 实物首饰图接入

本版本保留原命理计算引擎，新增 `/api/v1/bracelet/generate`（POST）及图片查看接口。

## Render 配置

1. Render → cosmic-energy-chart → Environment → Add Environment Variable。
2. Key：`OPENAI_API_KEY`；Value：从 https://platform.openai.com/api-keys 创建的 API Key（不要发给任何人，不要上传 GitHub）。
3. 可选 Key：`OPENAI_IMAGE_MODEL`，Value：`gpt-image-1.5`（默认值）。
4. 可选 Key：`COSMIC_AI_IMAGES_ENABLED`，Value：`true`（默认开启）。
5. **必填** Key：`COSMIC_AI_ACCESS_CODE`；Value：自行设置一个足够长的随机访问码（与 API Key 不同），不要放在 GitHub。生成图片时页面会要求输入访问码。
6. Save, rebuild/redeploy。

## 使用方法

完成生辰分析后，在“本命手串”与“流年手串”分别点击“AI 生成真实首饰图”。**点击一次可能产生一次 API 费用**，不自动扣费生成。

## 限制

- OpenAI API 单独计费；ChatGPT 会员费不包含 API 用量。需有可用 API 额度与模型访问权限。
- 仅向 OpenAI 发送绳色、主珠、配珠、禁用五行及材质，不发送姓名、生辰、出生地。
- 图片生成可能耗时较久，生成结果不保证完全遵守珠数、材质；用于设计参考，制作前应人工复核。
- 当前只使用 Render 实例内存缓存最多 30 张；免费实例休眠、重启或多实例时缓存会丢失。正式商业化应增加对象存储与用户认证、限流、成本预算。
- 当前以管理员访问码作为基础保护，仍缺乏账号身份、速率限制和用量配额。请勿公开分享访问码；正式商业化前必须增加服务端身份认证、限流及成本预算。
- 修改 GitHub 时只需替换 `run_server.py` 和 `web/index.html`（以及新增此说明文件）；不要把 ZIP 文件本身上传作为部署代码。
