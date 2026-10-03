# Unraid + Sub-Store + Flux 使用说明

## 本次配置的边界
- 主用 host 实例：Unraid 192.168.5.13；测试独立 IP 实例：192.168.5.33。
- 显式 HTTP/SOCKS 代理，Rule 模式，TUN 关闭。顶部私网规则直接使用 DIRECT。
- 保留原有 [Line]/[Landing] 筛选和业务组名称，避免未知节点名称造成迁移失败。
- “节点选择”新建时优先美国；已有面板选择可能继续保留，部署后手动确认。
- 地区组仍兼容线路直接出口与落地出口；国家标签不是最终出口保证。根据真实节点逐一验出口后，再拆分固定出口组。
- 公开模板不含节点密码、订阅密钥或管理密钥。通过私有 Sub-Store 处理步骤注入 external-controller 的 secret。

## 模板来源
让现有 Sub-Store 文件生成流程读取：
https://raw.githubusercontent.com/raymondhudson1987/clash/main/config/substore_template.yaml

不同 Sub-Store 版本的文件处理方式可能不同；保留你当前已工作的节点注入步骤。
仅把 YAML 放在 GitHub 不会自动注入 proxies，也不会自动更新 Unraid。
若当前保存的是粘贴的模板，需替换为新模板或调整生成步骤读取以上 URL。

## 规则归属与更新
- list/：原始上游 blackmatrix7/ios_rule_script 的规则。自动任务只更新本模板引用的上游文件。
- custom/direct.yaml：个人强制直连，优先于其他远程规则。
- custom/ManualAdjust.yaml：个人强制代理，优先于通用分类。保留原来的域名。
- custom/ 下其余文件：从本 fork 的现有规则迁移，不被同步覆盖。
- 不执行整个 fork 的自动合并；不自动覆盖 config/、substore/ 或 custom/。
- 其他历史模板及其 list/ 文件保留，但不属于本次自动更新范围。
- 原始上游： https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Clash
- 原 fork： https://github.com/holddyxu/clash
- 本模板的 Google 专项规则排在 YouTube/AI 专项规则之后；国内域名和国内 IP 分开匹配。
- ChinaMax 的混合规则保留为兼容 provider，但不重复参与匹配，避免其中 IP 提前覆盖业务域名。
- ChinaMaxIP 改用完整 classical 文件在末尾兜底（包含域名、IP、ASN）。原 _IP.yaml 含裸 ASN 132203，不是合法纯 IP 规则集；新来源保留规则类型，IP 匹配可触发解析。
- 国内域名、国内 IP、国内媒体、下载、PT、SteamCN 使用 DIRECT；个人代理例外优先。

自动任务每天北京时间 06:23（日本时间 07:23）同步，也可在 Actions 手动运行。
同步前检查所有源文件非空、YAML payload 格式正确；任一失败则不提交。
不会删除旧 list/ 文件，不会覆盖 custom/。上游删除或改名会让任务失败，等待检查，不会静默发布空规则。
工作流具有写入 contents 的权限声明，但仓库/组织限制仍可能禁止推送。
Fork 的定时任务可能默认禁用；必须在 Actions 确认工作流启用并至少成功运行一次。
本工作流做静态校验，不等同于真实节点、网络和 mihomo 内核验收。

## 规则下载
所有 provider 使用“规则更新”组下载；首次加载前确保其中有可用的美国或日本节点。
若该组筛选为空，修正节点名或改选可用成员，不能假定下载成功。
个人直连规则每小时刷新，其他规则通常每天刷新；可在面板主动更新规则集。
GitHub Raw 存在缓存，提交后不一定立即读到新内容。
规则内容更新不需要下载整份主配置或重启容器。

## Flux 与四种协议
继续使用现有 Flux 转发，节点的 server/port 对应入口监听地址和端口。
认证、TLS SNI、REALITY、WS/gRPC 参数对应落地服务，不要盲目一起替换。
常规 HY2 需要 UDP；VMess/VLESS/Trojan 常见 TCP、WS、gRPC 传输需要 TCP，按实际节点核对。
Flux 端口转发和隧道转发是不同模式；隧道模式还需检查隧道传输。
已通过 Flux 中转的节点不额外添加 dialer-proxy。
以后若改 mihomo 链式代理，dialer-proxy 放在出站节点或 provider override，不能直接放在策略组。
https://wiki.metacubex.one/config/proxies/dialer-proxy/

建议命名同时描述入口与出口，如 [Landing]🇺🇸 US入口-US原生-VLESS。
四种协议共享同一线路，不算四条独立容灾线路。
美国稳定路径日常主用；日本低延迟路径作为备选；Surfshark 三地区分别验证真实出口。
没有实际节点与服务端映射前，不自动创建虚构出口组。

## 一次性部署和验证
1. 备份 host 实例当前配置；确认面板和客户端都连 .13 的正确端口。
2. Sub-Store 获取新模板并重新生成完整配置，确认 proxies 非空、地区组有成员、私有 secret 被保留。
3. 在实际运行的 mihomo 容器内，用同版本内核对候选文件执行 -t 校验。目录和 -f 路径必须对应你的挂载。
4. 校验成功后替换文件，通过 PUT /configs?force=true 加载正式文件；请求使用容器内路径及 Bearer secret。
5. 确认运行模式 Rule、TUN 关闭、“规则更新”组可用、所有规则集加载成功。
6. 关闭对应旧连接，再访问 .13 的真实服务端口；预期命中 192.168.5.13/32，最终 DIRECT。
7. 分别验证一个国内网站、AI、YouTube 和各落地真实出口；失败时恢复备份并重新加载。
8. 验证后在客户端代理绕过列表加入 .13，保证 Unraid 管理不依赖 mihomo。
9. .33 使用独立配置目录和缓存；已 DIRECT 但访问 .13 失败时，再排查 Docker 自定义网络互通。

正式更新脚本应先下载临时文件，检查 HTTP 错误、超时和空内容，同版本 -t 校验，内容不变跳过，
备份并替换后 API 重载，验收失败回滚。禁止未校验直接覆盖；无需每次 docker restart。
当前仓库未掌握你的容器名、挂载路径和私有密钥，不提供假定可直接运行的部署脚本。

API 文档：https://wiki.metacubex.one/api/
