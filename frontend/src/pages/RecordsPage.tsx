import { React } from '../platform/react-host';
import { query, requestSchema, sessionSchema, timelineSchema, useResource, type Filters, type ModelRequest, type Selection, type Session } from '../services/preview';
import { Empty, Modal, money, number, Pagination, ResourceState, time } from '../components/common';

const requestsSchema = requestSchema.array();
const sessionsSchema = sessionSchema.array();

function Timeline({ id, session, filters, selection }: { id: string; session: Session; filters: Filters; selection: Selection }) {
  const resource = useResource(`/sessions/${encodeURIComponent(id)}/timeline?${query(selection)}`, timelineSchema);
  if (resource.loading || resource.error) return <ResourceState {...resource} />;
  if (!resource.data) return <Empty text="会话正文 unavailable" />;
  return <div className="hum-timeline"><p>{resource.data.session.profile} · {resource.data.session.platform} · {time(resource.data.session.time)}</p>
    <dl className="hum-detail-grid"><dt>用户 / 部门</dt><dd>{filters.users.find((item) => item.id === session.user_id)?.name ?? '未归属'} / {filters.departments.find((item) => item.id === session.department_id)?.name ?? '未归属'}</dd><dt>已知 Tokens</dt><dd>{session.input === null || session.output === null || session.cached === null ? '—（细分缺失）' : number(session.input + session.output + session.cached)}</dd><dt>MCP 调用</dt><dd>{session.mcp_calls} 次</dd></dl>
    {resource.data.messages.map((message) => message.kind === 'tools' ? <details className="hum-tool-group" key={message.id}><summary>工具调用 {message.tools.length} 次 · 成功 {message.tools.filter((tool) => tool.success).length} / 失败 {message.tools.filter((tool) => !tool.success).length}</summary>{message.tools.map((tool) => <details key={tool.id}><summary>{tool.success ? '✓' : '×'} {tool.name}</summary><h3>参数</h3><pre>{tool.args}</pre><h3>结果</h3><p>{tool.result}</p></details>)}</details> : <article className={`hum-message hum-message-${message.kind}`} key={message.id}><b>{message.kind === 'user' ? '用户' : 'Hermes 助手'}</b><p>{message.text}</p></article>)}
  </div>;
}

export function RecordsPage({ kind, selection, filters, initialSearch = '' }: { kind: 'requests' | 'sessions'; selection: Selection; filters: Filters; initialSearch?: string }) {
  const [page, setPage] = React.useState(1);
  const [size, setSize] = React.useState(20);
  const [sort, setSort] = React.useState('time');
  const [order, setOrder] = React.useState('desc');
  const term = initialSearch;
  const [detail, setDetail] = React.useState<ModelRequest | Session | null>(null);
  const schema = kind === 'requests' ? requestsSchema : sessionsSchema;
  const resource = useResource<(ModelRequest | Session)[]>(`/${kind}?${query(selection, { page, page_size: size, sort, order, search: term })}`, schema);
  React.useEffect(() => { setPage(1); }, [selection, term, size, kind]);
  const names = (id: string, type: 'department' | 'user') => (type === 'department' ? filters.departments : filters.users).find((item) => item.id === id)?.name ?? '未归属';
  const changeSort = (field: string) => { setSort(field); setOrder(sort === field && order === 'desc' ? 'asc' : 'desc'); setPage(1); };
  return <div className="hum-stack">
    <ResourceState {...resource} />
    {!resource.loading && !resource.error && resource.data && (resource.data.length === 0 ? <Empty /> : <><div className="hum-table-scroll hum-record-table"><table><thead><tr>
      <th><button className="hum-text" onClick={() => changeSort('time')}>{kind === 'requests' ? '请求时间' : '会话 ID'} {sort === 'time' ? (order === 'desc' ? '↓' : '↑') : '↕'}</button></th><th>部门</th><th>用户</th><th>{kind === 'requests' ? '模型' : '对话开始时间'}</th>
      <th><button className="hum-text" onClick={() => changeSort('input')}>输入 ↕</button></th><th><button className="hum-text" onClick={() => changeSort('output')}>输出 ↕</button></th><th>缓存读取</th><th>{kind === 'requests' ? '耗时' : 'MCP 使用'}</th>
    </tr></thead><tbody>{resource.data.map((row) => <tr key={row.id}>
      <td><button className="hum-text hum-row-link" onClick={() => setDetail(row)}>{'status' in row && <span className={row.status === 'failed' ? 'hum-failed' : 'hum-success'} aria-label={row.status === 'failed' ? '请求失败' : '请求成功'}>{row.status === 'failed' ? '⊗' : '⊙'}</span>}{kind === 'requests' ? time(row.time) : row.id}</button></td>
      <td>{names(row.department_id, 'department')}</td><td>{names(row.user_id, 'user')}</td><td>{'model' in row ? <span className="hum-model" title={`${row.provider} / ${row.model}`}><b>{row.provider.slice(0, 1)}</b>{row.model}</span> : time(row.time)}</td><td>{number(row.input)}</td><td>{number(row.output)}</td><td>{number(row.cached)}</td><td>{'duration_ms' in row ? `${number(row.duration_ms)} ms` : `${row.mcp_calls} 次`}</td>
    </tr>)}</tbody></table></div><Pagination page={page} total={resource.total} size={size} onPage={setPage} onSize={setSize} /></>)}
    {detail && <Modal title={kind === 'requests' ? '请求详情' : `会话详情 · ${detail.id}`} onClose={() => setDetail(null)}>{'model' in detail ? <dl className="hum-detail-grid">{Object.entries({ '请求 ID': detail.id, '会话': detail.session_id, 'Profile': detail.profile, '提供商': detail.provider, '模型': detail.model, '状态': detail.status, '请求时间': time(detail.time), '输入未命中': number(detail.input), '缓存读取': number(detail.cached), '输出': number(detail.output), '费用（估算）': money(detail.cost) }).map(([label, value]) => <React.Fragment key={label}><dt>{label}</dt><dd>{value}</dd></React.Fragment>)}</dl> : <Timeline id={detail.id} session={detail} filters={filters} selection={selection} />}</Modal>}
  </div>;
}
