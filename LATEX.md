# LaTeX 编译环境

本项目使用 Docker 提供 TeX Live，不需要在 macOS 宿主机安装 LaTeX。

## 当前论文主稿

当前迭代主稿为：

```text
论文/article_skycausal_v3_cn.tex
```

编译命令：

```bash
bash scripts/latex-build.sh 论文/article_skycausal_v3_cn.tex xelatex
```

主稿图表由冻结分析 JSON 重建：

```bash
./codebase/SkyEngine/.venv/bin/python 论文/scripts/generate_v3_figures.py
```

图形输出和证据哈希位于 `论文/figures/v3/`。结果图必须通过该脚本更新，禁止在
LaTeX 中手工改写图内数值。

`article.tex` 与 `article_skycausal_v2.tex` 是历史叙事草稿，不再作为当前论文主线。
版本边界和结果更新规则见 `论文/README_v3.md`。

## 首次准备

确保 Docker Desktop 已启动，然后在项目根目录执行：

```bash
docker compose -f compose.latex.yaml build latex
```

## 命令行编译

英文主稿使用 pdfLaTeX：

```bash
bash scripts/latex-build.sh 论文/article_skycausal_v2.tex pdf
```

含中文的稿件使用 XeLaTeX：

```bash
bash scripts/latex-build.sh 论文/article.tex xelatex
```

PDF 和辅助文件输出到 `论文/build/`。清理英文主稿的构建产物：

```bash
bash scripts/latex-build.sh 论文/article_skycausal_v2.tex clean
```

## VS Code / Trae

安装扩展 `LaTeX Workshop`（扩展 ID：`james-yu.latex-workshop`）。项目配置会：

- 保存 `.tex` 文件时通过 Docker 自动编译；
- 在编辑器标签页中预览 PDF；
- 支持 SyncTeX 正反向定位；
- 默认使用 pdfLaTeX，并提供 XeLaTeX recipe。

也可以按 `Cmd+Shift+B` 运行默认构建任务。首次编译会等待 Docker 镜像构建完成。

可选扩展：

- `LTeX+`（`ltex-plus.vscode-ltex-plus`）：英文语法和学术写作检查；
- `Code Spell Checker`（`streetsidesoftware.code-spell-checker`）：轻量拼写检查。

不要再安装 `texlab` 或其他会同时接管 LaTeX 构建的扩展，以免与 LaTeX Workshop 重复触发编译。
