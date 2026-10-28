import React, { useState, useEffect } from 'react';
import type { HealthStatus, Settings } from '../types';
import { fetchSettings, updateSettings, fetchHealth } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import { 
  Settings as SettingsIcon, Activity, Server, Database, 
  Cpu, CheckCircle2, AlertCircle, Save, RefreshCw, Terminal 
} from 'lucide-react';

interface SettingsScreenProps {
  health: HealthStatus | null;
  onRefreshHealth: () => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ 
  health, 
  onRefreshHealth 
}) => {
  const addToast = useAppStore((s) => s.addToast);
  const [settings, setSettings] = useState<Settings>({
    ollama_url: 'http://localhost:11434',
    ollama_model: 'llama3.2',
    use_ollama: true,
    embedding_mode: 'local_vectorizer',
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [testing, setTesting] = useState<boolean>(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await fetchSettings();
      setSettings(data);
    } catch (e: any) {
      addToast({ type: 'error', title: 'Settings Error', message: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await updateSettings(settings);
      addToast({ type: 'success', title: 'Settings Saved', message: 'Preferences updated successfully.' });
      onRefreshHealth();
    } catch (e: any) {
      addToast({ type: 'error', title: 'Save Failed', message: e.message });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTesting(true);
      onRefreshHealth();
      const updatedHealth = await fetchHealth();
      if (updatedHealth.ollama_available) {
        addToast({
          type: 'success',
          title: 'Ollama Connected',
          message: `Ollama is active! Active model: ${updatedHealth.active_model_name}`,
        });
      } else {
        addToast({
          type: 'warning',
          title: 'Ollama Offline',
          message: 'Ollama daemon not reached. KORTEX is running in 100% offline Extractive Mode.',
        });
      }
    } catch (e: any) {
      addToast({ type: 'error', title: 'Health Check Failed', message: e.message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-y-auto p-6 max-w-5xl mx-auto w-full space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-accent-cyan" />
          <span>System Settings & Architecture Health</span>
        </h2>
        <p className="text-xs text-text-secondary mt-0.5">
          Verify local AI capabilities, engine fallbacks, and storage integrity.
        </p>
      </div>

      {/* Live System Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Backend API Card */}
        <div className="p-4 bg-surface border border-border rounded-card shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-secondary flex items-center gap-1.5">
              <Server className="w-4 h-4 text-accent-primary" />
              FastAPI Core
            </span>
            <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-success">
              <CheckCircle2 className="w-3.5 h-3.5" /> Online
            </span>
          </div>
          <p className="text-xs text-text-muted">
            Port 8000 • Background Jobs Enabled
          </p>
        </div>

        {/* Ollama Card */}
        <div className="p-4 bg-surface border border-border rounded-card shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-secondary flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-accent-cyan" />
              Ollama Daemon
            </span>
            {health?.ollama_available ? (
              <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-success">
                <CheckCircle2 className="w-3.5 h-3.5" /> Active
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-warning" title="KORTEX gracefully uses extractive NLP">
                <Terminal className="w-3.5 h-3.5" /> Extractive Mode
              </span>
            )}
          </div>
          <p className="text-xs text-text-muted truncate" title={health?.active_model_name}>
            {health?.active_model_name || 'Extractive Engine'}
          </p>
        </div>

        {/* SQLite Database Card */}
        <div className="p-4 bg-surface border border-border rounded-card shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-secondary flex items-center gap-1.5">
              <Database className="w-4 h-4 text-accent-violet" />
              SQLite Store
            </span>
            <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-success">
              <CheckCircle2 className="w-3.5 h-3.5" /> Connected
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono">
            {health?.total_papers || 0} papers • {health?.total_chunks || 0} chunks
          </p>
        </div>
      </div>

      {/* Settings Form */}
      <div className="p-6 bg-surface border border-border rounded-card shadow-card space-y-5">
        <h3 className="text-sm font-semibold text-text-primary pb-3 border-b border-border">
          AI Engine & Model Configuration
        </h3>

        <form onSubmit={handleSave} className="space-y-4">
          {/* Ollama URL */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-text-primary">
              Ollama Base URL
            </label>
            <input
              type="text"
              value={settings.ollama_url}
              onChange={(e) => setSettings({ ...settings, ollama_url: e.target.value })}
              className="w-full px-3 py-2 text-xs font-mono bg-base border border-border rounded-control text-text-primary focus:outline-none focus:border-accent-cyan"
            />
            <p className="text-[11px] text-text-muted">
              Default local Ollama address (http://localhost:11434).
            </p>
          </div>

          {/* Model Name */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-text-primary">
              Target Ollama Model Name
            </label>
            <input
              type="text"
              value={settings.ollama_model}
              onChange={(e) => setSettings({ ...settings, ollama_model: e.target.value })}
              className="w-full px-3 py-2 text-xs font-mono bg-base border border-border rounded-control text-text-primary focus:outline-none focus:border-accent-cyan"
            />
            <p className="text-[11px] text-text-muted">
              e.g., llama3.2, mistral, deepseek-r1:8b, phi3
            </p>
          </div>

          {/* Enable Ollama Toggle */}
          <div className="flex items-center justify-between p-3 rounded-control bg-raised border border-border">
            <div>
              <h4 className="text-xs font-semibold text-text-primary">
                Enable Ollama LLM Enhancement
              </h4>
              <p className="text-[11px] text-text-muted">
                If disabled or if Ollama is offline, the app transparently runs section-heuristics and TF-IDF extraction with zero errors.
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.use_ollama}
                onChange={(e) => setSettings({ ...settings, use_ollama: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-base peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent-primary" />
            </label>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing}
              className="flex items-center gap-1.5 px-3 py-2 rounded-control text-xs font-medium bg-raised hover:bg-surface text-text-primary border border-border transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
              <span>Test Connection</span>
            </button>

            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded-control text-xs font-semibold bg-accent-primary hover:bg-accent-primary/80 text-white transition-colors shadow-sm disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Settings</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
