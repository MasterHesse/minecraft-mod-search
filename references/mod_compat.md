# Minecraft Java Mod 兼容性矩阵

## 1. 加载器兼容性（最核心规则）

### Forge / Fabric / Quilt 不可互通

| Mod 加载器 | Forge Mod | Fabric Mod | Quilt Mod |
|-----------|-----------|-----------|-----------|
| Forge | ✅ 兼容 | ❌ 不兼容 | ❌ 不兼容 |
| Fabric | ❌ 不兼容 | ✅ 兼容 | ✅ 兼容 |
| Quilt | ❌ 不兼容 | ✅ 兼容 | ✅ 兼容 |

> ⚠️ **核心原则**：整合包必须选择单一加载器。Forge 和 Fabric 的 Mod 生态完全不互通，混装会导致游戏崩溃。

### Forge vs Fabric 生态选择建议

| 需求 | 推荐加载器 | 理由 |
|------|----------|------|
| 科技类大型 Mod（Create/Mekanism/IE） | **Forge** | Forge 科技 Mod 生态最成熟 |
| 轻量优化 Mod（Sodium/Lithium） | **Fabric** | Fabric 优化 Mod 性能更优 |
| 纯 1.20.4+ 最新版本 | **Fabric/Quilt** | 部分新 Mod 仅 Fabric |
| 1.12.2 / 1.7.10 老版本 | **Forge** | 历史版本无 Fabric 支持 |
| 混合需求（科技+优化） | **Forge** | 推荐 OptiFine（非 Sodium） |

---

## 2. 优化 Mod 互斥关系

### 帧率优化 Mod 兼容性表

| Mod | Sodium | Lithium | Phosphor | OptiFine | Iris | Embeddium | Rubidium |
|-----|--------|---------|---------|----------|------|-----------|----------|
| **Sodium** | — | ✅ 兼容 | ✅ 兼容 | ❌ **互斥** | ✅ 兼容 | ❌ 互斥 | ❌ 互斥 |
| **Lithium** | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Phosphor** | ✅ 兼容 | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **OptiFine** | ❌ **互斥** | ✅ 兼容 | ✅ 兼容 | — | ❌ **互斥** | ❌ 互斥 | ❌ 互斥 |
| **Iris** | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ❌ **互斥** | — | ❌ 互斥 | ❌ 互斥 |
| **Embeddium** | ❌ **互斥** | ✅ 兼容 | ✅ 兼容 | ❌ **互斥** | ❌ **互斥** | — | ❌ 互斥 |
| **FerriteCore** | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |

> 💡 **规则**：OptiFine 与 Sodium/Iris 功能重叠，只能选择其一。Fabric 生态推荐 Sodium + Iris；Forge 生态推荐 OptiFine。

### 渲染/光照 Mod 兼容性

| Mod | Sodium | OptiFine | Iris | Continuity | Oculus | Rubidium |
|-----|--------|----------|------|------------|--------|----------|
| **Sodium** | — | ❌ 互斥 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ❌ 互斥 |
| **OptiFine** | ❌ 互斥 | — | ❌ 互斥 | ❌ 需 OptiFine | ❌ 需 OptiFine | ❌ 互斥 |
| **Iris** | ✅ 兼容 | ❌ 互斥 | — | ✅ 兼容 | ❌ 互斥 | ❌ 互斥 |

---

## 3. 存储 Mod 互斥关系

| Mod | AE2 | RS | Storage Drawers | Refined Storage | Industrial Foregoing | Simple Storage Network |
|-----|-----|----|----------------|-----------------|--------------------|----------------------|
| **AE2** | — | ❌ **互斥** | ✅ 兼容 | ❌ **互斥** | ✅ 兼容 | ✅ 兼容 |
| **Refined Storage** | ❌ **互斥** | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Storage Drawers** | ✅ 兼容 | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Industrial Foregoing** | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | — | ✅ 兼容 |

> ❌ **硬性互斥**：AE2 和 Refined Storage（RS）不可同时启用，只能选择其一。

---

## 4. 信息展示 Mod 互斥关系

| Mod | Jade | WTHIT | Hwyla | AppleSkin | Xaero's Minimap |
|-----|------|-------|-------|-----------|-----------------|
| **Jade** | — | ⚠️ **二选一** | ⚠️ **二选一** | ✅ 兼容 | ✅ 兼容 |
| **WTHIT** | ⚠️ **二选一** | — | ⚠️ **二选一** | ✅ 兼容 | ✅ 兼容 |
| **Hwyla** | ⚠️ **二选一** | ⚠️ **二选一** | — | ✅ 兼容 | ✅ 兼容 |

> 💡 Jade 为 WTHIT/Hwyla 的现代替代品，功能完全重叠，保留 Jade 即可。

---

## 5. 物品查看 Mod 互斥关系

| Mod | REI | EMI | Jade's Browse | Just Enough Items | Roughly Enough Items |
|-----|-----|-----|---------------|------------------|--------------------|
| **REI** | — | ❌ **互斥** | ❌ 需前置 | ❌ 互斥 | ❌ 互斥 |
| **EMI** | ❌ **互斥** | — | ❌ 需前置 | ❌ 互斥 | ❌ 互斥 |

> ❌ **REI / EMI / JEI 互斥**，三选一。EMI 为 REI 的现代 Fabric 替代品。

---

## 6. 科技 Mod 兼容性

### Forge 科技 Mod 联动兼容性

| Mod | Create | Mekanism | Immersive Eng. | Industrial Foregoing | Tech Reborn | Thermal Series |
|-----|--------|----------|---------------|--------------------|-----------|---------------|
| **Create** | — | ✅ 兼容* | ✅ 兼容* | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Mekanism** | ✅ 兼容* | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Immersive Eng.** | ✅ 兼容* | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Industrial Foregoing** | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 |
| **Tech Reborn** | ✅ 兼容 | ⚠️ 能源单位差异 | ⚠️ 能源单位差异 | ✅ 兼容 | — | ⚠️ 能源单位差异 |
| **Thermal Series** | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ⚠️ 能源单位差异 | — |

> * 表示存在专用联动 Mod（如 Create 的 Create: Contraption Utils 可联动 Mekanism 管道）

### 能源单位差异说明

| Mod | 默认能源单位 | 与其他 Mod 联动方式 |
|-----|-----------|------------------|
| Mekanism | RF / 通用 | 通过 KubeJS / Create 管道转换 |
| Immersive Engineering | IF (IguanaTweaks) | 需插件转换 |
| Tech Reborn | EU / RF | 部分支持 RF |
| Thermal Series | RF | 行业标准，兼容性最广 |

### Create 联动 Mod 矩阵

| 联动 Mod | 兼容性 | 说明 |
|---------|--------|------|
| Create + Mekanism | ✅ 兼容 | 通过 KubeJS 或 Create 管道连接 |
| Create + Refined Storage | ✅ 兼容 | 需 Refined Storage Addon |
| Create + AE2 | ✅ 兼容 | 需 AE2 Additions |
| Create + Immersive Engineering | ✅ 兼容 | 需 IE Create 补丁 |
| Create + Create Astral | ⚠️ 需注意 | 两者都修改世界生成 |

---

## 7. 魔法 Mod 兼容性

| Mod | Thaumcraft | Botania | Blood Magic | Electroblob's Magic | Mahou Tsukai |
|-----|-----------|---------|------------|---------------------|-------------|
| **Thaumcraft** | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 | ⚠️ 可能有 Aspect 冲突 |
| **Botania** | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| **Blood Magic** | ✅ 兼容 | ✅ 兼容 | — | ✅ 兼容 | ✅ 兼容 |

> 魔法 Mod 之间通常兼容，但注意 Aspect 系统（Thaumcraft）和标签系统可能的命名冲突。

---

## 8. 常用前置依赖 Mod

这些 Mod 通常为其他 Mod 提供底层支持，应优先安装：

| 依赖 Mod | 用途 | 需要它的主要 Mod |
|---------|------|----------------|
| **Fabric API** | Fabric 底层支持 | 几乎所有 Fabric Mod |
| **Architectury API** | Fabric/Forge 跨兼容层 | Cloth Config, REI 等 |
| **Cloth Config API** | 配置界面 | 大量 Mod 的 GUI 依赖 |
| **GeckoLib** | 动画支持 | 大量 Mod |
| **KubeJS** | 脚本/定制 | Create Addon, 科技包联动 |
| **EMI** | EMI 依赖（Fabric） | EMI 本身 |

---

## 9. 已知冲突 Mod 组合

以下组合同时安装会导致崩溃、功能异常或性能下降，**应避免**：

### 硬性冲突（崩溃）

| 组合 | 原因 | 解决方案 |
|------|------|---------|
| Forge Mod + Fabric Mod | 加载器不兼容 | 选择同一加载器 |
| OptiFine + Sodium/Iris | 渲染引擎冲突 | 只选其一 |
| AE2 + Refined Storage | 存储系统冲突 | 只选其一 |
| 不兼容游戏版本的 Mod | 版本不匹配 | 换版本或换 Mod |

### 功能重叠（性能浪费）

| 组合 | 原因 | 建议 |
|------|------|------|
| OptiFine + Sodium | 都优化渲染 | Forge 选 OptiFine，Fabric 选 Sodium |
| Jade + WTHIT/Hwyla | 功能完全重叠 | 只留 Jade |
| REI + EMI + JEI | 物品查看功能重叠 | 只留一个 |
| Xaero's Minimap + JourneyMap | 地图功能重叠 | 只留一个 |

### 潜在兼容性问题（需测试）

| 组合 | 风险等级 | 说明 |
|------|---------|------|
| Create + 大型科技包 | 🟡 中 | 物品处理逻辑可能冲突，测试后再用 |
| Lithium + 某些 AI 相关 Mod | 🟡 中 | 极少数 Mod 的 AI 改动与 Lithium 冲突 |
| 多版本同一功能 Mod | 🟡 中 | 如多个生物群系生成 Mod 可能互相覆盖 |

---

## 10. 版本特定兼容性速查

### 1.20.4 版本

| Mod | 1.20.4 兼容性 | 备注 |
|-----|-------------|------|
| Sodium | ✅ | 0.5.8+ 支持 |
| Create | ✅ | 0.1.x 支持 |
| Mekanism | ✅ | 10.3.x 支持 |
| Immersive Engineering | ✅ | 9.x 支持 |
| AE2 | ✅ | 2.12.x 支持 |
| Refined Storage | ✅ | 1.11.x 支持 |
| OptiFine | ✅ | HD_U_I6 支持 |
| Fabric API | ✅ | 0.100.x 支持 |

### 1.19.4 版本

| Mod | 1.19.4 兼容性 | 备注 |
|-----|-------------|------|
| Sodium | ✅ | 0.4.x 支持 |
| Create | ✅ | 0.5.x 支持 |
| Mekanism | ✅ | 10.2.x 支持 |
| Immersive Engineering | ✅ | 8.x 支持 |
| AE2 | ✅ | 2.10.x 支持 |
| Refined Storage | ✅ | 1.11.x 支持 |
| OptiFine | ✅ | HD_U_I5 支持 |
| Fabric API | ✅ | 0.87.x 支持 |

### 1.18.2 版本

| Mod | 1.18.2 兼容性 | 备注 |
|-----|-------------|------|
| Sodium | ✅ | 0.4.x 支持 |
| Create | ✅ | 0.4.x 支持 |
| Mekanism | ✅ | 10.1.x 支持 |
| AE2 | ✅ | 2.6.x 支持 |
| OptiFine | ✅ | HD_U_H8 支持 |

---

## 11. 整合包兼容性检查流程

在推荐整合包 Mod 时，按以下顺序检查兼容性：

### Step 1: 加载器统一性
```
检查所有 Mod 是否使用同一加载器（Forge 或 Fabric）
→ 如发现混合，立刻报告并要求用户选择加载器
```

### Step 2: 硬性互斥检查
```
遍历所有已知互斥组合（optifine↔sodium, ae2↔rs, rei↔emi）
→ 发现任何互斥，给出"二选一"建议
```

### Step 3: 依赖完整性
```
对每个推荐 Mod 提取 dependencies
→ 补全所有 required 依赖
→ 递归检查依赖的依赖
```

### Step 4: 版本兼容性
```
检查 target_version 是否在每个 mod.game_versions 中
→ 不兼容的标记 [🚫 版本不兼容] 并提供替代
```

### Step 5: 功能重叠检查
```
检测多个功能完全相同的 Mod（如多个生物群系 Mod）
→ 提示用户选择其一
```
