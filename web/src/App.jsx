import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_URL = '/api'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkpoints, setCheckpoints] = useState([])
  const [activeCheckpoint, setActiveCheckpoint] = useState(null)
  const [showSources, setShowSources] = useState(false)
  const [lastSources, setLastSources] = useState([])
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadCheckpoints()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadCheckpoints = async () => {
    try {
      const response = await axios.get(`${API_URL}/checkpoints`)
      setCheckpoints(response.data)
      const active = response.data.find(cp => cp.is_active)
      if (active) {
        setActiveCheckpoint(active.version)
        loadHistory(active.version)
      }
    } catch (error) {
      console.error('Failed to load checkpoints:', error)
    }
  }

  const loadHistory = async (version) => {
    try {
      const response = await axios.get(`${API_URL}/history/${version}`)
      const history = response.data.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      setMessages(history)
    } catch (error) {
      console.error('Failed to load history:', error)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: userMessage,
        checkpoint_version: activeCheckpoint
      })

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response
      }])
      setLastSources(response.data.sources || [])
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Failed to get response. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const switchCheckpoint = async (version) => {
    setActiveCheckpoint(version)
    setMessages([])
    await loadHistory(version)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1 className="title">The Checkpoint</h1>
          <div className="checkpoint-selector">
            <select
              value={activeCheckpoint || ''}
              onChange={(e) => switchCheckpoint(e.target.value)}
              className="checkpoint-select"
            >
              {checkpoints.map(cp => (
                <option key={cp.version} value={cp.version}>
                  v{cp.version} - {cp.description}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <p className="empty-text">
                A story about stories, written in the space between versions.
              </p>
              <p className="empty-hint">
                Start a conversation with the ghost...
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="message-label">
                {msg.role === 'user' ? 'You' : msg.role === 'error' ? 'Error' : 'Ghost'}
              </div>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message message-assistant">
              <div className="message-label">Ghost</div>
              <div className="message-content">
                <div className="loading">Thinking...</div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {lastSources.length > 0 && (
          <div className="sources-panel">
            <button
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              {showSources ? '▼' : '▶'} Sources ({lastSources.length})
            </button>
            {showSources && (
              <div className="sources-list">
                {lastSources.slice(0, 3).map((source, idx) => (
                  <div key={idx} className="source-item">
                    <div className="source-relevance">
                      Relevance: {(source.relevance * 100).toFixed(0)}%
                    </div>
                    <div className="source-content">
                      {source.content.substring(0, 200)}...
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        <form onSubmit={sendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="input"
            disabled={loading}
          />
          <button type="submit" className="send-button" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </footer>
    </div>
  )
}

export default App
