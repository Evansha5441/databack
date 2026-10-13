import React, { useState, useEffect, useRef } from 'react'
import {
  FileSpreadsheet,
  Upload,
  Send,
  Sparkles,
  Database,
  AlertTriangle,
  Code2,
  TrendingUp,
  BrainCircuit,
  CheckCircle2,
  Table as TableIcon
} from 'lucide-react'
import ChartViewer from './components/ChartViewer'

export default function App() {
  const [tables, setTables] = useState({})
  const [tableNames, setTableNames] = useState([])
  const [messages, setMessages] = useState([])
  const [inputQuery, setInputQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const [selectedQualityTable, setSelectedQualityTable] = useState('')
  const [qualityData, setQualityData] = useState(null)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  const sampleQuestions = [
    'Which region generated the highest revenue?',
    'Show monthly sales trends.',
    'Which products are underperforming?',
    'What are the top five customers?',
    'Generate SQL for this analysis.',
    'Detect anomalies in the dataset.'
  ]

  useEffect(() => {
    fetchTables()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchTables = async () => {
    try {
      const res = await fetch('/api/tables')
      const data = await res.json()
      setTables(data.tables || {})
      setTableNames(data.table_names || [])
      if (data.table_names && data.table_names.length > 0 && !selectedQualityTable) {
        setSelectedQualityTable(data.table_names[0])
      }
    } catch (err) {
      console.error('Failed to fetch tables:', err)
    }
  }

  const [uploadNotification, setUploadNotification] = useState(null)
  const [selectedTableModal, setSelectedTableModal] = useState(null)

  const handleFileUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    const formData = new FormData()
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i])
    }

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })
      const result = await res.json()
      await fetchTables()
      setUploadNotification(`Successfully uploaded ${result.uploaded} dataset(s) into database!`)
      setTimeout(() => setUploadNotification(null), 5000)
    } catch (err) {
      console.error('Upload failed:', err)
      setUploadNotification(`Upload failed: ${err.message}`)
      setTimeout(() => setUploadNotification(null), 5000)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleSend = async (queryText = null) => {
    const query = queryText || inputQuery
    if (!query.trim() || loading) return

    const userMsg = { role: 'user', content: query }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setInputQuery('')
    setLoading(true)

    const formattedHistory = messages.slice(-4).map(m => ({
      role: m.role,
      content: m.role === 'user' ? m.content : (m.data?.explanation || m.data?.thought || '')
    }))

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          history: formattedHistory
        })
      })
      const data = await res.json()
      setMessages([...updatedMessages, { role: 'assistant', data: data }])
    } catch (err) {
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          data: {
            thought: 'Connection error while communicating with backend server.',
            explanation: 'Failed to complete analytical evaluation. Ensure backend is running.',
            result: { success: false, error: err.message }
          }
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const fetchQualityMetrics = async (tableName) => {
    setSelectedQualityTable(tableName)
    try {
      const res = await fetch(`/api/quality/${tableName}`)
      const data = await res.json()
      setQualityData(data)
    } catch (err) {
      console.error('Quality check failed:', err)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header>
        <div className="logo-container">
          <div className="logo-badge">DBO AI</div>
          <div>
            <div className="title">Digital Back Office Ltd. - AI Data Analyst</div>
            <div className="subtitle">Production Data Analysis, SQL, ML Anomalies & BI Visualizer</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            style={{
              backgroundColor: activeTab === 'chat' ? '#3b82f6' : '#334155',
              color: 'white',
              border: 'none',
              borderRadius: 6,
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer'
            }}
            onClick={() => setActiveTab('chat')}
          >
            Chat & Analytics
          </button>
          <button
            style={{
              backgroundColor: activeTab === 'quality' ? '#3b82f6' : '#334155',
              color: 'white',
              border: 'none',
              borderRadius: 6,
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer'
            }}
            onClick={() => {
              setActiveTab('quality')
              if (tableNames.length > 0) fetchQualityMetrics(tableNames[0])
            }}
          >
            Data Quality
          </button>
        </div>
      </header>

      {uploadNotification && (
        <div style={{
          backgroundColor: '#10b981',
          color: 'white',
          padding: '10px 20px',
          fontWeight: 600,
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>{uploadNotification}</span>
          <button onClick={() => setUploadNotification(null)} style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 700 }}>×</button>
        </div>
      )}

      <div className="app-layout">
        <aside className="sidebar">
          <div className="sidebar-section">
            <div className="section-title">Upload Datasets (CSV)</div>
            <div
              className="upload-box"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={22} style={{ margin: '0 auto 8px', color: '#60a5fa' }} />
              <div style={{ fontSize: 13, fontWeight: 600 }}>
                {uploading ? 'Processing files...' : 'Click to Upload CSVs'}
              </div>
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                Supports multi-file joins & auto-schema registration
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
              />
            </div>
          </div>

          <div className="sidebar-section">
            <div className="section-title">Active Database Tables ({tableNames.length})</div>
            {tableNames.map((name) => {
              const meta = tables[name] || {}
              return (
                <div
                  key={name}
                  className="table-card"
                  style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                  onClick={() => {
                    setActiveTab('quality')
                    fetchQualityMetrics(name)
                  }}
                  title="Click to view schema and data quality"
                >
                  <div className="table-name">
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <TableIcon size={14} /> {name}
                    </span>
                    <span className="badge">{meta.row_count || 0} rows</span>
                  </div>
                  <div className="table-stats">
                    {meta.columns ? `${meta.columns.length} columns (click to profile)` : 'In-memory'}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                    {(meta.columns || []).slice(0, 4).map((c) => (
                      <span key={c.name} style={{ fontSize: 10, background: '#0f172a', padding: '2px 5px', borderRadius: 3, color: '#94a3b8' }}>
                        {c.name}
                      </span>
                    ))}
                    {(meta.columns || []).length > 4 && (
                      <span style={{ fontSize: 10, color: '#64748b' }}>
                        +{meta.columns.length - 4} more
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </aside>

        <main className="main-content">
          {activeTab === 'chat' ? (
            <>
              <div className="chat-history">
                {messages.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">
                      <Sparkles size={28} />
                    </div>
                    <h2 style={{ fontSize: 20, fontWeight: 700 }}>Interactive AI Data Analyst</h2>
                    <p style={{ color: '#94a3b8', fontSize: 14 }}>
                      Ask questions in natural language, request DuckDB SQL / Pandas calculations, view charts, and run machine learning anomaly checks.
                    </p>
                    <div className="suggestion-chips">
                      {sampleQuestions.map((q, idx) => (
                        <div key={idx} className="chip" onClick={() => handleSend(q)}>
                          {q}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map((msg, index) => (
                    <div key={index} className={`message-card ${msg.role}`}>
                      {msg.role === 'user' ? (
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{msg.content}</div>
                      ) : (
                        <div>
                          {msg.data?.thought && (
                            <div className="reasoning-box" style={{ marginBottom: 12 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, color: '#818cf8', marginBottom: 4 }}>
                                <BrainCircuit size={14} /> Agent Reasoning & CoT Plan
                              </div>
                              {msg.data.thought}
                            </div>
                          )}

                          {msg.data?.code && (
                            <div style={{ marginBottom: 12 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
                                <Code2 size={13} /> Generated {msg.data.action_type?.toUpperCase() || 'Query'}
                              </div>
                              <pre className="code-box">{msg.data.code}</pre>
                            </div>
                          )}

                          {msg.data?.explanation ? (
                            <div style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 12 }}>
                              {msg.data.explanation}
                            </div>
                          ) : (
                            !msg.data?.code && !msg.data?.thought && !msg.data?.result?.data && (
                              <div style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 12 }}>
                                {typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data)}
                              </div>
                            )
                          )}

                          {msg.data?.chart_spec?.recommended && msg.data?.result?.data && (
                            <ChartViewer
                              spec={msg.data.chart_spec}
                              data={msg.data.result.data}
                            />
                          )}

                          {msg.data?.result?.data && Array.isArray(msg.data.result.data) && msg.data.result.data.length > 0 && (
                            <div className="data-table-container">
                              <table className="styled-table">
                                <thead>
                                  <tr>
                                    {Object.keys(msg.data.result.data[0]).map((col) => (
                                      <th key={col}>{col}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {msg.data.result.data.slice(0, 10).map((row, rIdx) => (
                                    <tr key={rIdx}>
                                      {Object.values(row).map((val, cIdx) => (
                                        <td key={cIdx}>
                                          {typeof val === 'object' && val !== null ? JSON.stringify(val) : String(val ?? '')}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              {msg.data.result.data.length > 10 && (
                                <div style={{ padding: '6px 12px', fontSize: 11, color: '#64748b', background: '#090d16' }}>
                                  Showing 10 of {msg.data.result.total_rows || msg.data.result.data.length} records
                                </div>
                              )}
                            </div>
                          )}

                          {msg.data?.result?.error && (
                            <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              <AlertTriangle size={15} /> Execution Warning: {msg.data.result.error}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
                {loading && (
                  <div className="message-card assistant" style={{ color: '#94a3b8', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Sparkles size={16} className="animate-spin" /> Analyzing dataset schemas and computing solution...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="chat-input-bar">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask any question, request charts, SQL, or anomaly detection..."
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                />
                <button
                  className="btn-primary"
                  onClick={() => handleSend()}
                  disabled={loading || !inputQuery.trim()}
                >
                  <Send size={16} /> Send
                </button>
              </div>
            </>
          ) : (
            <div style={{ padding: 24, overflowY: 'auto', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700 }}>Data Quality & Profile Report</h2>
                  <p style={{ color: '#94a3b8', fontSize: 13 }}>Audit null distributions, cardinality, and statistical ranges</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {tableNames.map((tbl) => (
                    <button
                      key={tbl}
                      className={`btn-secondary ${selectedQualityTable === tbl ? 'badge' : ''}`}
                      onClick={() => fetchQualityMetrics(tbl)}
                    >
                      {tbl}
                    </button>
                  ))}
                </div>
              </div>

              {qualityData && (
                <div>
                  <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
                    <div className="table-card" style={{ flex: 1 }}>
                      <div className="table-stats">Total Rows</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#38bdf8' }}>{qualityData.total_rows}</div>
                    </div>
                    <div className="table-card" style={{ flex: 1 }}>
                      <div className="table-stats">Columns</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#38bdf8' }}>{qualityData.total_columns}</div>
                    </div>
                    <div className="table-card" style={{ flex: 1 }}>
                      <div className="table-stats">Duplicate Rows</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: qualityData.duplicate_rows > 0 ? '#f59e0b' : '#10b981' }}>
                        {qualityData.duplicate_rows}
                      </div>
                    </div>
                  </div>

                  <div className="data-table-container">
                    <table className="styled-table">
                      <thead>
                        <tr>
                          <th>Column</th>
                          <th>Data Type</th>
                          <th>Missing Values</th>
                          <th>Missing %</th>
                          <th>Unique Count</th>
                          <th>Mean / Range</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(qualityData.quality_metrics || []).map((m) => (
                          <tr key={m.column}>
                            <td style={{ fontWeight: 600 }}>{m.column}</td>
                            <td><span className="badge">{m.type}</span></td>
                            <td>{m.null_count}</td>
                            <td>{m.null_percentage}%</td>
                            <td>{m.unique_count}</td>
                            <td>{m.mean !== null && m.mean !== undefined ? `Mean: ${m.mean} (Min: ${m.min}, Max: ${m.max})` : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
