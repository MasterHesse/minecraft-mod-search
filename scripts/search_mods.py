#!/usr/bin/env python3
"""
Minecraft Java Mod 多平台搜索脚本
- Modrinth (主平台，国内可直连)
- CurseForge (备选，需 API Key)
- Planet Minecraft (补充，网页抓取)
"""

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# 在 Windows 下强制 stdout/stderr 使用 UTF-8，避免中文/特殊字符 GBK 编码错误
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from typing import Optional

# requests 可能不在标准库中，使用 urllib 作为 fallback
try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    print("ERROR: urllib not available", file=sys.stderr)
    sys.exit(1)

# ============================================================
# 常量配置
# ============================================================
MODRINTH_BASE = "https://api.modrinth.com/v2"
CURSEFORGE_BASE = "https://api.curseforge.com/v1"

DEFAULT_TIMEOUT = 8  # 秒
MAX_RESULTS_PER_PLATFORM = 20
SORT_SCORE_WEIGHTS = {
    "downloads": 0.30,
    "update_frequency": 0.25,
    "rating": 0.25,
    "version_match": 0.20,
}

# ============================================================
# TACZ 枪械生态常量
# ============================================================
TACZ_MOD_SLUG = "timeless-and-classics-zero"
TACZ_MOD_NAME = "Timeless and Classics Zero (TaCZ)"
TACZ_MODRINTH_URL = f"https://modrinth.com/mod/{TACZ_MOD_SLUG}"

# 触发"枪械意图"的关键词（中英文混合）
TACZ_GUN_KEYWORDS = {
    # 中文
    "枪", "枪械", "枪包", "枪mod", "枪模组", "射击", "武器", "手枪", "步枪",
    "狙击", "霰弹", "冲锋枪", "机枪", "左轮", "燧发枪", "火枪", "枪战",
    "现代战争", "军事", "弹药", "子弹",
    # 英文
    "gun", "firearm", "weapon", "pistol", "rifle", "sniper", "shotgun",
    "smg", "submachine", "lmg", "machine gun", "revolver", "musket",
    "gunpack", "gun pack", "tacz", "tac", "bullet", "ammo", "ammunition",
    "fps", "combat", "warfare", "military",
}

# Modrinth 上 TACZ 枪包的典型 category 标签
TACZ_GUNPACK_CATEGORIES = {"equipment", "adventure", "game-mechanics"}

# TACZ 支持的 Minecraft 版本范围（Forge 官方版）
TACZ_SUPPORTED_VERSIONS = {
    "1.18.2", "1.19", "1.19.1", "1.19.2", "1.20", "1.20.1",
}

# ============================================================
# Create 机械动力生态常量
# ============================================================
CREATE_MOD_SLUG = "create"
CREATE_MOD_NAME = "Create (机械动力)"
CREATE_MODRINTH_URL = "https://modrinth.com/mod/create"

# 触发"机械/自动化意图"的关键词（中英文混合）
CREATE_KEYWORDS = {
    # 中文
    "机械", "机械动力", "自动化", "传送带", "齿轮", "活塞", "动力",
    "轴承", "铁路", "火车", "矿车", "旋转", "应力", "流水线",
    "工厂", "制造", "加工", "搅拌", "碾压", "装配", "压缩",
    "机械臂", "部署器", "红石机械", "蒸汽", "风车", "水车",
    # 英文
    "create mod", "create addon", "create ",  # 注意 "create " 带空格避免误匹配
    "conveyor", "belt", "gear", "pulley", "bearing", "piston",
    "automation", "factory", "assembly", "mechanical",
    "train", "railway", "steam", "windmill", "waterwheel",
    "rotational", "kinetic", "stress", "cogwheel", "shaft",
    "deployer", "mixer", "press", "millstone", "crusher",
}

# Create 在 Modrinth 上的典型 category 标签（附属 mod 分布）
CREATE_ADDON_CATEGORIES = {"technology", "equipment", "transportation", "utility"}

# Create 支持的 Minecraft 版本范围
CREATE_SUPPORTED_VERSIONS = {
    "1.14.4", "1.15.2", "1.16.5", "1.18.2", "1.19.2", "1.20.1",
}


# ============================================================
# 数据模型
# ============================================================
@dataclass
class ModDependency:
    name: str
    slug: str
    required: bool
    downloads: int = 0
    url: str = ""


@dataclass
class ModResult:
    # 基础信息
    name: str
    slug: str
    author: str
    description: str
    downloads: int
    categories: list
    game_versions: list
    loaders: list
    favorites: int = 0
    latest_version: str = ""
    published: str = ""
    updated: str = ""
    icon_url: str = ""
    # 链接
    modrinth_url: str = ""
    curseforge_url: str = ""
    curseforge_id: int = 0
    # 依赖
    dependencies: list = None
    # 评分
    score: float = 0.0
    # 警告
    warnings: list = None
    # 来源
    platform: str = ""

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.warnings is None:
            self.warnings = []
        if isinstance(self.game_versions, str):
            self.game_versions = [self.game_versions]
        if isinstance(self.loaders, str):
            self.loaders = [self.loaders]


# ============================================================
# HTTP 工具
# ============================================================
def http_get(url: str, headers: dict = None, timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    """发送 GET 请求，返回 JSON"""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", "MinecraftModSearch/1.0")

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {url}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason} — {url}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {e} — {url}", file=sys.stderr)
        return None


# ============================================================
# TACZ 枪械意图识别 & 枪包搜索
# ============================================================

def detect_gun_intent(query: str) -> bool:
    """
    判断用户输入是否属于枪械/武器相关需求。
    任意关键词命中即返回 True。
    """
    q_lower = query.lower()
    for kw in TACZ_GUN_KEYWORDS:
        if kw in q_lower:
            return True
    return False


@dataclass
class TaczGunpackResult:
    """TACZ 枪包搜索结果（轻量包装，复用 ModResult 格式）"""
    mod_result: "ModResult"
    is_tacz_gunpack: bool = True  # 标记来源为 TACZ 枪包搜索


# 中文枪械关键词 → 英文搜索词映射（Modrinth 枪包标题大多为英文）
_CN_GUN_MAP = {
    "步枪": "rifle", "狙击": "sniper", "霰弹": "shotgun",
    "手枪": "pistol", "冲锋枪": "smg", "机枪": "machine gun",
    "左轮": "revolver", "燧发枪": "musket", "火枪": "musket",
    "枪": "gun", "枪械": "gun", "枪包": "gun pack",
    "武器": "weapon", "弹药": "ammo", "子弹": "bullet",
    "射击": "shooting", "军事": "military", "战争": "warfare",
    "现代": "modern", "废土": "fallout", "末日": "apocalypse",
    "科幻": "scifi", "未来": "futuristic", "西部": "western",
}


def _translate_gun_query(query: str) -> str:
    """将中文枪械查询词转换为英文，提升 Modrinth 搜索命中率"""
    import re
    q = query.lower().strip()
    for cn, en in _CN_GUN_MAP.items():
        if cn in q:
            q = q.replace(cn, en)
    # 移除剩余中文字符，保留英文词和翻译结果
    q = re.sub(r'[\u4e00-\u9fff]+', ' ', q).strip()
    q = re.sub(r'\s+', ' ', q).strip()
    return q or "gun"


def search_tacz_gunpacks(
    query: str,
    version: str = None,
    limit: int = 10,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[bool, list]:
    """
    TACZ 枪包专项搜索。

    搜索策略（按优先级）：
      1. query="tacz <英文关键词>" + filters="equipment AND version"
      2. query="tacz <英文关键词>"（不加分类过滤）
      3. 若均无结果，返回 (False, []) 触发 fallback

    Returns:
        (found: bool, mods: list[ModResult])
    """
    endpoint = f"{MODRINTH_BASE}/search"
    all_results = []
    seen_slugs: set = set()

    en_query = _translate_gun_query(query)

    # 构造策略：使用 Modrinth facets JSON 语法（[[...],[...]] 格式）
    strategies = []

    # 策略1：equipment 分类 + 版本过滤
    facets1 = [["categories:equipment"]]
    if version:
        facets1.append([f"versions:{version}"])
    strategies.append({
        "query": f"tacz {en_query}",
        "facets": facets1,
        "label": f"策略1(equipment+{version or 'any'})",
    })

    # 策略2：只加版本过滤，不限分类
    facets2 = []
    if version:
        facets2.append([f"versions:{version}"])
    strategies.append({
        "query": f"tacz {en_query}",
        "facets": facets2 if facets2 else None,
        "label": f"策略2(no-cat+{version or 'any'})",
    })

    for strategy in strategies:
        params = [
            ("query", strategy["query"]),
            ("limit", str(min(limit, 20))),
            ("index", "downloads"),
        ]
        if strategy["facets"]:
            params.append(("facets", json.dumps(strategy["facets"])))

        url = endpoint + "?" + "&".join(
            f"{k}={urllib.parse.quote(str(v))}" for k, v in params
        )
        data = http_get(url, timeout=timeout)

        if not data or "hits" not in data:
            print(f"  [TACZ] {strategy['label']}: 请求失败或超时", file=sys.stderr)
            continue

        hits = data.get("hits", [])
        print(f"  [TACZ] {strategy['label']}: 返回 {len(hits)} 条", file=sys.stderr)

        for hit in hits:
            slug = hit.get("slug", "").lower()
            title = hit.get("title", "").lower()

            if not _is_tacz_related(slug, title, hit.get("description", "")):
                continue
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            deps = fetch_modrinth_dependencies(hit.get("project_id", ""), timeout)
            warnings = _check_warnings(hit, version)

            mod = ModResult(
                name=hit.get("title", ""),
                slug=slug,
                author=hit.get("author", ""),
                description=hit.get("description", ""),
                downloads=hit.get("downloads", 0),
                categories=hit.get("categories", []),
                game_versions=[hit.get("latest_version", "")],
                loaders=hit.get("loaders") or [],
                favorites=0,
                latest_version=hit.get("latest_version", ""),
                published=hit.get("date_created", "")[:10] if hit.get("date_created") else "",
                updated=hit.get("date_modified", "")[:10] if hit.get("date_modified") else "",
                icon_url=hit.get("icon_url", ""),
                modrinth_url=f"https://modrinth.com/mod/{slug}",
                dependencies=deps,
                warnings=warnings,
                platform="modrinth",
            )
            all_results.append(mod)

        if len(all_results) >= 3:
            break

    if not all_results:
        return False, []

    for mod in all_results:
        mod.score = calculate_mod_score(mod, version)
    all_results.sort(key=lambda m: m.score, reverse=True)

    return True, all_results[:limit]


def _is_tacz_related(slug: str, title: str, description: str) -> bool:
    """判断一个 Modrinth 条目是否是 TACZ 相关的枪包"""
    combined = f"{slug} {title} {description[:200]}".lower()
    tacz_markers = ["tacz", "timeless and classics zero", "timeless-and-classics-zero",
                    "timeless-and-classics", "gun pack", "gunpack"]
    return any(marker in combined for marker in tacz_markers)


def _check_warnings(hit: dict, version: str = None) -> list[str]:
    """通用警告检查（更新时间 + 版本兼容）"""
    warnings = []
    updated_date = hit.get("date_modified", "")
    if updated_date:
        try:
            update_time = datetime.fromisoformat(updated_date.replace("Z", "+00:00"))
            days_since = (datetime.now(update_time.tzinfo) - update_time).days
            if days_since > 365:
                warnings.append("久未更新")
            elif days_since > 180:
                warnings.append("更新较久")
        except Exception:
            pass
    return warnings


def build_tacz_base_mod(version: str = None) -> "ModResult":
    """构造 TACZ 本体的 ModResult 占位（用于在结果中优先展示基础 Mod）"""
    return ModResult(
        name="[TaCZ] Timeless and Classics Zero",
        slug=TACZ_MOD_SLUG,
        author="Timeless Squad",
        description=(
            "最沉浸、最可定制的 Minecraft 现代 FPS 体验。"
            "支持第三方枪包扩展，提供精致的射击动画和改装系统。"
            "枪包放入 .minecraft/tacz/ 目录即可加载。"
        ),
        downloads=17_000_000,
        favorites=2749,
        categories=["adventure", "equipment"],
        game_versions=list(TACZ_SUPPORTED_VERSIONS),
        loaders=["forge"],
        latest_version="1.1.4",
        modrinth_url=TACZ_MODRINTH_URL,
        warnings=(
            ["⚠️ 当前版本不在 TACZ 官方支持范围内，请关注社区移植版"]
            if version and version not in TACZ_SUPPORTED_VERSIONS
            else []
        ),
        platform="modrinth",
        score=99.0,
    )


def format_tacz_header(version: str = None, loader: str = None) -> str:
    """生成 TACZ 搜索模式的标题提示"""
    lines = [
        "\n" + "=" * 60,
        "  [TACZ] Minecraft 枪械 Mod 搜索 — TACZ 优先模式",
        f"  版本: {version or '不限'}  |  加载器: {loader or 'Forge（TACZ 默认）'}",
        "=" * 60,
        "",
        "  [第一步] 推荐基础框架",
        "  " + "-" * 40,
        f"  >> {TACZ_MOD_NAME}",
        f"     Modrinth: {TACZ_MODRINTH_URL}",
        f"     支持版本: 1.18.2 / 1.19.x / 1.20-1.20.1 (Forge)",
        "     安装枪包：将 .zip 放入 .minecraft/tacz/ 后执行 /tacz reload",
        "",
        "  [第二步] TACZ 枪包搜索结果",
        "  " + "-" * 40,
    ]
    return "\n".join(lines)


# ============================================================
# Create 机械动力 — 意图识别 & 附属 mod 搜索
# ============================================================

def detect_create_intent(query: str) -> bool:
    """
    判断用户输入是否属于机械/自动化/科技相关需求。
    任意关键词命中即返回 True。
    """
    q_lower = query.lower()
    for kw in CREATE_KEYWORDS:
        if kw in q_lower:
            return True
    return False


def search_create_addons(
    query: str,
    version: str = None,
    loader: str = None,
    limit: int = 10,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple:
    """
    Create 机械动力附属 mod 专项搜索。

    搜索策略（按优先级）：
      1. query="create <关键词>" + facets=[technology, version]
      2. query="create <关键词>" + facets=[version]（不限分类）
      3. 若均无结果，返回 (False, []) 触发 fallback

    Returns:
        (found: bool, mods: list[ModResult])
    """
    endpoint = f"{MODRINTH_BASE}/search"
    all_results = []
    seen_slugs = set()

    en_query = _translate_create_query(query)

    strategies = []

    # 策略1：technology 分类 + 版本过滤
    facets1 = [["categories:technology"]]
    if version:
        facets1.append([f"versions:{version}"])
    if loader:
        facets1.append([f"loaders:{loader}"])
    strategies.append({
        "query": f"create {en_query}",
        "facets": facets1,
        "label": f"策略1(technology+{version or 'any'})",
    })

    # 策略2：不限分类 + 版本过滤
    facets2 = []
    if version:
        facets2.append([f"versions:{version}"])
    strategies.append({
        "query": f"create {en_query}",
        "facets": facets2 if facets2 else None,
        "label": f"策略2(no-cat+{version or 'any'})",
    })

    for strategy in strategies:
        params = [
            ("query", strategy["query"]),
            ("limit", str(min(limit, 20))),
            ("index", "downloads"),
        ]
        if strategy["facets"]:
            params.append(("facets", json.dumps(strategy["facets"])))

        url = endpoint + "?" + "&".join(
            f"{k}={urllib.parse.quote(str(v))}" for k, v in params
        )
        data = http_get(url, timeout=timeout)

        if not data or "hits" not in data:
            print(f"  [Create] {strategy['label']}: 请求失败或超时", file=sys.stderr)
            continue

        hits = data.get("hits", [])
        print(f"  [Create] {strategy['label']}: 返回 {len(hits)} 条", file=sys.stderr)

        for hit in hits:
            slug = hit.get("slug", "").lower()
            title = hit.get("title", "").lower()

            # 跳过 Create 本体（单独展示在 header 中）
            if slug == CREATE_MOD_SLUG:
                continue

            # 过滤：标题或描述中需包含 "create"
            if not _is_create_related(slug, title, hit.get("description", "")):
                continue

            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            deps = fetch_modrinth_dependencies(hit.get("project_id", ""), timeout)
            warnings = _check_warnings(hit, version)

            mod = ModResult(
                name=hit.get("title", ""),
                slug=slug,
                author=hit.get("author", ""),
                description=hit.get("description", ""),
                downloads=hit.get("downloads", 0),
                categories=hit.get("categories", []),
                game_versions=[hit.get("latest_version", "")],
                loaders=hit.get("loaders") or [],
                favorites=0,
                latest_version=hit.get("latest_version", ""),
                published=hit.get("date_created", "")[:10] if hit.get("date_created") else "",
                updated=hit.get("date_modified", "")[:10] if hit.get("date_modified") else "",
                icon_url=hit.get("icon_url", ""),
                modrinth_url=f"https://modrinth.com/mod/{slug}",
                dependencies=deps,
                warnings=warnings,
                platform="modrinth",
            )
            all_results.append(mod)

        if len(all_results) >= 5:
            break

    if not all_results:
        return False, []

    for mod in all_results:
        mod.score = calculate_mod_score(mod, version)
    all_results.sort(key=lambda m: m.score, reverse=True)

    return True, all_results[:limit]


# 中文机械/自动化关键词 → 英文搜索词映射
_CN_CREATE_MAP = {
    "机械": "mechanical", "机械动力": "create", "自动化": "automation",
    "传送带": "conveyor belt", "齿轮": "gear cogwheel", "活塞": "piston",
    "轴承": "bearing", "铁路": "railway train", "火车": "train",
    "矿车": "minecart", "旋转": "rotational", "应力": "stress",
    "流水线": "assembly line", "工厂": "factory", "制造": "manufacturing",
    "加工": "processing", "搅拌": "mixing", "碾压": "crushing",
    "装配": "assembly", "压缩": "pressing", "机械臂": "deployer",
    "部署器": "deployer", "红石机械": "redstone mechanical",
    "蒸汽": "steam", "风车": "windmill", "水车": "waterwheel",
    "动力": "kinetic", "科技": "technology",
}


def _translate_create_query(query: str) -> str:
    """将中文机械/自动化查询词转换为英文，提升 Modrinth 搜索命中率"""
    import re
    q = query.lower().strip()
    # 优先匹配长词（避免"机械动力"只替换了"机械"）
    for cn, en in sorted(_CN_CREATE_MAP.items(), key=lambda x: -len(x[0])):
        if cn in q:
            q = q.replace(cn, en, 1)
    # 移除剩余中文字符
    q = re.sub(r'[\u4e00-\u9fff]+', ' ', q).strip()
    q = re.sub(r'\s+', ' ', q).strip()
    return q or "create"


def _is_create_related(slug: str, title: str, description: str) -> bool:
    """判断一个 Modrinth 条目是否是 Create 相关的附属 mod"""
    combined = f"{slug} {title} {description[:300]}".lower()
    create_markers = ["create", "createaddon", "create addon", "simplycreate"]
    # "create" 太常见，仅在 slug 或标题中出现时才认定为 Create 相关
    return any(marker in combined for marker in create_markers)


def format_create_header(version: str = None, loader: str = None) -> str:
    """生成 Create 搜索模式的标题提示"""
    lines = [
        "\n" + "=" * 60,
        "  [Create] Minecraft 机械动力 Mod 搜索 — Create 优先模式",
        f"  版本: {version or '不限'}  |  加载器: {loader or 'Forge / Fabric'}",
        "=" * 60,
        "",
        "  [第一步] 推荐基础框架",
        "  " + "-" * 40,
        f"  >> {CREATE_MOD_NAME}",
        f"     Modrinth: {CREATE_MODRINTH_URL}",
        f"     支持版本: 1.14.4 / 1.15.2 / 1.16.5 / 1.18.2 / 1.19.2 / 1.20.1",
        "     支持 Forge 和 Fabric 加载器",
        "",
        "  [第二步] Create 附属 Mod 搜索结果",
        "  " + "-" * 40,
    ]
    return "\n".join(lines)


# ============================================================
# Modrinth 搜索
# ============================================================
def search_modrinth(
    query: str,
    version: str = None,
    loader: str = None,
    category: str = None,
    limit: int = MAX_RESULTS_PER_PLATFORM,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[ModResult]:
    """从 Modrinth 搜索 Mod"""
    endpoint = f"{MODRINTH_BASE}/search"

    params = [("query", query), ("limit", str(min(limit, 100)))]
    facets_list = []

    if version:
        facets_list.append([f"versions:{version}"])
    if loader:
        facets_list.append([f"loaders:{loader}"])
    if category:
        facets_list.append([f"categories:{category}"])

    if facets_list:
        params.append(("facets", json.dumps(facets_list)))

    url = endpoint + "?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params)
    results = http_get(url, timeout=timeout)

    if not results or "hits" not in results:
        return []

    mods = []
    for hit in results.get("hits", []):
        # 获取详细依赖信息
        deps = fetch_modrinth_dependencies(hit.get("project_id", ""), timeout)
        warnings = []
        updated_date = hit.get("date_modified", "")

        # 检查更新状态
        if updated_date:
            try:
                update_time = datetime.fromisoformat(updated_date.replace("Z", "+00:00"))
                days_since = (datetime.now(update_time.tzinfo) - update_time).days
                if days_since > 365:
                    warnings.append("久未更新")
                elif days_since > 180:
                    warnings.append("更新较久")
            except Exception:
                pass

        # 检查版本兼容性
        if version and version not in (hit.get("latest_version", "") or ""):
            # 需要进一步检查 versions 字段
            pass

        mod = ModResult(
            name=hit.get("title", ""),
            slug=hit.get("slug", ""),
            author=hit.get("author", ""),
            description=hit.get("description", ""),
            downloads=hit.get("downloads", 0),
            favorites=0,
            categories=hit.get("categories", []),
            game_versions=[hit.get("latest_version", "")],
            loaders=hit.get("loaders", []) or [],
            latest_version=hit.get("latest_version", ""),
            published=hit.get("date_created", "")[:10] if hit.get("date_created") else "",
            updated=updated_date[:10] if updated_date else "",
            icon_url=hit.get("icon_url", ""),
            modrinth_url=f"https://modrinth.com/mod/{hit.get('slug', '')}",
            dependencies=deps,
            warnings=warnings,
            platform="modrinth",
        )
        mods.append(mod)

    return mods


def fetch_modrinth_dependencies(project_id: str, timeout: int = DEFAULT_TIMEOUT) -> list[ModDependency]:
    """获取 Modrinth Mod 的依赖列表"""
    if not project_id:
        return []

    url = f"{MODRINTH_BASE}/project/{project_id}/dependencies"
    data = http_get(url, timeout=timeout)

    if not data:
        return []

    # Modrinth /dependencies 可能返回 {"projects": [...], "versions": [...]}
    # 也可能直接返回 list（旧版 API）
    if isinstance(data, dict):
        projects = data.get("projects", [])
        deps = []
        for proj in projects:
            if not isinstance(proj, dict):
                continue
            deps.append(ModDependency(
                name=proj.get("title", ""),
                slug=proj.get("slug", ""),
                required=True,  # projects 列表中的均视为 required
                downloads=proj.get("downloads", 0),
                url=f"https://modrinth.com/mod/{proj.get('slug', '')}",
            ))
        return deps

    # 兼容旧版 list 格式
    deps = []
    for item in data:
        if not isinstance(item, dict):
            continue
        proj = item.get("project")
        if not proj or not isinstance(proj, dict):
            continue
        dep_type = item.get("dependency_type", "optional")
        deps.append(ModDependency(
            name=proj.get("title", ""),
            slug=proj.get("slug", ""),
            required=(dep_type == "required"),
            downloads=proj.get("downloads", 0),
            url=f"https://modrinth.com/mod/{proj.get('slug', '')}",
        ))
    return deps


def fetch_modrinth_project_details(slug: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    """获取 Modrinth Mod 完整详情"""
    url = f"{MODRINTH_BASE}/project/{urllib.parse.quote(slug)}"
    return http_get(url, timeout=timeout)


# ============================================================
# CurseForge 搜索
# ============================================================
def search_curseforge(
    query: str,
    version: str = None,
    loader: str = None,
    api_key: str = None,
    limit: int = MAX_RESULTS_PER_PLATFORM,
    timeout: int = 5,
) -> list[ModResult]:
    """从 CurseForge 搜索 Mod"""
    if not api_key:
        return []

    # 加载器映射
    loader_map = {"forge": 2, "fabric": 4, "liteloader": 3, "rift": 5}
    mod_loader = loader_map.get(loader) if loader else None

    endpoint = f"{CURSEFORGE_BASE}/games/432/mods/search"
    params = [
        ("gameId", "432"),
        ("searchFilter", query),
        ("sortField", "1"),  # popularity
        ("sortOrder", "desc"),
        ("pageSize", str(min(limit, 50))),
        ("classId", "6"),  # Minecraft Mod
    ]
    if version:
        params.append(("gameVersion", version))
    if mod_loader:
        params.append(("modLoaderType", str(mod_loader)))

    url = endpoint + "?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params)
    headers = {"X-API-Key": api_key}

    data = http_get(url, headers=headers, timeout=timeout)
    if not data or "data" not in data:
        return []

    mods = []
    for item in data.get("data", []):
        warnings = []
        date_modified = item.get("dateModified", "")
        if date_modified:
            try:
                dt = datetime.fromisoformat(date_modified.replace("Z", "+00:00"))
                days_since = (datetime.now(dt.tzinfo) - dt).days
                if days_since > 365:
                    warnings.append("久未更新")
                elif days_since > 180:
                    warnings.append("更新较久")
            except Exception:
                pass

        latest_file = item.get("latestFiles", [{}])[0] if item.get("latestFiles") else {}
        game_versions = latest_file.get("gameVersions", []) if latest_file else []

        mod = ModResult(
            name=item.get("name", ""),
            slug=item.get("slug", ""),
            author=item.get("authors", [{}])[0].get("name", "") if item.get("authors") else "",
            description=item.get("summary", ""),
            downloads=item.get("downloadCount", 0),
            favorites=0,
            categories=[c.get("name", "") for c in item.get("categories", [])],
            game_versions=game_versions,
            loaders=[loader] if loader else [],
            latest_version=latest_file.get("version", "") if latest_file else "",
            published=item.get("dateCreated", "")[:10] if item.get("dateCreated") else "",
            updated=date_modified[:10] if date_modified else "",
            icon_url=item.get("logo", {}).get("url", "") if item.get("logo") else "",
            curseforge_url=item.get("externalUrl", "") or f"https://www.curseforge.com/minecraft/mc-mods/{item.get('slug', '')}",
            curseforge_id=item.get("id", 0),
            dependencies=[],
            warnings=warnings,
            platform="curseforge",
        )
        mods.append(mod)

    return mods


# ============================================================
# 评分与排序
# ============================================================
def calculate_mod_score(mod: ModResult, target_version: str = None) -> float:
    """计算 Mod 综合评分 (0-100)"""
    scores = {}

    # 1. 下载量评分 (0-100，对数平滑)
    if mod.downloads > 0:
        scores["downloads"] = min(100, math.log10(mod.downloads + 1) / math.log10(100_000_000) * 100)
    else:
        scores["downloads"] = 0

    # 2. 更新频率评分 (0-100)
    if mod.updated:
        try:
            dt = datetime.fromisoformat(mod.updated.replace("Z", "+00:00"))
            days_since = (datetime.now(dt.tzinfo) - dt).days
            if days_since <= 30:
                scores["update_frequency"] = 100
            elif days_since <= 90:
                scores["update_frequency"] = 90
            elif days_since <= 180:
                scores["update_frequency"] = 70
            elif days_since <= 365:
                scores["update_frequency"] = 50
            else:
                scores["update_frequency"] = max(0, 30 - (days_since - 365) // 365 * 20)
        except Exception:
            scores["update_frequency"] = 50
    else:
        scores["update_frequency"] = 50

    # 3. 评价指数 (简化为下载量代理)
    scores["rating"] = scores["downloads"] * 0.5 + (100 if mod.favorites > 10000 else mod.favorites / 100)

    # 4. 版本匹配度 (0-100)
    if target_version:
        if target_version in mod.game_versions:
            scores["version_match"] = 100
        else:
            # 检查是否有相近版本
            target_major = ".".join(target_version.split(".")[:2])
            has_near = any(target_major in v for v in mod.game_versions if v)
            scores["version_match"] = 60 if has_near else 0
    else:
        scores["version_match"] = 100

    # 加权求和
    total = sum(SORT_SCORE_WEIGHTS[k] * scores.get(k, 0) for k in SORT_SCORE_WEIGHTS)
    return round(total, 1)


def merge_and_rank(
    modrinth_mods: list[ModResult],
    curseforge_mods: list[ModResult],
    target_version: str = None,
    top_n: int = 15,
) -> list[ModResult]:
    """合并多平台结果，去重并按评分排序"""
    seen = {}
    all_mods = []

    # 优先使用 Modrinth 数据
    for mod in modrinth_mods:
        key = mod.slug.lower()
        if key not in seen:
            seen[key] = mod
            all_mods.append(mod)
        else:
            # 保留下载量更高的
            existing = seen[key]
            if mod.downloads > existing.downloads:
                seen[key] = mod
                all_mods = [m if m.slug != mod.slug else mod for m in all_mods]

    # 合并 CurseForge（仅添加不重复的）
    for mod in curseforge_mods:
        key = mod.slug.lower()
        if key not in seen:
            seen[key] = mod
            all_mods.append(mod)
        else:
            existing = seen[key]
            # 如果 CurseForge 有 externalUrl 但 Modrinth 没有，补上
            if not existing.curseforge_url and mod.curseforge_url:
                existing.curseforge_url = mod.curseforge_url
                existing.curseforge_id = mod.curseforge_id

    # 计算所有 Mod 的评分
    for mod in all_mods:
        mod.score = calculate_mod_score(mod, target_version)
        # 添加版本不兼容警告
        if target_version and target_version not in mod.game_versions and mod.game_versions:
            if "版本不兼容" not in mod.warnings:
                mod.warnings.append(f"与 {target_version} 不兼容")

    # 排序：评分降序
    all_mods.sort(key=lambda m: m.score, reverse=True)

    return all_mods[:top_n]


def add_dependency_mods(mods: list[ModResult], timeout: int = DEFAULT_TIMEOUT) -> list[ModResult]:
    """补充缺失的前置依赖 Mod"""
    result = list(mods)
    seen_slugs = {m.slug.lower() for m in mods}

    for mod in mods:
        for dep in mod.dependencies:
            if dep.required and dep.slug.lower() not in seen_slugs and dep.slug:
                seen_slugs.add(dep.slug.lower())
                # 查询依赖 Mod 详情
                dep_details = search_modrinth(dep.slug, limit=1, timeout=timeout)
                if dep_details:
                    dep_mod = dep_details[0]
                    dep_mod.score = max(0, dep_mod.score - 10)  # 依赖 Mod 降权
                    result.append(dep_mod)
                else:
                    # 如果查不到，创建占位
                    placeholder = ModResult(
                        name=dep.name or dep.slug,
                        slug=dep.slug,
                        author="",
                        description=f"[前置依赖] 所需前置模组",
                        downloads=dep.downloads,
                        dependencies=[],
                        warnings=["需前置依赖"],
                        platform="dependency",
                    )
                    result.append(placeholder)

    result.sort(key=lambda m: m.score, reverse=True)
    return result


# ============================================================
# 整合包兼容性检查
# ============================================================

# 已知硬性冲突：任意两者不可同时安装
HARD_CONFLICTS = {
    ("optifine", "sodium"): ("OptiFine", "Sodium", "两者均为渲染优化 Mod，功能重叠，同时安装会冲突"),
    ("optifine", "iris"): ("OptiFine", "Iris", "OptiFine 着色器与 Iris 着色器互斥"),
    ("optifine", "embeddium"): ("OptiFine", "Embeddium", "渲染引擎冲突"),
    ("optifine", "rubidium"): ("OptiFine", "Rubidium", "渲染引擎冲突"),
    ("sodium", "iris"): None,  # 已在 Modrinth 中处理，兼容
    ("ae2", "refined-storage"): ("AE2", "Refined Storage", "两个存储系统不可同时启用"),
    ("ae2", "refinedstorage"): ("AE2", "Refined Storage", "两个存储系统不可同时启用"),
    ("ae2", "rs"): ("AE2", "Refined Storage", "两个存储系统不可同时启用"),
}

# 存储 Mod 互斥组（同一组只能选一个）
STORAGE_MODS_GROUP = {
    "ae2", "refined-storage", "refinedstorage", "rs",
    "storage drawers", "storagedrawers",
    "industrial foregoing",
    "simple storage network",
}

# 信息展示 Mod 互斥组（同一组最多选一个）
INFO_DISPLAY_GROUP = {
    "jade", "wthit", "hwyla", "theoneprobe",
}

# 物品查看 Mod 互斥组
ITEM_VIEW_GROUP = {
    "roughly enough items", "rei",
    "emi", "emi (ex mode independent)",
    "jade's browse", "jades browse",
    "just enough items", "jei",
}

# 优化 Mod 互斥组
OPTIMIZATION_GROUP = {
    "optifine", "sodium", "iris", "embeddium", "rubidium", "magnesium",
}

# 加载器不兼容警告
LOADER_INCOMPATIBLE_PAIRS = [
    ("forge", "fabric"), ("forge", "quilt"), ("fabric", "rift")
]


@dataclass
class CompatibilityReport:
    """整合包兼容性报告"""
    loader_issues: list  # 加载器不一致问题
    hard_conflicts: list  # 硬性冲突
    version_incompat: list  # 版本不兼容
    functional_overlap: list  # 功能重叠
    dependency_missing: list  # 缺失依赖
    all_good: list  # 完全兼容的 Mod 对
    recommendations: list  # 解决建议


def normalize_slug(name: str) -> str:
    """标准化 Mod 名称为 slug 格式"""
    return name.lower().replace(" ", "-").replace("_", "-").replace("'", "")


def check_mod_compatibility(mods: list[ModResult], target_version: str = None) -> CompatibilityReport:
    """
    对给定 Mod 列表进行全面兼容性检查。
    返回 CompatibilityReport，包含所有问题和推荐。
    """
    report = CompatibilityReport(
        loader_issues=[],
        hard_conflicts=[],
        version_incompat=[],
        functional_overlap=[],
        dependency_missing=[],
        all_good=[],
        recommendations=[],
    )

    if not mods:
        return report

    # Step 1: 加载器一致性检查
    all_loaders = set()
    for mod in mods:
        for loader in (mod.loaders or []):
            all_loaders.add(loader.lower())

    for loader_a, loader_b in LOADER_INCOMPATIBLE_PAIRS:
        if loader_a in all_loaders and loader_b in all_loaders:
            report.loader_issues.append({
                "type": "loader_conflict",
                "loaders": [loader_a, loader_b],
                "reason": f"{loader_a.title()} 和 {loader_b.title()} Mod 不可混用，必须选择单一加载器",
                "severity": "error",
            })

    # Step 2: 硬性冲突检查
    mod_slugs = {normalize_slug(m.name): m for m in mods}
    mod_names_lower = {normalize_slug(m.name): m.name for m in mods}

    checked_pairs = set()
    for mod in mods:
        slug_norm = normalize_slug(mod.name)
        for (conf_a, conf_b), info in HARD_CONFLICTS.items():
            if info is None:
                continue  # 允许同时安装
            norm_a, norm_b = normalize_slug(conf_a), normalize_slug(conf_b)
            pair = tuple(sorted([norm_a, norm_b]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            a_in = norm_a in mod_slugs or conf_a.lower() in mod_names_lower
            b_in = norm_b in mod_slugs or conf_b.lower() in mod_names_lower

            if a_in and b_in:
                name_a = mod_names_lower.get(norm_a, conf_a)
                name_b = mod_names_lower.get(norm_b, conf_b)
                report.hard_conflicts.append({
                    "type": "hard_conflict",
                    "mods": [name_a, name_b],
                    "reason": info[2],
                    "severity": "error",
                    "solution": f"在 {name_a} 和 {name_b} 中选择一个",
                })

    # Step 3: 功能重叠检查（存储 / 信息展示 / 物品查看 / 优化 Mod）
    groups = [
        ("storage", STORAGE_MODS_GROUP),
        ("info_display", INFO_DISPLAY_GROUP),
        ("item_view", ITEM_VIEW_GROUP),
        ("optimization", OPTIMIZATION_GROUP),
    ]

    for group_name, group_set in groups:
        found = []
        for mod in mods:
            slug = normalize_slug(mod.name)
            for keyword in group_set:
                if keyword in slug or slug in keyword:
                    found.append(mod.name)
                    break
        if len(found) > 1:
            if group_name == "optimization":
                # 进一步检查是否真的有冲突（sodium+iris 是允许的）
                sodium_found = any("sodium" in normalize_slug(n) for n in found)
                iris_found = any("iris" in normalize_slug(n) for n in found)
                if sodium_found and iris_found:
                    continue  # Sodium + Iris 是兼容的，跳过
                elif len(found) > 1:
                    report.functional_overlap.append({
                        "type": "functional_overlap",
                        "group": group_name,
                        "mods": found,
                        "reason": "多个功能相同的 Mod 同时存在",
                        "severity": "warning",
                        "solution": f"{group_name} 类只保留 1 个，建议保留: {found[0]}",
                    })
            else:
                report.functional_overlap.append({
                    "type": "functional_overlap",
                    "group": group_name,
                    "mods": found,
                    "reason": "多个功能相同的 Mod 同时存在",
                    "severity": "warning",
                    "solution": f"{group_name} 类只保留 1 个，建议保留: {found[0]}",
                })

    # Step 4: 版本兼容性检查
    if target_version:
        for mod in mods:
            if mod.game_versions and target_version not in mod.game_versions:
                report.version_incompat.append({
                    "type": "version_incompatible",
                    "mod": mod.name,
                    "target_version": target_version,
                    "supported_versions": mod.game_versions[:5],
                    "severity": "error" if len(mod.game_versions) > 0 else "warning",
                    "suggestion": f"该 Mod 不支持 {target_version}，最高支持 {mod.game_versions[0] if mod.game_versions else '未知'}",
                })

    # Step 5: 依赖完整性检查
    selected_slugs = {normalize_slug(m.name) for m in mods}
    for mod in mods:
        for dep in mod.dependencies:
            if dep.required:
                dep_slug = normalize_slug(dep.slug or dep.name)
                if dep_slug not in selected_slugs:
                    report.dependency_missing.append({
                        "type": "missing_dependency",
                        "parent_mod": mod.name,
                        "dependency": dep.name or dep.slug,
                        "required": dep.required,
                        "suggestion": f"安装 {mod.name} 前需先安装 {dep.name or dep.slug}",
                    })

    # Step 6: 生成推荐建议
    if report.loader_issues:
        loaders_used = [l for iss in report.loader_issues for l in iss.get("loaders", [])]
        report.recommendations.append({
            "type": "loader_decision",
            "suggestion": f"检测到加载器冲突：{loaders_used}。请选择单一加载器（推荐 Forge 生态用于科技包，Fabric 生态用于轻量包）",
        })

    if not report.hard_conflicts and not report.loader_issues and not report.version_incompat:
        report.recommendations.append({
            "type": "all_clear",
            "suggestion": "整合包 Mod 之间未发现硬性冲突，可正常安装使用",
        })

    return report


def format_compatibility_report(
    report: CompatibilityReport,
    mods: list[ModResult],
    target_version: str = None,
    loader: str = None,
) -> str:
    """生成人类可读的兼容性报告"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  整合包兼容性检查报告")
    lines.append(f"  版本: {target_version or '不限'}  |  加载器: {loader or '未指定'}")
    lines.append(f"{'='*60}\n")

    # 错误级问题（最优先告知）
    if report.loader_issues or report.hard_conflicts:
        lines.append("  ❌ 严重冲突（必须解决）")
        lines.append("  " + "-"*40)
        for issue in report.loader_issues:
            lines.append(f"  ⚠️  加载器冲突: {' + '.join(issue['loaders'])}")
            lines.append(f"     {issue['reason']}")
            lines.append("")
        for conflict in report.hard_conflicts:
            lines.append(f"  ❌ {conflict['mods'][0]} + {conflict['mods'][1]}")
            lines.append(f"     {conflict['reason']}")
            lines.append(f"     → {conflict['solution']}")
            lines.append("")
        lines.append("")

    # 版本不兼容
    if report.version_incompat:
        lines.append("  🚫 版本不兼容（需换 Mod 或换版本）")
        lines.append("  " + "-"*40)
        for item in report.version_incompat:
            lines.append(f"  · {item['mod']} 不支持 {item['target_version']}")
            lines.append(f"    支持版本: {', '.join(item['supported_versions'][:3])}")
            lines.append(f"    → {item['suggestion']}")
            lines.append("")
        lines.append("")

    # 功能重叠
    if report.functional_overlap:
        lines.append("  ⚠️  功能重叠（建议精简）")
        lines.append("  " + "-"*40)
        for item in report.functional_overlap:
            lines.append(f"  · {item['group']}: {' + '.join(item['mods'])}")
            lines.append(f"    {item['reason']}")
            lines.append(f"    → {item['solution']}")
            lines.append("")
        lines.append("")

    # 缺失依赖
    if report.dependency_missing:
        lines.append("  ⬆️  缺失前置依赖（需补充安装）")
        lines.append("  " + "-"*40)
        for item in report.dependency_missing:
            lines.append(f"  · {item['parent_mod']} 需要 → {item['dependency']}")
        lines.append("")

    # 推荐建议
    if report.recommendations:
        lines.append("  💡 推荐建议")
        lines.append("  " + "-"*40)
        for rec in report.recommendations:
            if rec["type"] == "all_clear":
                lines.append(f"  ✅ {rec['suggestion']}")
            else:
                lines.append(f"  · {rec['suggestion']}")
        lines.append("")

    # 整合包安装顺序建议
    if not report.hard_conflicts and not report.loader_issues:
        lines.append("  📦 推荐安装顺序")
        lines.append("  " + "-"*40)
        deps = {normalize_slug(d.name): d for m in mods for d in m.dependencies}
        lib_mods = []
        opt_mods = []
        feature_mods = []
        ui_mods = []
        lib_keywords = ["api", "lib", "core", "library"]
        opt_keywords = ["sodium", "lithium", "phosphor", "ferrite", "optifine", "iris"]
        ui_keywords = ["jade", "rei", "emi", "jei", "wthit", "hwyla", "item", "tooltip"]

        for mod in sorted(mods, key=lambda m: -m.score):
            slug = normalize_slug(mod.name)
            if any(k in slug for k in lib_keywords):
                lib_mods.append(mod.name)
            elif any(k in slug for k in opt_keywords):
                opt_mods.append(mod.name)
            elif any(k in slug for k in ui_keywords):
                ui_mods.append(mod.name)
            else:
                feature_mods.append(mod.name)

        order = []
        if lib_mods:
            order.append(f"[1] 基础层（前置/库）: {', '.join(lib_mods[:3])}")
        if opt_mods:
            order.append(f"[2] 优化层: {', '.join(opt_mods[:3])}")
        if feature_mods:
            order.append(f"[3] 功能层: {', '.join(feature_mods[:5])}")
        if ui_mods:
            order.append(f"[4] UI/辅助层: {', '.join(ui_mods[:2])}")

        for step in order:
            lines.append(f"  {step}")
        lines.append("")

    lines.append(f"{'='*60}")
    return "\n".join(lines)


# ============================================================
# 输出格式化
# ============================================================
def format_results_json(mods: list[ModResult], query: str, version: str = None) -> str:
    """以 JSON 格式输出结果"""
    output = {
        "query": query,
        "version": version,
        "total": len(mods),
        "results": [asdict(mod) for mod in mods],
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def format_results_text(mods: list[ModResult], query: str, version: str = None) -> str:
    """以人类可读文本格式输出结果"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  Minecraft Mod 搜索结果")
    lines.append(f"  关键词: {query}  |  版本: {version or '不限'}")
    lines.append(f"{'='*60}\n")

    for i, mod in enumerate(mods, 1):
        is_top3 = i <= 3
        badge = " [🔥 TOP推荐]" if is_top3 else ""

        lines.append(f"  {'▶' if is_top3 else '·'} {i}. {mod.name}{badge}")
        lines.append(f"    作者: {mod.author or '未知'}")
        lines.append(f"    下载: {mod.downloads:,}  |  版本: {mod.latest_version or mod.game_versions[0] if mod.game_versions else '未知'}")

        cats = ", ".join(mod.categories[:3]) if mod.categories else "未分类"
        lines.append(f"    分类: {cats}")

        if mod.description:
            desc = mod.description[:120].replace("\n", " ")
            lines.append(f"    简介: {desc}{'...' if len(mod.description) > 120 else ''}")

        links = []
        if mod.modrinth_url:
            links.append(f"Modrinth: {mod.modrinth_url}")
        if mod.curseforge_url:
            links.append(f"CurseForge: {mod.curseforge_url}")
        if links:
            lines.append(f"    链接: {' | '.join(links)}")

        if mod.warnings:
            for w in mod.warnings:
                lines.append(f"    ⚠️  {w}")

        lines.append("")

    lines.append(f"{'='*60}")
    lines.append(f"  共找到 {len(mods)} 个相关 Mod\n")
    return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Minecraft Java Mod 多平台搜索 / 整合包分析")
    parser.add_argument("--query", "-q", required=True, help="搜索关键词（单 Mod 搜索）或用 --modpack 模式")
    parser.add_argument("--version", "-v", default=None, help="Minecraft 版本，如 1.20.4")
    parser.add_argument("--loader", "-l", default=None, help="加载器类型: forge/fabric/quilt")
    parser.add_argument("--category", "-c", default=None, help="Mod 分类")
    parser.add_argument("--platform", "-p", default="all", choices=["modrinth", "curseforge", "all"], help="搜索平台")
    parser.add_argument("--limit", type=int, default=15, help="返回结果数量")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="请求超时秒数")
    parser.add_argument("--api-key", default=None, help="CurseForge API Key")
    parser.add_argument("--output", "-o", default="text", choices=["text", "json"], help="输出格式")
    # 整合包分析专用参数
    parser.add_argument("--modpack", action="store_true", help="启用整合包分析模式")
    parser.add_argument("--directions", "-d", nargs="+", default=None,
                        help="整合包各方向关键词，如: 能源 自动化 物流 (与 --modpack 配合)")

    args = parser.parse_args()

    # 获取 CF API Key
    cf_api_key = args.api_key or os.environ.get("CF_API_KEY", "")

    # 整合包分析模式
    if args.modpack and args.directions:
        print(f"\n🎮 整合包分析模式", file=sys.stderr)
        print(f"版本: {args.version or '不限'}  |  加载器: {args.loader or '未指定'}", file=sys.stderr)
        print(f"功能方向: {' / '.join(args.directions)}\n", file=sys.stderr)

        all_mods = []
        directions_results = {}

        for direction in args.directions:
            print(f"  → 分析方向: {direction}", file=sys.stderr)
            t0 = time.time()
            mr = search_modrinth(
                query=direction,
                version=args.version,
                loader=args.loader,
                limit=5,
                timeout=args.timeout,
            )
            cf = []
            if cf_api_key:
                cf = search_curseforge(
                    query=direction,
                    version=args.version,
                    loader=args.loader,
                    api_key=cf_api_key,
                    limit=3,
                    timeout=5,
                )
            merged_dir = merge_and_rank(mr, cf, target_version=args.version, top_n=3)
            merged_dir = add_dependency_mods(merged_dir, timeout=args.timeout)
            directions_results[direction] = merged_dir
            all_mods.extend(merged_dir)
            print(f"    返回 {len(merged_dir)} 个 Mod (耗时 {time.time()-t0:.1f}s)", file=sys.stderr)

        # 去重
        seen = {}
        for mod in all_mods:
            key = normalize_slug(mod.name)
            if key not in seen or mod.downloads > seen[key].downloads:
                seen[key] = mod
        all_mods = list(seen.values())

        # 兼容性检查
        print(f"\n  → 执行兼容性检查...", file=sys.stderr)
        compat_report = check_mod_compatibility(all_mods, target_version=args.version)

        # 输出整合包分析结果
        print(format_modpack_report(directions_results, compat_report, args.version, args.loader))
        return

    # 单 Mod 搜索模式（默认）
    # ── TACZ 枪械优先路径 ──────────────────────────────────────
    if detect_gun_intent(args.query):
        print(f"  → 检测到枪械意图，启用 TACZ 枪包优先搜索...", file=sys.stderr)
        tacz_found, tacz_mods = search_tacz_gunpacks(
            query=args.query,
            version=args.version,
            limit=args.limit,
            timeout=args.timeout,
        )

        if tacz_found and tacz_mods:
            # 计算依赖并输出
            tacz_mods = add_dependency_mods(tacz_mods, timeout=args.timeout)

            if args.output == "json":
                output_data = {
                    "mode": "tacz_gunpack",
                    "query": args.query,
                    "version": args.version,
                    "tacz_base": {
                        "name": TACZ_MOD_NAME,
                        "modrinth_url": TACZ_MODRINTH_URL,
                        "supported_versions": sorted(TACZ_SUPPORTED_VERSIONS),
                    },
                    "total": len(tacz_mods),
                    "results": [asdict(m) for m in tacz_mods],
                    "errors": [],
                }
                print(json.dumps(output_data, ensure_ascii=False, indent=2))
            else:
                print(format_tacz_header(args.version, args.loader))
                print(format_results_text(tacz_mods, args.query, args.version))
                print("\n  💡 提示：上述枪包需要先安装 TACZ 基础 Mod，枪包放入 .minecraft/tacz/ 目录")
            return
        else:
            print(f"  → TACZ 枪包搜索无结果，回退到普通 Mod 搜索...", file=sys.stderr)

    # ── Create 机械动力优先路径 ───────────────────────────────────
    if detect_create_intent(args.query):
        print(f"  → 检测到机械/自动化意图，启用 Create 优先搜索...", file=sys.stderr)
        create_found, create_mods = search_create_addons(
            query=args.query,
            version=args.version,
            loader=args.loader,
            limit=args.limit,
            timeout=args.timeout,
        )

        if create_found and create_mods:
            create_mods = add_dependency_mods(create_mods, timeout=args.timeout)

            if args.output == "json":
                output_data = {
                    "mode": "create_addon",
                    "query": args.query,
                    "version": args.version,
                    "create_base": {
                        "name": CREATE_MOD_NAME,
                        "modrinth_url": CREATE_MODRINTH_URL,
                        "supported_versions": sorted(CREATE_SUPPORTED_VERSIONS),
                    },
                    "total": len(create_mods),
                    "results": [asdict(m) for m in create_mods],
                    "errors": [],
                }
                print(json.dumps(output_data, ensure_ascii=False, indent=2))
            else:
                print(format_create_header(args.version, args.loader))
                print(format_results_text(create_mods, args.query, args.version))
                print("\n  💡 提示：上述附属 Mod 需要先安装 Create (机械动力) 基础 Mod")
            return
        else:
            print(f"  → Create 附属搜索无结果，回退到普通 Mod 搜索...", file=sys.stderr)

    # ── 普通 Mod 搜索（默认路径 / TACZ & Create fallback）─────────
    print(f"正在搜索 Modrinth... (超时 {args.timeout}s)", file=sys.stderr)
    t0 = time.time()
    modrinth_results = search_modrinth(
        query=args.query,
        version=args.version,
        loader=args.loader,
        category=args.category,
        limit=args.limit,
        timeout=args.timeout,
    )
    print(f"  → Modrinth 返回 {len(modrinth_results)} 条结果 (耗时 {time.time()-t0:.1f}s)", file=sys.stderr)

    curseforge_results = []
    if args.platform in ("curseforge", "all") and cf_api_key:
        print(f"正在搜索 CurseForge... (超时 5s)", file=sys.stderr)
        t0 = time.time()
        curseforge_results = search_curseforge(
            query=args.query,
            version=args.version,
            loader=args.loader,
            api_key=cf_api_key,
            limit=args.limit,
            timeout=5,
        )
        print(f"  → CurseForge 返回 {len(curseforge_results)} 条结果 (耗时 {time.time()-t0:.1f}s)", file=sys.stderr)

    # 合并去重并排序
    merged = merge_and_rank(modrinth_results, curseforge_results, target_version=args.version, top_n=args.limit)

    # 补充依赖 Mod
    merged = add_dependency_mods(merged, timeout=args.timeout)

    # 输出
    if args.output == "json":
        print(format_results_json(merged, args.query, args.version))
    else:
        print(format_results_text(merged, args.query, args.version))


def format_modpack_report(
    directions: dict,
    compat_report: CompatibilityReport,
    version: str = None,
    loader: str = None,
) -> str:
    """格式化整合包分析报告"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  整合包规划与推荐报告")
    lines.append(f"  版本: {version or '不限'}  |  加载器: {loader or '根据功能方向选择'}")
    lines.append(f"{'='*60}\n")

    # 方向推荐
    lines.append(f"  {'─'*56}")
    lines.append(f"  各功能方向推荐 Mod")
    lines.append(f"  {'─'*56}\n")

    for i, (direction, mods) in enumerate(directions.items(), 1):
        lines.append(f"  【{i}. {direction}】")
        for j, mod in enumerate(mods[:3], 1):
            badge = "🔥 核心" if j == 1 else f"  备选{j}"
            lines.append(f"    {j}. {mod.name} [{badge}]")
            lines.append(f"       📥 {mod.downloads:,} | 🎮 {mod.latest_version or '未知'}")
            cats = ", ".join(mod.categories[:3]) if mod.categories else ""
            if cats:
                lines.append(f"       🏷️  {cats}")
            if mod.description:
                desc = mod.description[:100].replace("\n", " ")
                lines.append(f"       {desc}...")
            if mod.warnings:
                for w in mod.warnings:
                    lines.append(f"       ⚠️  {w}")
            lines.append(f"       🔗 {mod.modrinth_url or mod.curseforge_url}")
            lines.append("")
        lines.append("")

    # 兼容性总览
    lines.append(f"  {'─'*56}")
    lines.append(f"  兼容性总览")
    lines.append(f"  {'─'*56}\n")

    if compat_report.hard_conflicts:
        lines.append(f"  ❌ 发现 {len(compat_report.hard_conflicts)} 项严重冲突：")
        for c in compat_report.hard_conflicts:
            lines.append(f"    · {c['mods'][0]} + {c['mods'][1]}: {c['reason']}")
            lines.append(f"      → {c['solution']}")
        lines.append("")
    else:
        lines.append(f"  ✅ 核心 Mod 之间无硬性冲突\n")

    if compat_report.version_incompat:
        lines.append(f"  🚫 {len(compat_report.version_incompat)} 个 Mod 版本不兼容：")
        for v in compat_report.version_incompat[:5]:
            lines.append(f"    · {v['mod']}: {v['suggestion']}")
        lines.append("")

    if compat_report.functional_overlap:
        lines.append(f"  ⚠️  功能重叠（建议精简）：")
        for o in compat_report.functional_overlap:
            lines.append(f"    · {o['group']}: {' + '.join(o['mods'])}")
            lines.append(f"      → {o['solution']}")
        lines.append("")

    if compat_report.dependency_missing:
        lines.append(f"  ⬆️  缺失前置依赖（自动补充）：")
        for d in compat_report.dependency_missing:
            lines.append(f"    · {d['parent_mod']} → {d['dependency']}")
        lines.append("")

    # 安装顺序
    all_mods = []
    for mods in directions.values():
        all_mods.extend(mods)
    seen = {}
    for mod in all_mods:
        key = normalize_slug(mod.name)
        if key not in seen or mod.downloads > seen[key].downloads:
            seen[key] = mod
    all_mods = list(seen.values())

    if not compat_report.hard_conflicts and not compat_report.loader_issues:
        lines.append(f"  {'─'*56}")
        lines.append(f"  推荐安装顺序")
        lines.append(f"  {'─'*56}\n")
        lib_mods, opt_mods, feature_mods, ui_mods = [], [], [], []
        lib_kw, opt_kw, ui_kw = ["api", "lib", "core"], \
            ["sodium", "lithium", "phosphor", "ferrite", "optifine", "iris"], \
            ["jade", "rei", "emi", "jei", "wthit", "hwyla", "tooltip"]

        for mod in sorted(all_mods, key=lambda m: -m.score):
            slug = normalize_slug(mod.name)
            if any(k in slug for k in lib_kw):
                lib_mods.append(mod.name)
            elif any(k in slug for k in opt_kw):
                opt_mods.append(mod.name)
            elif any(k in slug for k in ui_kw):
                ui_mods.append(mod.name)
            else:
                feature_mods.append(mod.name)

        steps = []
        if lib_mods:
            steps.append(f"[1] 基础层（前置库）: {', '.join(lib_mods[:3])}")
        if opt_mods:
            steps.append(f"[2] 优化层: {', '.join(opt_mods[:3])}")
        if feature_mods:
            steps.append(f"[3] 功能层: {', '.join(feature_mods[:5])}")
        if ui_mods:
            steps.append(f"[4] UI/辅助层: {', '.join(ui_mods[:2])}")

        for step in steps:
            lines.append(f"  {step}")
        lines.append("")

    lines.append(f"{'='*60}\n")
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    main()
