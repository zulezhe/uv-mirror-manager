"""Command-line interface for UVM."""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from uvm import __version__
from uvm.constants import EXIT_ERROR, EXIT_INVALID_ARGS, EXIT_SUCCESS
from uvm.core.mirror import MirrorManager
from uvm.core.speedtest import SpeedTester

# Fix Windows console encoding for Chinese output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

# Create Typer app
app = typer.Typer(
    name="uvm",
    help="UV镜像源管理工具 - 一键管理uv的PyPI镜像源",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True,
)

# Rich console for pretty output
console = Console()


def get_mirror_manager() -> MirrorManager:
    """Get mirror manager instance."""
    return MirrorManager()


def format_mirror_list(mirrors_data: list[dict]) -> Table:
    """Format mirror list as rich table."""
    table = Table(title="可用镜像源")
    table.add_column("状态", style="cyan", no_wrap=True)
    table.add_column("名称", style="magenta")
    table.add_column("URL", style="blue")
    table.add_column("地区", style="green")
    table.add_column("类型", style="yellow")
    table.add_column("描述", style="dim")

    for mirror in mirrors_data:
        status = "->" if mirror["current"] else "  "
        name = Text(mirror["name"])
        if mirror["current"]:
            name.stylize("bold green")

        url = Text(mirror["url"], style="blue")
        region = mirror["region"]
        mirror_type = "内置" if mirror["builtin"] else "自定义"
        description = mirror["description"] or "-"

        table.add_row(status, name, url, region, mirror_type, description)

    return table


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="显示版本信息"
    ),
) -> None:
    """UV镜像源管理工具主入口."""
    if version:
        console.print(f"uvm {__version__}")
        raise typer.Exit(EXIT_SUCCESS)


@app.command()
@app.command("ls")
def list() -> None:
    """列出所有可用的镜像源."""
    try:
        manager = get_mirror_manager()
        mirrors_data = manager.list_mirrors(show_current=True)

        if not mirrors_data:
            console.print("[X] 没有找到任何镜像源", style="red")
            raise typer.Exit(EXIT_ERROR)

        table = format_mirror_list(mirrors_data)
        console.print(table)

        # 显示统计信息
        stats = manager.get_mirror_statistics()
        console.print(f"\n[INFO] 总计: {stats['total_mirrors']} 个镜像源")
        console.print(f"   内置: {stats['builtin_mirrors']} 个")
        console.print(f"   自定义: {stats['custom_mirrors']} 个")

    except Exception as e:
        console.print(f"[X] 列出镜像源失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)


@app.command()
@app.command("cur")
def current() -> None:
    """显示当前使用的镜像源."""
    try:
        manager = get_mirror_manager()
        current_mirror = manager.get_current_mirror()
        current_url = manager._config.get_current_index_url()

        if current_mirror:
            console.print(f"[INFO] 当前镜像源: {current_mirror.name}")
            console.print(f"[URL] URL: {current_mirror.url}")
            if current_mirror.description:
                console.print(f"[DESC] 描述: {current_mirror.description}")
        elif current_url:
            console.print(f"[INFO] 当前镜像源: 自定义URL")
            console.print(f"[URL] URL: {current_url}")
        else:
            console.print("[INFO] 当前使用默认官方源", style="yellow")

    except Exception as e:
        console.print(f"[X] 获取当前镜像源失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)


@app.command()
@app.command("u")
def use(name: str = typer.Argument(..., help="镜像源名称")) -> None:
    """切换到指定的镜像源."""
    try:
        manager = get_mirror_manager()
        mirror = manager.get_mirror_by_name(name)

        if not mirror:
            console.print(f"[X] 未找到镜像源: {name}", style="red")
            console.print("[INFO] 使用 'uvm list' 查看可用镜像源", style="yellow")
            raise typer.Exit(EXIT_INVALID_ARGS)

        success = manager.use_mirror(name)
        if success:
            console.print(f"[OK] 已切换到镜像源: {mirror.name}", style="green")
            console.print(f"[URL] URL: {mirror.url}")
        else:
            console.print(f"[X] 切换镜像源失败: {name}", style="red")
            raise typer.Exit(EXIT_ERROR)

    except Exception as e:
        console.print(f"[X] 切换镜像源失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)


@app.command()
@app.command("t")
def test(
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="是否使用缓存结果"),
    timeout: float = typer.Option(5.0, "--timeout", "-t", help="超时时间（秒）"),
) -> None:
    """测试镜像源速度并排序."""

    async def run_test():
        try:
            manager = get_mirror_manager()
            speed_tester = SpeedTester(timeout=timeout)
            mirrors = manager.all_mirrors

            if not mirrors:
                console.print("[X] 没有找到任何镜像源", style="red")
                raise typer.Exit(EXIT_ERROR)

            console.print("[INFO] 开始测试镜像源速度...", style="blue")
            console.print(f"[INFO] 将测试 {len(mirrors)} 个镜像源\n")

            results = await speed_tester.test_and_cache(mirrors, use_cache=use_cache)

            # 显示结果表格
            table_str = speed_tester.format_results_table(results)
            console.print(table_str)

            # 显示推荐
            recommendations = speed_tester.get_recommendations(results, 3)
            if recommendations:
                console.print("\n[TOP] 推荐镜像源 (前3名):", style="green bold")
                for i, result in enumerate(recommendations, 1):
                    console.print(
                        f"  {i}. {result.mirror.name} - {result.response_time:.3f}s"
                    )

        except Exception as e:
            console.print(f"[X] 测试失败: {e}", style="red")
            raise typer.Exit(EXIT_ERROR)

    # Run async function
    asyncio.run(run_test())


@app.command()
@app.command("r")
def reset() -> None:
    """恢复到官方默认镜像源."""
    try:
        manager = get_mirror_manager()

        console.print("[WARN] 即将恢复到官方默认镜像源", style="yellow")
        if typer.confirm("确定要继续吗？"):
            manager.reset_mirror()
            console.print("[OK] 已恢复到官方默认镜像源", style="green")
        else:
            console.print("[X] 操作已取消", style="red")
            raise typer.Exit(EXIT_SUCCESS)

    except Exception as e:
        console.print(f"[X] 恢复默认镜像源失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)


@app.command()
@app.command("a")
def add(
    name: str = typer.Argument(..., help="镜像源名称"),
    url: str = typer.Argument(..., help="镜像源URL"),
    description: str = typer.Option("", "--description", "-d", help="镜像源描述"),
    region: str = typer.Option("CN", "--region", "-r", help="地区代码"),
) -> None:
    """添加自定义镜像源."""
    try:
        manager = get_mirror_manager()

        # 检查名称是否已存在
        if manager.get_mirror_by_name(name):
            console.print(f"[X] 镜像源名称已存在: {name}", style="red")
            raise typer.Exit(EXIT_INVALID_ARGS)

        # 验证URL
        if not manager.validate_mirror_url(url):
            console.print("[X] 无效的镜像源URL，必须以/simple结尾", style="red")
            raise typer.Exit(EXIT_INVALID_ARGS)

        success = manager.add_custom_mirror(name, url, description, region)
        if success:
            console.print(f"[OK] 已添加自定义镜像源: {name}", style="green")
            console.print(f"[URL] URL: {url}")
            if description:
                console.print(f"[DESC] 描述: {description}")
        else:
            console.print(f"[X] 添加镜像源失败: {name}", style="red")
            raise typer.Exit(EXIT_ERROR)

    except Exception as e:
        console.print(f"[X] 添加镜像源失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)


@app.command()
@app.command("rm")
def remove(name: str = typer.Argument(..., help="要删除的镜像源名称")) -> None:
    """删除自定义镜像源."""
    try:
        manager = get_mirror_manager()
        mirror = manager.get_mirror_by_name(name)

        if not mirror:
            console.print(f"[X] 未找到镜像源: {name}", style="red")
            raise typer.Exit(EXIT_INVALID_ARGS)

        if mirror.builtin:
            console.print("[X] 不能删除内置镜像源", style="red")
            raise typer.Exit(EXIT_INVALID_ARGS)

        console.print(f"[WARN] 即将删除自定义镜像源: {name}", style="yellow")
        if typer.confirm("确定要继续吗？"):
            success = manager.remove_custom_mirror(name)
            if success:
                console.print(f"[OK] 已删除自定义镜像源: {name}", style="green")
            else:
                console.print(f"[X] 删除镜像源失败: {name}", style="red")
                raise typer.Exit(EXIT_ERROR)
        else:
            console.print("[X] 操作已取消", style="red")
            raise typer.Exit(EXIT_SUCCESS)

    except Exception as e:
        console.print(f"[X] 删除镜像源失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)  # noqa: B904


@app.command()
@app.command("s")
def search(query: str = typer.Argument(..., help="搜索关键词")) -> None:
    """搜索镜像源."""
    try:
        manager = get_mirror_manager()
        results = manager.search_mirrors(query)

        if not results:
            console.print(f"[X] 未找到匹配的镜像源: {query}", style="red")
            raise typer.Exit(EXIT_SUCCESS)

        console.print(f"[SEARCH] 搜索结果: '{query}' ({len(results)} 个)\n")

        # 转换为列表数据格式
        mirrors_data = []
        current_mirror = manager.get_current_mirror()
        for mirror in results:
            mirrors_data.append(
                {
                    "name": mirror.name,
                    "url": str(mirror.url),
                    "region": mirror.region,
                    "builtin": mirror.builtin,
                    "description": mirror.description,
                    "current": current_mirror and mirror.name == current_mirror.name,
                }
            )

        table = format_mirror_list(mirrors_data)
        console.print(table)

    except Exception as e:
        console.print(f"[X] 搜索失败: {e}", style="red")
        raise typer.Exit(EXIT_ERROR)  # noqa: B904


if __name__ == "__main__":
    app()
