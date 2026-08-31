# ZhiPhoto 技能

[English](README.md) | 简体中文

## ZhiPhoto 一览

| 01 · 从想法到画面 | 02 · 从文字到画面 |
|---|---|
| ![ZhiPhoto 将想法变成画面](demo/zhiphoto-promotion-illustrations-20260824/01-idea-to-image-20260824T233614.png) | ![ZhiPhoto 将文字变成画面](demo/zhiphoto-promotion-illustrations-20260824/02-text-to-picture-20260824T233907.png) |

| 03 · 控制风格与构图 | 04 · 迭代出更好的结果 |
|---|---|
| ![用 ZhiPhoto 控制风格与构图](demo/zhiphoto-promotion-illustrations-20260824/03-style-composition-control-20260824T234108.png) | ![迭代出更好的 ZhiPhoto 结果](demo/zhiphoto-promotion-illustrations-20260824/04-iteration-20260824T234907.png) |

| 05 · 将产出放进内容 | |
|---|---|
| ![将 ZhiPhoto 产出用于内容](demo/zhiphoto-promotion-illustrations-20260824/05-output-to-content-20260824T235244.png) | |

| 07 · 多组照片风格模板集合 | |
|---|---|
| ![多组照片风格模板集合](demo/zhiphoto-promotion-illustrations-20260824/07-style-template-collections-20260824T240407.png) | |

这是一个可扩展的 Codex 技能，用于编写图像提示词——既可以通过 Codex 内置的图像生成能力直接生成图像并验证本地结果，也可以在客户要的其实是提示词而不是图像时，把一批提示词整理成一份本地静态网页，交给你自己去 ChatGPT 里逐条粘贴运行。

本项目由 **zhi-ai-lab** 所有和维护，采用 Apache License 2.0 发布。

本项目独立开发，与 OpenAI 没有关联，也不代表 OpenAI 的认可。此处使用 Codex 和 OpenAI 产品名称，仅用于描述互操作性；Apache License 不授予商标权。

## 要求

- Python 3.10 或更高版本。目录和测试仅使用 Python 标准库。
- Codex，并可使用其内置的 `image_gen` 工具——无需浏览器、无需登录，生成本身也不需要 API key。
- 对所选输出目录的本地文件系统访问权限，以及检查已保存图像的能力。

## 安装

安装公开的 GitHub marketplace，然后使用带 marketplace 限定符的名称安装插件：

```bash
codex plugin marketplace add zhi-ai-lab/zhiphoto
codex plugin add zhiphoto@zhi-ai-lab
```

marketplace 条目固定到 `v1.0.0`。如果宿主应用有相应要求，请重启 Codex，或重新加载 Codex 技能发现结果。

## 快速安装（npx skills）

推荐通过 [`skills`](https://www.npmjs.com/package/skills) 为 Codex 安装：

```bash
npx skills add zhi-ai-lab/zhiphoto --skill zhiphoto --agent codex --global --yes --copy
```

重新运行这条命令即可把安装更新到仓库的当前状态。仓库是唯一的事实来源；已安装的副本不会被手动修改。

## 使用

让 Codex 生成图像，或者显式调用此技能：

```text
Use $zhiphoto to create a sunlit travel poster and save it locally.
```

此技能已启用自动调用功能。因此，除非用户选择其他生成器，否则普通的单图文本到图像请求，以及明确要求的正文多张配图请求，无需指定技能名称，也可以激活此技能。

对于 `article-illustration` 类型，只要客户表达了要使用 personal-IP 模板的意图，ZhiPhoto 就会优先使用该模板：获取模板文件（本次运行中已附带的，或请客户直接附上/指出本地文件路径），用 `view_image` 将其带入上下文，再以标注角色的方式（作为参考图）传给 `image_gen`。如果客户完全没有提供模板意图，它会回退到原始 Xiaohei 角色；但如果已经提供了模板意图，却无法获得可用的模板文件，ZhiPhoto 会直接停止，不会静默回退。

该工作流会动态发现提示词指导，编写保留用户确切要求的最终提示词，通过 Codex 内置的 `image_gen` 工具生成图像，等待每张图生成完成，然后把工具输出的文件移动到目标位置。默认情况下，每次运行都会在 `.local/output/` 下生成一个带时间戳的独立文件夹，把图像和记录了实际提交提示词的 `<basename>.prompt.md` 提示词副本保存在一起。除非客户在请求中明确要求直接生成，否则 ZhiPhoto 会先把最终提示词保存到本地，并请客户确认后才真正调用 `image_gen` 生成。正文配图 series 会先形成有序 shot list，再逐张生成和保存；如果需要模板，会对每个 shot 重复模板获取与 `view_image` 检查、以及生成前的确认。默认仍然是一张图；如果客户明确要求 `N` 张配图，就必须生成恰好 `N` 个 shot；如果客户只说要多张图却没给数量，ZhiPhoto 会先追问数量，再开始生成。它会在 `$CODEX_HOME/generated_images/` 下定位工具生成的输出文件，并将其移动、重命名到目标输出目录，不使用浏览器下载控件、直接获取资源或截图。

如果客户要的是提示词而不是图像——比如“帮我生成 10 条窗边人像的提示词，我自己去 ChatGPT 里试”——ZhiPhoto 会走完同一套路由、类型/profile 选择和提示词编写流程，但不再调用 `image_gen`：它会在 `.local/output/` 下生成一个带时间戳的文件夹，写入一份机器可读的 `batch.json` 清单和一份自包含的 `prompts.html` 静态网页。这份网页可以离线打开（`file://`，不需要服务器，也不发起任何网络请求），每条提示词都配有复制按钮、说明是否需要参考图（以及需要附什么、为什么）的徽章，还有一个“已测试”开关，方便你在自己的 ChatGPT 会话里逐条粘贴、按需附上参考图、亲自查看结果之后再做标记。这个模式下 ZhiPhoto 同样不会打开、跳转、链接或提交任何内容到 chatgpt.com 或其他网站——粘贴、附图、查看结果，全部由你自己动手完成。

## 架构

```text
skills/zhiphoto/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── image_catalog.py
│   └── prompt_page.py
└── references/
    ├── image-profile-authoring.md
    ├── transport/
    │   ├── codex-image-gen.md
    │   └── prompt-handoff.md
    └── types/
        └── <type-id>/
            ├── TYPE.md
            ├── foundations/...
            └── profiles/**/*.md
```

`SKILL.md` 是稳定的路由器，也负责判断一个请求该走下面两种传输方式中的哪一种。`image_catalog.py` 从发现到的类型和 profile 文件中读取严格 frontmatter，验证目录，并返回 agent 必须读取的参考资料。类型 foundation 提供共享指导；profile 只包含特定请求的差异。两份传输参考资料共用同一套路由结果：`codex-image-gen.md` 负责 Codex `image_gen` 的调用、输出文件的定位与移动、文件名冲突处理、文件格式检测以及最终的视觉验证；`prompt-handoff.md` 负责把一批提示词写入 `batch.json`，再通过确定性脚本 `scripts/prompt_page.py` 渲染成本地的 `prompts.html` 网页——全程不调用 `image_gen`，也不涉及 chatgpt.com 的任何自动化。

根路由器和目录脚本都不会枚举类型或 profile ID。添加一个有效的类型或 profile 不需要编辑其中任何一个文件。

## 扩展

请遵循 `references/image-profile-authoring.md`。概要如下：

1. 使用 `image-type/v2` 在 `references/types/<type-id>/TYPE.md` 中添加类型。
2. 在该类型的 `profiles/` 目录下至少添加一个使用 `image-profile/v1` 的 profile。
3. 将每一个必需的参考文件放在对应的类型目录中。
4. 保持 profile 的 `type` 和 `kind` 与其所在类型一致。
5. 在完整目录中只保留一个 fallback 类型。
6. 运行下面列出的验证命令。

目录排序按 `sort_order` 再按 ID 确定，因此相同的排序值也是安全的。选择依据是标题、摘要和关键词的语义，而不是脆弱的评分表。

## 隐私与安全

- 图像生成通过 Codex 内置的 `image_gen` 工具进行；不涉及任何第三方网站，此工作流也不会读取 Cookie、已保存的密码、浏览器配置文件或其他身份验证数据。
- Agent 通过 `view_image` 加载的参考图像只停留在当前 Codex 会话内，不会上传到任何外部服务。
- 除非客户在请求中明确要求直接生成，否则 ZhiPhoto 会先把最终提示词保存到本地，并在客户确认后才真正调用 `image_gen` 生成图像。
- 提示词交接模式只编写提示词并写入本地网页，绝不会打开、跳转、链接或提交任何内容到 chatgpt.com 或其他网站。把提示词粘贴进你自己的 ChatGPT 会话、按提示徽章的要求附上参考图、查看生成结果，这几步都由你自己完成，ZhiPhoto 不会替你做。
- 成人 profile 要求主体明确为成年人。内置成人指导排除了未成年人、年龄不明确、胁迫、剥削、明确的性行为，以及对真实人物进行欺骗性的性描绘；同时仍须遵守适用的平台安全要求。
- 生成结果可能包含错误或瑕疵。工作流会验证已保存的文件，并从视觉上检查它是否符合请求，但无法保证事实或艺术上的正确性。

## 限制

- 需要 Codex 及其内置的 `image_gen` 工具可用。
- 支持的工作流面向从文本简报生成一张新图像、按 shot list 逐张生成明确要求的正文多图，以及修改本次会话已生成或客户提供的既有图像；正文多图既支持客户提供 personal-IP 模板，也支持在完全未提供模板意图时使用 Xiaohei 回退。其他图像类型的通用批量生成不在支持范围内。
- 不会静默回退到其他 API、命令行调用、Computer Use 或其他生成工具；如果 `image_gen` 不可用或调用失败，工作流会停止并报告问题，而不是静默改用别的方式。
- 如果无法唯一定位本次调用生成的输出文件，或文件、格式、视觉检查未能通过验证，工作流会停止并报告失败的部分，而不是宣称整组已完成。
- Codex `image_gen` 的界面和生成可用性可能独立于本仓库发生变化。
- 输出质量、格式、尺寸、生成耗时以及安全执行由 Codex 的 `image_gen` 工具决定，并可能独立于本项目发生变化。
- 默认传输目前使用 Mac 的本地时间生成输出文件名。

## 验证

在仓库根目录运行：

```bash
python3 skills/zhiphoto/scripts/image_catalog.py validate
python3 skills/zhiphoto/scripts/image_catalog.py list-types --format json
python3 -m unittest discover -s tests -v
```

如果标准 Codex 技能验证器可用，也可以运行：

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skills/zhiphoto
```

## 许可证

Copyright 2026 zhi-ai-lab.

根据 [Apache License 2.0](LICENSE) 授权。归属信息请参阅 [NOTICE](NOTICE)。

## 致谢

`article-illustration` 正文配图类型参考了 [Ian Xiaohei Illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations)。感谢 Ian 的原创工作。这份致谢仅针对 `article-illustration` 类型；ZhiPhoto 整体并非改编自 Ian Xiaohei Illustrations。

## 维护者

[Jason Shen 的 X](https://x.com/jason_shen_2000)
